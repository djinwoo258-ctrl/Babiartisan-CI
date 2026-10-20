import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session, url_for, Response, jsonify
import re, time
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

# --- SÉCURITÉ V13 RENFORCÉE AJOUTÉE ---
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
# --- FIN SÉCURITÉ V13 ---

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
    # --- AJOUTS V13 SANS CASSER ---
    try:
        c.execute("SELECT precision FROM artisans LIMIT 1")
    except:
        try: c.execute("ALTER TABLE artisans ADD COLUMN precision TEXT DEFAULT ''")
        except: pass
    # Table notifications V13
    c.execute("""CREATE TABLE IF NOT EXISTS notifications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT, date TEXT, lu INTEGER DEFAULT 0)""")
    c.commit(); c.close()
init_db()

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
<meta name="description" content="artisan CI - BabiArtisan-CI N°1 pour trouver un artisan en Côte d'Ivoire. Maçon, mécano moto, auto, vélo, peintre, vigile, nounou à Abidjan et intérieur.">
<meta name="keywords" content="artisan CI, artisan Abidjan, artisan Côte d'Ivoire, BabiArtisan, artisan Bouaké, Yamoussoukro, San-Pedro, Korhogo, vendeur materiaux, quincaillerie, reparateur, entrepreneur, chef chantier">
<meta property="og:title" content="artisan CI | BabiArtisan-CI - Toute la Côte d'Ivoire">
<meta property="og:description" content="Trouve un artisan qualifié partout en Côte d'Ivoire en 30 secondes">
<meta property="og:image" content="https://babiartisan-ci.onrender.com/icon.png">
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/icon.png">
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
.hero-pro p.sub{{font-size:17px;opacity:.9;line-height:1.4;margin-bottom:20px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.btn-pro{{display:block;padding:18px;border-radius:16px;text-align:center;font-weight:900;text-decoration:none;transition:.15s;font-size:15px}}
.btn-pro:active{{transform:scale(.96)}}
.g{{background:linear-gradient(135deg,#00d26a,#00ff88);color:#000;box-shadow:0 10px 30px rgba(0,255,136,.3)}}
.o{{background:#fff;color:#111}}
.b{{background:#111;color:#fff}}
.wrap{{max-width:800px;margin:0 auto;padding:0 14px 100px}}
.card{{background:#fff;border-radius:24px;padding:20px;margin:16px 0;box-shadow:0 10px 40px rgba(0,0,0,.06);border:1px solid #f0f0f0}}
.stat{{display:flex;justify-content:space-around;text-align:center;padding:14px 0}}
.stat b{{font-size:26px;display:block}}
input,select,textarea{{width:100%;padding:16px;border-radius:14px;border:1.5px solid #e5e7eb;margin:7px 0;font-size:15px}}
.pill{{padding:8px 14px;background:#f3f4f6;border-radius:99px;font-size:13px;text-decoration:none;color:#111;font-weight:700;display:inline-block;margin:4px}}
.badge{{padding:6px 12px;border-radius:99px;font-size:11px;font-weight:800}}
.ok{{background:#dcfce7;color:#166534}}.ko{{background:#fee2e2;color:#991b1b}}
.why{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin:16px 0}}
.why div{{background:#fff;padding:14px;border-radius:18px;text-align:center;border:1px solid #eee}}
.notif-bell{{position:fixed;top:15px;right:15px;background:#111;color:#fff;padding:12px 16px;border-radius:99px;font-weight:900;z-index:999;box-shadow:0 5px 20px rgba(0,0,0,.3)}}
</style>
<script>
if ('serviceWorker' in navigator) {{
  window.addEventListener('load', function() {{
    navigator.serviceWorker.register('/sw.js');
  }});
}}
</script>
"""

def layout(content, is_admin=False, notif_count=0):
    check_abo()
    bell = f"<div class='notif-bell'>🔔 {notif_count} nouvelle(s)</div>" if is_admin and notif_count>0 else ""
    nav = "" if is_admin else f"""
    <div class='hero-pro'>
      <img class='bg' src='hero.jpg' onerror="this.src='https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=1200'">
      <div class='content'>
        <div class='badge-top'>🇨🇮 N°1 EN CÔTE D'IVOIRE • TOUTE LA CI • +200 ARTISANS</div>
        <h1>Tu es artisan ?<br>On t'envoie des <span>clients tous les jours.</span></h1>
        <p class='sub'>Maçon, Mécano Moto/Voiture/Vélo, Peintre, Vigile, Nounou, Vendeur matériaux, Quincaillerie, Réparateur, Entrepreneur, Chef chantier... Tu t'inscris en 30s, c'est GRATUIT partout en Côte d'Ivoire. Tu ne paies que 1% quand tu gagnes un marché.</p>
        <div class='grid2'>
          <a class='btn-pro g' href='/devenir-artisan'>🚀 JE VEUX DES CLIENTS</a>
          <a class='btn-pro o' href='#liste'>🔍 TROUVER UN PRO</a>
        </div>
      </div>
    </div>
    <div class='wrap'>
      <div class='why'>
        <div><b style='font-size:22px'>💰</b><br><b>Tu gagnes</b><br><small>50k = 500F seulement</small></div>
        <div><b style='font-size:22px'>📱</b><br><b>Clients WhatsApp</b><br><small>Direct sur ton tel</small></div>
        <div><b style='font-size:22px'>🔥</b><br><b>Toute la CI</b><br><small>Abidjan à Korhogo</small></div>
      </div>
    """
    end = "</div>" if not is_admin else ""
    return f"<html><head>{CSS}</head><body>{bell}{nav}{content}{end}</body></html>"

@app.route('/google-site-verification.html')
@app.route(f'/{GOOGLE_CODE}.html')
def google_file():
    return f"google-site-verification: google-site-verification={GOOGLE_CODE}"
@app.route('/robots.txt')
def robots():
    return Response("User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /admin/*\nSitemap: https://babiartisan-ci.onrender.com/sitemap.xml", mimetype="text/plain")
@app.route('/sitemap.xml')
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://babiartisan-ci.onrender.com/</loc><priority>1.0</priority></url>
  <url><loc>https://babiartisan-ci.onrender.com/devenir-artisan</loc><priority>0.8</priority></url>
</urlset>"""
    return Response(xml, mimetype="application/xml")
@app.route('/manifest.json')
def manifest():
    return jsonify({"name": "artisan CI - BabiArtisan-CI","short_name": "artisan CI","description": "Trouve un artisan en Côte d'Ivoire - Toute la CI","start_url": "/","display": "standalone","background_color": "#f8faf8","theme_color": "#00d26a","icons": [{"src": "/icon.png", "sizes": "512x512", "type": "image/png"}]})
@app.route('/sw.js')
def sw():
    js = "self.addEventListener('install', e => self.skipWaiting()); self.addEventListener('activate', e => self.clients.claim()); self.addEventListener('fetch', e => e.respondWith(fetch(e.request).catch(()=>caches.match(e.request))));"
    return Response(js, mimetype="application/javascript")
@app.route('/icon.png')
def icon():
    return redirect("https://cdn-icons-png.flaticon.com/512/1995/1995515.png")

@app.route('/')
def home():
    ville=request.args.get('ville','').strip()
    metier=request.args.get('metier','').strip()
    c=get_db()
    arts=c.execute("SELECT * FROM artisans ORDER BY vues DESC, id DESC").fetchall()
    if ville: arts=[a for a in arts if ville.lower() in a['ville'].lower()]
    if metier: arts=[a for a in arts if metier.lower() in a['metier'].lower()]
    contacts=c.execute("SELECT COUNT(*) as n FROM contacts").fetchone()['n']
    c.close()
    filters=f"""
    <div class='card' style='text-align:center'>
      <h2>👋 {len(arts)} pros disponibles dans toute la CI</h2>
      <p style='color:#666;font-size:13px'>{contacts} mises en relation • Vérifiés • 4.9/5 • Toute la Côte d'Ivoire</p>
      <form style='display:flex;gap:8px;margin-top:14px'><input name='ville' placeholder='📍 Ville (Bouaké, Yakro...)' value='{ville}'><input name='metier' placeholder='🛠️ Métier' value='{metier}'><button class='btn-pro g' style='width:110px;padding:12px'>🔍</button></form>
      <div style='margin-top:12px'><a class='pill' href='/'>Tous CI</a><a class='pill' href='/?metier=maçon'>🧱 Maçon</a><a class='pill' href='/?metier=peintre'>🎨 Peintre</a><a class='pill' href='/?metier=moto'>🏍️ Moto</a><a class='pill' href='/?metier=voiture'>🚗 Auto</a><a class='pill' href='/?metier=vélo'>🚲 Vélo</a><a class='pill' href='/?metier=matériaux'>🧱 Matériaux</a><a class='pill' href='/?metier=quincaillerie'>🔩 Quincaillerie</a><a class='pill' href='/?metier=réparateur'>🔧 Réparateur</a><a class='pill' href='/?metier=entrepreneur'>🏗️ Entrepreneur</a><a class='pill' href='/?metier=chef chantier'>👷 Chef chantier</a></div>
    </div>"""
    cards="<div id='liste'></div>"
    for a in arts[:150]:
        bloque=(a['dette'] or 0)>0 or a['status']!='DISPO'
        try: prec = a['precision'] if 'precision' in a.keys() and a['precision'] else ""
        except: prec=""
        prec_txt = f" ({prec})" if prec else ""
        badge=f"<span class='badge ko'>🔒 {a['dette']}F dû</span>" if bloque else f"<span class='badge ok'>✅ DISPO • {a['rating']}⭐ • {a['vues']} vues</span>"
        if bloque:
            act=f"<div style='background:#fef2f2;padding:12px;border-radius:12px;text-align:center'><b style='color:#991b1b'>BLOQUÉ - Doit {a['dette']}F Wave {WAVE}</b></div>"
        else:
            act=f"<div class='grid2'><a class='btn-pro g' style='padding:12px' href='/contact/{a['id']}'>💬 NÉGOCIER</a><a class='btn-pro b' style='padding:12px' href='tel:{a['tel']}'>📞 APPELER</a></div>"
        cards+=f"<div class='card'><div style='display:flex;justify-content:space-between'><b>👷 {a['nom']}</b>{badge}</div><div style='font-weight:800;margin:6px 0'>🛠️ {a['metier']}{prec_txt} • 📍 {a['ville']}</div><div style='font-size:13px;color:#555'>{a['description'] or ''}</div><div style='margin-top:12px'>{act}</div></div>"
    if not arts:
        cards+="<div class='card' style='text-align:center'><h3>🚀 Sois le 1er dans ta zone !</h3><a class='btn-pro g' href='/devenir-artisan'>JE M'INSCRIS GRATUIT</a></div>"
    return layout(filters+cards)

@app.route('/contact/<int:id>')
def contact(id):
    c=get_db(); a=c.execute("SELECT * FROM artisans WHERE id=?",(id,)).fetchone()
    if a:
        c.execute("UPDATE artisans SET vues=vues+1 WHERE id=?",(id,))
        c.execute("INSERT INTO contacts(artisan_id,artisan_nom,date) VALUES(?,?,?)",(id,a['nom'],datetime.now().strftime("%d/%m/%Y %H:%M")))
        c.execute("INSERT INTO notifications(message,date) VALUES(?,?)",(f"👀 Client a contacté {a['nom']} ({a['metier']}) à {a['ville']}", datetime.now().strftime("%d/%m/%Y %H:%M")))
        c.commit()
    c.close()
    return redirect(f"https://wa.me/225{a['tel']}?text=Salut {a['nom']} 👋 via BabiArtisan CI pour {a['metier']} à {a['ville']}")

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
        c.execute("INSERT INTO notifications(message,date) VALUES(?,?)",(f"🆕 Nouvel artisan: {nom} - {metier} {('('+precision+')') if precision else ''} à {ville}", datetime.now().strftime("%d/%m/%Y %H:%M")))
        c.commit(); c.close()
        return layout(f"<div class='card' style='text-align:center'><h1>🎉 Bienvenue {nom} !</h1><p>Tu es visible dans toute la Côte d'Ivoire. Tu vas recevoir des clients sur WhatsApp.</p><a class='btn-pro g' href='/'>VOIR MA FICHE</a></div>")
    return layout("""
<div class='card'><h2>📝 Inscription 30s - SANS MOT DE PASSE - TOUTE LA CI</h2>
<form method='post' id='formArtisan'>
<input type="text" name="website" style="display:none">
<input name='nom' placeholder='👤 Nom complet' required maxlength="50">
<select name='metier' id='metierSelect' required onchange="checkReparateur()">
<option value=''>🛠️ Choisis ton métier</option>
<optgroup label='🏗️ BÂTIMENT'><option>Maçon</option><option>Peintre bâtiment</option><option>Carreleur</option><option>Menuisier</option><option>Plombier</option><option>Électricien</option><option>Soudeur</option><option>Climatisation</option></optgroup>
<optgroup label='🔧 MÉCANIQUE'><option>Mécanicien Moto</option><option>Mécanicien Voiture</option><option>Mécanicien Vélo</option><option>Électricien Auto</option></optgroup>
<optgroup label='🧱 MATÉRIAUX & COMMERCE - NOUVEAU V13'><option>Vendeur de matériaux - briques/sable/gravier/ciment</option><option>Quincaillerie</option></optgroup>
<optgroup label='🔧 RÉPARATION & DIRECTION - NOUVEAU V13'><option>Réparateur tout genre</option><option>Entrepreneur</option><option>Chef chantier</option></optgroup>
<optgroup label='🛡️ SERVICE PLUS'><option>Vigile / Sécurité</option><option>Nounou</option><option>Sage-femme</option></optgroup>
</select>
<div id='precisionBox' style='display:none'>
<input name='precision' id='precisionInput' placeholder='🔧 Précise: téléphone, frigo, clim, TV, ordinateur...'>
<small style='color:#666'>Si tu choisis Réparateur tout genre, précise exactement ce que tu répares</small>
</div>
<input name='ville' placeholder='📍 Ville + quartier (ex: Bouaké, Yamoussoukro...)' required maxlength="60">
<input name='tel' placeholder='📱 WhatsApp 07...' required maxlength="20">
<textarea name='desc' placeholder='💼 Décris ton travail...' rows=4 required maxlength="300"></textarea>
<button class='btn-pro g'>🚀 JE M'INSCRIS - GRATUIT</button>
</form><a class='btn-pro b' href='/'>← Retour</a></div>
<script>
function checkReparateur(){
  var m = document.getElementById('metierSelect').value;
  var box = document.getElementById('precisionBox');
  if(m.toLowerCase().includes('réparateur')){
    box.style.display='block';
    document.getElementById('precisionInput').required=true;
  } else {
    box.style.display='none';
    document.getElementById('precisionInput').required=false;
  }
}
</script>
""")

# --- TON CODE SECRET BOSS CONSERVÉ À 100% ---
@app.route('/admin', methods=['GET','POST'])
def admin():
    ip = request.remote_addr
    if is_blocked(ip): return layout("<div class='card' style='text-align:center'><h2>⛔ Trop d'essais. Attends 5 minutes.</h2></div>", is_admin=True)
    if session.get('admin_logged'):
        return redirect(url_for('dashboard'))
    error=None
    if request.method=='POST':
        taped = request.form.get('password','').replace("\n","").replace("\r","").replace(" ","").strip()
        if taped == ADMIN_PASSWORD:
            session['admin_logged']=True
            return redirect(url_for('dashboard'))
        else:
            add_attempt(ip)
            error=f"Mauvais ! Tentative bloquée. Tu as tapé {len(taped)} caractères, attendu {len(ADMIN_PASSWORD)}"
    return layout(f"""
<div class='card' style='max-width:400px;margin:40px auto'><h2>🔐 Centre BabiArtisan - BOSS DJINWOO</h2><p style='font-size:12px;color:#666'>Seul le boss a le code secret central</p>
<form method='post'><input type='password' name='password' placeholder='Mot de passe secret central' required><button class='btn-pro b'>ENTRER AU CENTRE</button></form>
<p style='color:red;font-size:12px'>{error or ''}</p><p style='font-size:10px;color:#999;margin-top:10px'>V13 Sécurisée - Anti-bot - Anti-pirate - Notifications 🔔</p></div>
""", is_admin=True)

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    c=get_db()
    arts=c.execute("SELECT * FROM artisans ORDER BY dette DESC, id DESC").fetchall()
    contacts=c.execute("SELECT * FROM contacts ORDER BY id DESC LIMIT 100").fetchall()
    notifs=c.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 20").fetchall()
    notif_count=c.execute("SELECT COUNT(*) as n FROM notifications WHERE lu=0").fetchone()['n']
    total=len(arts); dette=sum(a['dette'] or 0 for a in arts); vues=sum(a['vues'] or 0 for a in arts)
    c.close()
    head=f"""
<div class='card' style='background:#111;color:#fff'><h2>🔐 CENTRE DE CONTRÔLE - DJINWOO - V13</h2>
<div class='stat'><div><b>{total}</b><small>Artisans</small></div><div><b style='color:#00ff88'>{dette}F</b><small>À encaisser</small></div><div><b>{vues}</b><small>Vues</small></div><div><b style='color:#ff6b00'>🔔 {notif_count}</b><small>Notifs</small></div></div>
<p style='font-size:12px;margin-top:10px'>Wave: {WAVE} • Code central: {len(ADMIN_PASSWORD)} caractères • V13 Sécurisée • Vision: Toute la Côte d'Ivoire</p>
<div class='grid2' style='margin-top:12px'><a class='btn-pro o' href='/'>Voir site</a><a class='btn-pro' style='background:#333;color:#fff' href='/admin/logout'>Déconnexion</a></div></div>
<div class='card' style='border:2px solid #00ff88'><h3>🔔 Notifications V13 ({notif_count} non lues) <a href='/admin/notif-lu' style='font-size:11px'>Tout marquer lu</a></h3>{"".join([f"<div style='padding:8px 0;border-bottom:1px solid #eee;font-size:13px;{'' if n['lu']==0 else 'opacity:.5'}'>{'🔴' if n['lu']==0 else '⚪'} {n['date']} - {n['message']}</div>" for n in notifs]) or "<small>Aucune notif</small>"}</div>
<div class='card'><h3>📋 {len(contacts)} Contacts clients récents</h3>{"".join([f"<div style='padding:6px 0;border-bottom:1px solid #eee;font-size:12px'>📅 {ct['date']} - Client → <b>{ct['artisan_nom']}</b></div>" for ct in contacts[:20]]) or "<small>Aucun</small>"}</div>
"""
    def get_prec(a):
        try: return a['precision'] if 'precision' in a.keys() and a['precision'] else ""
        except: return ""
    body="".join([f"<div class='card'><b>{a['id']}. {a['nom']} | {a['metier']} {('('+get_prec(a)+')') if get_prec(a) else ''} | {a['ville']} | {a['tel']}</b><br><small>Dette: <b style='color:red'>{a['dette']}F</b> | {a['status']} | {a['vues']} vues</small><div class='grid2' style='margin-top:8px'><a class='btn-pro' style='background:#f59e0b;color:#fff;padding:8px' href='/commission/{a['id']}/500'>+500F</a><a class='btn-pro' style='background:#f59e0b;color:#fff;padding:8px' href='/commission/{a['id']}/1000'>+1000F</a></div><div class='grid2'><a class='btn-pro g' style='padding:8px' href='/debloquer/{a['id']}'>✅ Payé</a><a class='btn-pro r' style='padding:8px;background:#e11d48;color:#fff' href='/supprimer/{a['id']}'>🗑️ Suppr</a></div></div>" for a in arts])
    return layout(head+body, is_admin=True, notif_count=notif_count)

@app.route('/admin/notif-lu')
def notif_lu():
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    c=get_db(); c.execute("UPDATE notifications SET lu=1"); c.commit(); c.close()
    return redirect(url_for('dashboard'))

@app.route('/commission/<int:id>/<int:montant>')
def commission(id,montant):
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    c=get_db(); c.execute("UPDATE artisans SET dette=dette+?,status='BLOQUE' WHERE id=?",(montant,id)); c.execute("INSERT INTO notifications(message,date) VALUES(?,?)",(f"💰 Commission {montant}F ajoutée à artisan {id}", datetime.now().strftime("%d/%m/%Y %H:%M"))); c.commit(); c.close(); return redirect(url_for('dashboard'))
@app.route('/debloquer/<int:id>')
def debloquer(id):
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    c=get_db(); c.execute("UPDATE artisans SET dette=0,status='DISPO',last_pay=? WHERE id=?",(datetime.now().strftime("%d/%m/%Y"),id)); c.execute("INSERT INTO notifications(message,date) VALUES(?,?)",(f"✅ Artisan {id} débloqué (payé)", datetime.now().strftime("%d/%m/%Y %H:%M"))); c.commit(); c.close(); return redirect(url_for('dashboard'))
@app.route('/supprimer/<int:id>')
def supprimer(id):
    if not session.get('admin_logged'): return redirect(url_for('admin'))
    c=get_db(); c.execute("DELETE FROM artisans WHERE id=?",(id,)); c.commit(); c.close(); return redirect(url_for('dashboard'))
@app.route('/admin/logout')
def logout():
    session.pop('admin_logged',None); return redirect(url_for('admin'))

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
