import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session, url_for, Response, jsonify
import re, time, hashlib
from functools import wraps

app = Flask(__name__)

# --- TON CODE ANTI-BUG TÉLÉPHONE PRO CONSERVÉ 100% ---
def clean_env(name, default):
    raw = os.environ.get(name, default)
    return raw.replace("\n","").replace("\r","").replace(" ","").replace("\t","").strip()

ADMIN_PASSWORD = clean_env("ADMIN_PASSWORD", "Djinwoo258")
SECRET_KEY = clean_env("SECRET_KEY", "babi-artisan-ci-2026-pro")
app.secret_key = SECRET_KEY
WAVE = "0596003270"
DB = "babiartisan_v11.db"
GOOGLE_CODE = "R8QG7u_Wj5KU4chom1VGfq-nu8qG0WG_zLcOMewlEnw"

# --- SÉCURITÉ V13 RENFORCÉE ---
login_attempts = {}
def is_blocked(ip):
    now = time.time()
    attempts = login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < 300]
    login_attempts[ip] = attempts
    return len(attempts) >= 10
def add_attempt(ip):
    login_attempts.setdefault(ip, []).append(time.time())

def clean_input(text, max_len=100):
    if not text: return ""
    text = str(text).strip()[:max_len]
    text = re.sub(r'[<>\"\'`;]', '', text)
    return text

@app.after_request
def secure_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

def get_db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = get_db()
    c.execute("""CREATE TABLE IF NOT EXISTS artisans(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT, metier TEXT, ville TEXT, tel TEXT, description TEXT,
    dette INTEGER DEFAULT 0, status TEXT DEFAULT 'DISPO', rating REAL DEFAULT 4.9,
    date TEXT, last_pay TEXT, vues INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS contacts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artisan_id INTEGER, artisan_nom TEXT, date TEXT)""")
    try:
        c.execute("SELECT precision FROM artisans LIMIT 1")
    except:
        try: c.execute("ALTER TABLE artisans ADD COLUMN precision TEXT DEFAULT ''")
        except: pass
    c.execute("""CREATE TABLE IF NOT EXISTS notifications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT, date TEXT, lu INTEGER DEFAULT 0)""")
    # ============ V16 WALLET YANGO ============
    c.execute("""CREATE TABLE IF NOT EXISTS wallets(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artisan_id INTEGER UNIQUE,
    solde INTEGER DEFAULT 0,
    is_blocked INTEGER DEFAULT 0,
    total_gagne INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS wallet_transactions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artisan_id INTEGER,
    type TEXT,
    montant INTEGER,
    marche_montant INTEGER,
    reference_wave TEXT UNIQUE,
    date TEXT,
    security_hash TEXT)""")
    # Table chat V16 pour preuve
    c.execute("""CREATE TABLE IF NOT EXISTS chat_messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artisan_id INTEGER,
    client_nom TEXT,
    message TEXT,
    montant_detecte INTEGER DEFAULT 0,
    date TEXT)""")
    c.commit(); c.close()
init_db()

# ============ MOTEUR V16 WALLET YANGO 5% ============
def calculer_commission_v16(montant_marche):
    if montant_marche < 50000:
        return 0
    return int(montant_marche * 0.05)

def get_or_create_wallet(artisan_id):
    c = get_db()
    w = c.execute("SELECT * FROM wallets WHERE artisan_id=?", (artisan_id,)).fetchone()
    if not w:
        c.execute("INSERT INTO wallets(artisan_id,solde,is_blocked,total_gagne) VALUES(?,?,0,0)", (artisan_id,0))
        c.commit()
        w = c.execute("SELECT * FROM wallets WHERE artisan_id=?", (artisan_id,)).fetchone()
    c.close()
    return w

def debiter_wallet_securise(artisan_id, montant_marche, source="chat"):
    wallet = get_or_create_wallet(artisan_id)
    commission = calculer_commission_v16(montant_marche)
    if commission == 0:
        return {"status": "gratuit", "commission": 0, "solde": wallet['solde']}
    c = get_db()
    solde_actuel = wallet['solde']
    if solde_actuel < commission:
        c.execute("UPDATE wallets SET is_blocked=1 WHERE artisan_id=?", (artisan_id,))
        c.commit(); c.close()
        return {"status": "bloque", "solde": solde_actuel, "commission_due": commission}
    nouveau_solde = solde_actuel - commission
    is_blocked = 1 if nouveau_solde <= 0 else 0
    ref = f"AUTO-{source}-{int(time.time())}-{artisan_id}"
    hash_data = f"{artisan_id}{commission}{ref}{SECRET_KEY}"
    sec_hash = hashlib.sha256(hash_data.encode()).hexdigest()
    c.execute("UPDATE wallets SET solde=?, is_blocked=?, total_gagne=total_gagne+? WHERE artisan_id=?", (nouveau_solde, is_blocked, montant_marche, artisan_id))
    c.execute("INSERT INTO wallet_transactions(artisan_id,type,montant,marche_montant,reference_wave,date,security_hash) VALUES(?,?,?,?,?,?,?)",
              (artisan_id, 'DEBIT_COMMISSION', commission, montant_marche, ref, datetime.now().strftime("%d/%m/%Y %H:%M"), sec_hash))
    c.execute("INSERT INTO notifications(message,date) VALUES(?,?)", (f"💰 V16 Wallet: -{commission}F sur artisan {artisan_id} pour marché {montant_marche}F | Solde: {nouveau_solde}F", datetime.now().strftime("%d/%m/%Y %H:%M")))
    c.commit(); c.close()
    return {"status": "debite", "commission": commission, "nouveau_solde": nouveau_solde, "bloque": is_blocked}

def check_abo():
    c=get_db()
    try:
        for a in c.execute("SELECT * FROM artisans").fetchall():
            try:
                d=datetime.strptime(a['last_pay'] or a['date'], "%d/%m/%Y")
                if datetime.now() - d > timedelta(days=30) and a['status']=='DISPO':
                    c.execute("UPDATE artisans SET dette=dette+1000,status='BLOQUE' WHERE id=?",(a['id'],))
            except: pass
        c.commit()
    except: pass
    c.close()

CSS = f"""
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google-site-verification" content="{GOOGLE_CODE}" />
<meta name="theme-color" content="#00d26a">
<link rel="manifest" href="/manifest.json">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@700;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',system-ui}}
body{{background:#f8faf8;color:#111}}
.hero-pro{{position:relative;width:100%;min-height:520px;background:linear-gradient(135deg,#0a0a0a 0%,#1a3a1a 100%);overflow:hidden;display:flex;align-items:center;padding:24px}}
.hero-pro img.bg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.35}}
.hero-pro .content{{position:relative;z-index:2;max-width:800px;margin:0 auto;width:100%;color:#fff}}
.badge-top{{display:inline-block;background:#00ff88;color:#000;padding:6px 14px;border-radius:99px;font-weight:900;font-size:12px;margin-bottom:14px}}
.hero-pro h1{{font-size:42px;font-weight:900;line-height:.95;letter-spacing:-2px;margin-bottom:12px}}
.hero-pro h1 span{{color:#00ff88}}
.btn-pro{{display:block;padding:18px;border-radius:16px;text-align:center;font-weight:900;text-decoration:none;transition:.15s;font-size:15px}}
.g{{background:linear-gradient(135deg,#00d26a,#00ff88);color:#000}}
.o{{background:#fff;color:#111}} .b{{background:#111;color:#fff}}
.wrap{{max-width:800px;margin:0 auto;padding:0 14px 100px}}
.card{{background:#fff;border-radius:24px;padding:20px;margin:16px 0;box-shadow:0 10px 40px rgba(0,0,0,.06);border:1px solid #f0f0f0}}
.pill{{padding:8px 14px;background:#f3f4f6;border-radius:99px;font-size:13px;text-decoration:none;color:#111;font-weight:700;display:inline-block;margin:4px}}
.badge{{padding:6px 12px;border-radius:99px;font-size:11px;font-weight:800}}
.ok{{background:#dcfce7;color:#166534}}.ko{{background:#fee2e2;color:#991b1b}}
</style>
<script>if ('serviceWorker' in navigator) {{window.addEventListener('load', function() {{navigator.serviceWorker.register('/sw.js');}});}}</script>
"""

def layout(content, is_admin=False, notif_count=0):
    check_abo()
    nav = "" if is_admin else f"""
    <div class='hero-pro'>
      <img class='bg' src='https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=1200'>
      <div class='content'>
        <div class='badge-top'>🇨🇮 V16 WALLET YANGO • N°1 CI • +200 ARTISANS</div>
        <h1>Tu es artisan ?<br>On t'envoie des <span>clients tous les jours.</span></h1>
        <p style='opacity:.9;margin-bottom:20px'>Maçon, Mécano, Peintre, Vigile, Nounou, Matériaux, Quincaillerie... Inscription 30s GRATUIT. Commission 5% seulement au dessus de 50k.</p>
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:12px'>
          <a class='btn-pro g' href='/devenir-artisan'>🚀 JE VEUX DES CLIENTS</a>
          <a class='btn-pro o' href='#liste'>🔍 TROUVER UN PRO</a>
        </div>
      </div>
    </div><div class='wrap'>"""
    end = "</div>" if not is_admin else ""
    return f"<html><head>{CSS}</head><body>{nav}{content}{end}</body></html>"

# --- ROUTES LEGALES PLAY STORE V16 ---
@app.route('/privacy')
def privacy():
    return layout("<div class='card'><h2>Politique de Confidentialité - BabiArtisan-CI</h2><p><b>Date:</b> 20 Octobre 2026</p><br><p><b>1. Données collectées:</b> Nom, métier, ville, numéro WhatsApp avec votre consentement.</p><p><b>2. Utilisation:</b> Mise en relation artisan-client uniquement.</p><p><b>3. Stockage:</b> Données stockées sécurisées sur Render, chiffrées.</p><p><b>4. Partage:</b> Nous ne vendons jamais vos données. Numéro visible uniquement pour clients.</p><p><b>5. Suppression:</b> Demandez suppression via WhatsApp Wave 0596003270.</p><p><b>6. Contact:</b> contact@babiartisan-ci.com</p></div>")

@app.route('/terms')
def terms():
    return layout("<div class='card'><h2>Conditions d'utilisation - BabiArtisan-CI</h2><p><b>1.</b> Inscription gratuite, commission 5% seulement sur marchés >= 50.000F.</p><p><b>2.</b> L'artisan doit avoir un solde wallet positif pour rester visible.</p><p><b>3.</b> Commission prélevée automatiquement du solde wallet.</p><p><b>4.</b> Si solde à 0F, compte bloqué jusqu'à recharge Wave.</p><p><b>5.</b> Plateforme de mise en relation, pas responsable qualité travaux.</p><p><b>6.</b> Contact: 0596003270</p></div>")

@app.route('/contact-legal')
def contact_legal():
    return layout("<div class='card'><h2>Contact Légal - BabiArtisan-CI</h2><p><b>Développeur:</b> BabiArtisan-CI</p><p><b>Email:</b> babiartisan.contact@gmail.com</p><p><b>Téléphone:</b> 0596003270 (Wave)</p><p><b>Adresse:</b> Abidjan, Côte d'Ivoire</p><p><b>Site:</b> https://babiartisan-ci.onrender.com</p></div>")

@app.route('/google-site-verification.html')
@app.route(f'/{GOOGLE_CODE}.html')
def google_file():
    return f"google-site-verification: google-site-verification={GOOGLE_CODE}"
@app.route('/robots.txt')
def robots():
    return Response("User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: https://babiartisan-ci.onrender.com/sitemap.xml", mimetype="text/plain")
@app.route('/sitemap.xml')
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://babiartisan-ci.onrender.com/</loc><priority>1.0</priority></url><url><loc>https://babiartisan-ci.onrender.com/privacy</loc></url><url><loc>https://babiartisan-ci.onrender.com/terms</loc></url></urlset>"""
    return Response(xml, mimetype="application/xml")
@app.route('/manifest.json')
def manifest():
    return jsonify({"name": "BabiArtisan-CI - Artisan Côte d'Ivoire","short_name": "BabiArtisan","description": "Trouve un artisan en CI - Wallet Yango","start_url": "/","display": "standalone","background_color": "#f8faf8","theme_color": "#00d26a","icons": [{"src": "/icon.png", "sizes": "512x512", "type": "image/png"}]})
@app.route('/sw.js')
def sw():
    return Response("self.addEventListener('install', e => self.skipWaiting());", mimetype="application/javascript")
@app.route('/icon.png')
def icon():
    return redirect("https://cdn-icons-png.flaticon.com/512/1995/1995515.png")

# --- ROUTES WALLET V16 ---
@app.route('/api/wallet/recharge', methods=['POST'])
def recharge_wallet():
    data = request.get_json() or request.form
    try:
        artisan_id = int(data.get('artisan_id'))
        montant = int(data.get('montant'))
        ref_wave = clean_input(data.get('reference_wave',''), 100)
    except:
        return jsonify({"error": "Données invalides"}), 400
    if montant < 1000:
        return jsonify({"error": "Minimum 1000F"}), 400
    c = get_db()
    if c.execute("SELECT id FROM wallet_transactions WHERE reference_wave=?", (ref_wave,)).fetchone():
        c.close()
        return jsonify({"error": "Référence Wave déjà utilisée - anti-fraude"}), 400
    w = c.execute("SELECT * FROM wallets WHERE artisan_id=?", (artisan_id,)).fetchone()
    if not w:
        c.execute("INSERT INTO wallets(artisan_id,solde,is_blocked,total_gagne) VALUES(?,?,0,0)", (artisan_id,0))
    hash_data = f"{artisan_id}{montant}{ref_wave}{SECRET_KEY}"
    sec_hash = hashlib.sha256(hash_data.encode()).hexdigest()
    c.execute("UPDATE wallets SET solde=solde+?, is_blocked=0 WHERE artisan_id=?", (montant, artisan_id))
    c.execute("INSERT INTO wallet_transactions(artisan_id,type,montant,marche_montant,reference_wave,date,security_hash) VALUES(?,?,?,?,?,?,?)",
              (artisan_id,'CREDIT_WAVE',montant,0,ref_wave,datetime.now().strftime("%d/%m/%Y %H:%M"),sec_hash))
    c.execute("INSERT INTO notifications(message,date) VALUES(?,?)", (f"✅ Recharge Wallet: +{montant}F artisan {artisan_id} Ref:{ref_wave}", datetime.now().strftime("%d/%m/%Y %H:%M")))
    c.commit()
    new_solde = c.execute("SELECT solde FROM wallets WHERE artisan_id=?", (artisan_id,)).fetchone()['solde']
    c.close()
    return jsonify({"success": True, "nouveau_solde": new_solde})

@app.route('/api/wallet/solde/<int:artisan_id>')
def get_solde(artisan_id):
    c = get_db()
    w = c.execute("SELECT * FROM wallets WHERE artisan_id=?", (artisan_id,)).fetchone()
    if not w:
        c.close()
        return jsonify({"solde": 0, "is_blocked": False, "total_gagne": 0})
    trans = c.execute("SELECT * FROM wallet_transactions WHERE artisan_id=? ORDER BY id DESC LIMIT 10", (artisan_id,)).fetchall()
    c.close()
    return jsonify({"solde": w['solde'], "is_blocked": bool(w['is_blocked']), "total_gagne": w['total_gagne'], "history": [dict(t) for t in trans]})

@app.route('/api/chat/send', methods=['POST'])
def chat_send():
    data = request.get_json()
    artisan_id = int(data.get('artisan_id',0))
    message = clean_input(data.get('message',''), 500)
    client_nom = clean_input(data.get('client_nom','Client'), 50)
    # Detection prix V16 - cherche 50000, 50k, 50 mille etc.
    montant_detecte = 0
    m = re.search(r'(\d+)\s*(k|000|mille)', message.lower())
    if m:
        try:
            num = re.sub(r'\D', '', m.group(0))
            if 'k' in message.lower() and len(num)<=3:
                montant_detecte = int(num)*1000
            else:
                montant_detecte = int(num)
        except: pass
    else:
        # cherche nombre direct > 1000
        m2 = re.search(r'\b(\d{5,})\b', message)
        if m2:
            try: montant_detecte = int(m2.group(1))
            except: pass
    c = get_db()
    c.execute("INSERT INTO chat_messages(artisan_id,client_nom,message,montant_detecte,date) VALUES(?,?,?,?,?)",
              (artisan_id, client_nom, message, montant_detecte, datetime.now().strftime("%d/%m/%Y %H:%M")))
    c.commit(); c.close()
    result = None
    if montant_detecte >= 50000:
        result = debiter_wallet_securise(artisan_id, montant_detecte, "chat_auto")
    return jsonify({"success": True, "montant_detecte": montant_detecte, "wallet": result})

@app.route('/')
def home():
    ville=request.args.get('ville','').strip()
    metier=request.args.get('metier','').strip()
    c=get_db()
    arts=c.execute("SELECT * FROM artisans ORDER BY vues DESC, id DESC").fetchall()
    if ville: arts=[a for a in arts if ville.lower() in a['ville'].lower()]
    if metier: arts=[a for a in arts if metier.lower() in a['metier'].lower()]
    # check wallet blocked
    blocked_ids = [w['artisan_id'] for w in c.execute("SELECT artisan_id FROM wallets WHERE is_blocked=1").fetchall()]
    c.close()
    filters=f"<div class='card' style='text-align:center'><h2>👋 {len(arts)} pros - V16 WALLET YANGO ACTIF</h2><p style='color:#666;font-size:13px'>Solde wallet obligatoire • 5% au dessus de 50k • Gratuit en dessous</p><form style='display:flex;gap:8px;margin-top:14px'><input name='ville' placeholder='📍 Ville' value='{ville}'><input name='metier' placeholder='🛠️ Métier' value='{metier}'><button class='btn-pro g' style='width:110px;padding:12px'>🔍</button></form></div>"
    cards="<div id='liste'></div>"
    for a in arts[:150]:
        is_wallet_blocked = a['id'] in blocked_ids
        bloque = (a['dette'] or 0)>0 or a['status']!='DISPO' or is_wallet_blocked
        badge = f"<span class='badge ko'>🔒 WALLET VIDE</span>" if is_wallet_blocked else (f"<span class='badge ko'>🔒 {a['dette']}F dû</span>" if (a['dette'] or 0)>0 else f"<span class='badge ok'>✅ DISPO • {a['rating']}⭐</span>")
        if bloque:
            act=f"<div style='background:#fef2f2;padding:12px;border-radius:12px;text-align:center'><b style='color:#991b1b'>BLOQUÉ - Recharge Wallet Wave {WAVE}</b><br><a href='/api/wallet/solde/{a['id']}' style='font-size:12px'>Voir solde</a></div>"
        else:
            act=f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px'><a class='btn-pro g' style='padding:12px' href='/contact/{a['id']}'>💬 NÉGOCIER</a><a class='btn-pro b' style='padding:12px' href='tel:{a['tel']}'>📞 APPELER</a></div>"
        cards+=f"<div class='card'><div style='display:flex;justify-content:space-between'><b>👷 {a['nom']}</b>{badge}</div><div style='font-weight:800;margin:6px 0'>🛠️ {a['metier']} • 📍 {a['ville']}</div><div style='font-size:13px;color:#555'>{a['description'] or ''}</div><div style='margin-top:12px'>{act}</div></div>"
    return layout(filters+cards)

@app.route('/contact/<int:id>')
def contact(id):
    c=get_db(); a=c.execute("SELECT * FROM artisans WHERE id=?",(id,)).fetchone()
    if a:
        c.execute("UPDATE artisans SET vues=vues+1 WHERE id=?",(id,))
        c.execute("INSERT INTO contacts(artisan_id,artisan_nom,date) VALUES(?,?,?)",(id,a['nom'],datetime.now().strftime("%d/%m/%Y %H:%M")))
        c.execute("INSERT INTO notifications(message,date) VALUES(?,?)",(f"👀 Client a contacté {a['nom']} ({a['metier']})", datetime.now().strftime("%d/%m/%Y %H:%M")))
        c.commit()
    c.close()
    return redirect(f"https://wa.me/225{a['tel']}?text=Salut {a['nom']} via BabiArtisan V16 Wallet pour {a['metier']}")

@app.route('/devenir-artisan',methods=['GET','POST'])
def devenir():
    if request.method=='POST':
        if request.form.get('website'): return "Bot détecté", 400
        nom = clean_input(request.form.get('nom',''), 50)
        metier = clean_input(request.form.get('metier',''), 100)
        ville = clean_input(request.form.get('ville',''), 60)
        tel = clean_input(request.form.get('tel',''), 20)
        precision = clean_input(request.form.get('precision',''), 80)
        desc_raw = clean_input(request.form.get('desc',''), 300)
        desc_full = f"[{precision}] {desc_raw}" if precision else desc_raw
        c=get_db()
        try:
            c.execute("INSERT INTO artisans(nom,metier,ville,tel,description,precision,dette,status,rating,date,last_pay,vues) VALUES(?,?,?,?,?,?,0,'DISPO',4.9,?,?,0)",
            (nom,metier,ville,tel,desc_full,precision,datetime.now().strftime("%d/%m/%Y"),datetime.now().strftime("%d/%m/%Y")))
        except:
            c.execute("INSERT INTO artisans(nom,metier,ville,tel,description,dette,status,rating,date,last_pay,vues) VALUES(?,?,?,?,?,0,'DISPO',4.9,?,?,0)",
            (nom,metier,ville,tel,desc_full,datetime.now().strftime("%d/%m/%Y"),datetime.now().strftime("%d/%m/%Y")))
        artisan_id = c.lastrowid
        c.execute("INSERT INTO wallets(artisan_id,solde,is_blocked,total_gagne) VALUES(?,?,0,0)", (artisan_id, 0))
        c.execute("INSERT INTO notifications(message,date) VALUES(?,?)",(f"🆕 Nouvel artisan V16: {nom} - {metier}", datetime.now().strftime("%d/%m/%Y %H:%M")))
        c.commit(); c.close()
        return layout(f"<div class='card' style='text-align:center'><h1>🎉 Bienvenue {nom} ! V16 Wallet actif</h1><p>Ton solde: 0F. Recharge 2000F Wave {WAVE} pour être visible. En dessous de 50k = gratuit, au dessus 5% auto.</p><a class='btn-pro g' href='/'>VOIR MA FICHE</a></div>")
    return layout("""
<div class='card'><h2>📝 Inscription V16 WALLET YANGO - 30s</h2>
<form method='post'><input type="text" name="website" style="display:none">
<input name='nom' placeholder='👤 Nom complet' required maxlength="50">
<select name='metier' required><option value=''>🛠️ Métier</option><option>Maçon</option><option>Peintre bâtiment</option><option>Mécanicien Moto</option><option>Mécanicien Voiture</option><option>Vendeur de matériaux</option><option>Quincaillerie</option><option>Réparateur tout genre</option><option>Entrepreneur</option><option>Chef chantier</option><option>Vigile</option><option>Nounou</option></select>
<input name='precision' placeholder='🔧 Précise si réparateur: téléphone, frigo...'>
<input name='ville' placeholder='📍 Ville + quartier' required maxlength="60">
<input name='tel' placeholder='📱 WhatsApp 07...' required maxlength="20">
<textarea name='desc' placeholder='💼 Décris ton travail...' rows=4 required maxlength="300"></textarea>
<button class='btn-pro g'>🚀 JE M'INSCRIS - V16 WALLET</button></form></div>
""")

@app.route('/admin', methods=['GET','POST'])
def admin():
    ip = request.remote_addr
    if is_blocked(ip): return layout("<div class='card'><h2>⛔ Trop d'essais. Attends 5 min.</h2></div>", is_admin=True)
    if session.get('admin_logged'): return redirect(url_for('dashboard'))
    error=None
    if request.method=='POST':
        taped = request.form.get('password','').replace("\n","").replace("\r","").replace(" ","").strip()
        if taped == ADMIN_PASSWORD:
            session['admin_logged']=True
            return redirect(url_for('dashboard'))
        else:
            add_attempt(ip)
            error=f"Mauvais ! {len(taped)} caractères"
    return layout(f"<div class='card' style='max-width:400px;margin:40px auto'><h2>🔐 BOSS DJINWOO V16 WALLET</h2><form method='post'><input type='password' name='password' placeholder='Mot de passe' required><button class='btn-pro b'>ENTRER</button></form><p style='color:red'>{error or ''}</p></div>", is_admin=True)

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    c=get_db()
    arts=c.execute("SELECT * FROM artisans ORDER BY id DESC").fetchall()
    wallets=c.execute("SELECT * FROM wallets").fetchall()
    wallet_map = {w['artisan_id']: w for w in wallets}
    trans=c.execute("SELECT * FROM wallet_transactions ORDER BY id DESC LIMIT 30").fetchall()
    notifs=c.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 20").fetchall()
    notif_count=c.execute("SELECT COUNT(*) as n FROM notifications WHERE lu=0").fetchone()['n']
    total=len(arts); dette=sum(a['dette'] or 0 for a in arts)
    total_wallet = sum(w['solde'] for w in wallets)
    total_commission = sum(t['montant'] for t in trans if t['type']=='DEBIT_COMMISSION')
    c.close()
    head=f"""
<div class='card' style='background:#111;color:#fff'><h2>🔐 CENTRE V16 WALLET YANGO - DJINWOO</h2>
<div style='display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;text-align:center;margin-top:12px'>
<div><b>{total}</b><br><small>Artisans</small></div>
<div><b style='color:#00ff88'>{total_wallet}F</b><br><small>Solde wallets</small></div>
<div><b style='color:#ffcc00'>{total_commission}F</b><br><small>Commissions V16</small></div>
<div><b>🔔 {notif_count}</b><br><small>Notifs</small></div>
</div>
<p style='font-size:12px;margin-top:10px'>Wave: {WAVE} • V16 Règle: {'<'}50k=0F | 50k=2500F 5% auto • Play Store READY /privacy /terms</p>
<div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px'><a class='btn-pro o' href='/'>Voir site</a><a class='btn-pro' style='background:#333;color:#fff' href='/admin/logout'>Déco</a></div></div>
<div class='card'><h3>💳 Transactions Wallet V16 (30 dernières)</h3>{"".join([f"<div style='padding:6px 0;border-bottom:1px solid #eee;font-size:12px'>{t['date']} - Artisan {t['artisan_id']} - {t['type']} {t['montant']}F - Marché {t['marche_montant'] or 0}F - Ref:{t['reference_wave']}</div>" for t in trans]) or "<small>Aucune</small>"}</div>
"""
    body="".join([f"<div class='card'><b>{a['id']}. {a['nom']} | {a['metier']} | {a['ville']}</b><br><small>Wallet: <b style='color:{'green' if wallet_map.get(a['id'], {'solde':0})['solde']>0 else 'red'}'>{wallet_map.get(a['id'], {'solde':0, 'is_blocked':0})['solde']}F</b> | Bloqué: {'OUI 🔒' if wallet_map.get(a['id'], {'is_blocked':0})['is_blocked'] else 'NON ✅'} | Dette old: {a['dette']}F</small><div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:8px'><a class='btn-pro' style='background:#00d26a;color:#fff;padding:8px;font-size:12px' href='/admin/wallet/add/{a['id']}/2000'>+2000F Wallet</a><a class='btn-pro' style='background:#f59e0b;color:#fff;padding:8px;font-size:12px' href='/commission/{a['id']}/1000'>+Dette old</a><a class='btn-pro' style='background:#111;color:#fff;padding:8px;font-size:12px' href='/admin/wallet/solde/{a['id']}'>Voir solde</a></div></div>" for a in arts])
    return layout(head+body, is_admin=True, notif_count=notif_count)

@app.route('/admin/wallet/add/<int:id>/<int:montant>')
def admin_wallet_add(id,montant):
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    c=get_db()
    c.execute("INSERT OR IGNORE INTO wallets(artisan_id,solde,is_blocked,total_gagne) VALUES(?,?,0,0)", (id,0))
    c.execute("UPDATE wallets SET solde=solde+?, is_blocked=0 WHERE artisan_id=?", (montant,id))
    ref = f"ADMIN-{int(time.time())}-{id}"
    sec_hash = hashlib.sha256(f"{id}{montant}{ref}{SECRET_KEY}".encode()).hexdigest()
    c.execute("INSERT INTO wallet_transactions(artisan_id,type,montant,marche_montant,reference_wave,date,security_hash) VALUES(?,?,?,?,?,?,?)", (id,'CREDIT_WAVE',montant,0,ref,datetime.now().strftime("%d/%m/%Y %H:%M"),sec_hash))
    c.commit(); c.close()
    return redirect(url_for('dashboard'))

@app.route('/admin/wallet/solde/<int:id>')
def admin_wallet_solde(id):
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    return redirect(f"/api/wallet/solde/{id}")

@app.route('/admin/notif-lu')
def notif_lu():
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    c=get_db(); c.execute("UPDATE notifications SET lu=1"); c.commit(); c.close()
    return redirect(url_for('dashboard'))
@app.route('/commission/<int:id>/<int:montant>')
def commission(id,montant):
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    c=get_db(); c.execute("UPDATE artisans SET dette=dette+?,status='BLOQUE' WHERE id=?",(montant,id)); c.commit(); c.close(); return redirect(url_for('dashboard'))
@app.route('/debloquer/<int:id>')
def debloquer(id):
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    c=get_db(); c.execute("UPDATE artisans SET dette=0,status='DISPO',last_pay=? WHERE id=?",(datetime.now().strftime("%d/%m/%Y"),id)); c.execute("UPDATE wallets SET is_blocked=0 WHERE artisan_id=?",(id,)); c.commit(); c.close(); return redirect(url_for('dashboard'))
@app.route('/supprimer/<int:id>')
def supprimer(id):
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    c=get_db(); c.execute("DELETE FROM artisans WHERE id=?",(id,)); c.execute("DELETE FROM wallets WHERE artisan_id=?",(id,)); c.commit(); c.close(); return redirect(url_for('dashboard'))
@app.route('/admin/logout')
def logout():
    session.pop('admin_logged',None); return redirect(url_for('admin'))

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
