
from flask import Flask, request, redirect, session, abort
import sqlite3, os, html
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
# SÉCURITÉ 1 : clé secrète depuis Render, pas dans le code
app.secret_key = os.environ.get("SECRET_KEY", "change-moi-en-prod-urgence-123456789")
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True

DB='babiartisan_v10.db'
WAVE="0596003270"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Babi2026!Fort_0596")

def get_db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    c=get_db()
    c.execute("""CREATE TABLE IF NOT EXISTS artisans(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT, metier TEXT, ville TEXT, tel TEXT, description TEXT,
    dette INTEGER DEFAULT 0, status TEXT DEFAULT 'DISPO', rating REAL DEFAULT 4.9,
    date TEXT, last_pay TEXT, vues INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS contacts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_tel TEXT, artisan_id INTEGER, artisan_nom TEXT, date TEXT)""")
    c.commit(); c.close()
init_db()

# SÉCURITÉ 2 : décorateur qui protège l'admin
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('is_admin') != True:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def check_abonnement():
    c=get_db(); arts=c.execute("SELECT * FROM artisans").fetchall()
    for a in arts:
        try:
            d=datetime.strptime(a['last_pay'] or a['date'], "%d/%m/%Y")
            if datetime.now() - d > timedelta(days=30) and a['status']=='DISPO':
                c.execute("UPDATE artisans SET dette=dette+1000,status='BLOQUE' WHERE id=?",(a['id'],))
        except: pass
    c.commit(); c.close()

CSS="""
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BabiArtisan CI - Tous les pros de CI</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,sans-serif}
body{background:#f5f7f5}
.hero{position:relative;width:100%;height:400px;overflow:hidden}
.hero img{width:100%;height:100%;object-fit:cover;filter:blur(1.5px) brightness(0.6)}
.hero .grad{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.15),rgba(0,0,0,.8))}
.hero .txt{position:absolute;bottom:22px;left:16px;right:16px;color:#fff}
.hero .txt h1{font-size:34px;font-weight:900;letter-spacing:-1px}
.wrap{max-width:740px;margin:0 auto;padding:0 12px 90px}
.card{background:#fff;border-radius:22px;padding:18px;margin:14px 0;box-shadow:0 12px 40px rgba(0,0,0,.08);border:1px solid #f0f0f0}
.btn{display:block;width:100%;padding:16px;border-radius:14px;text-align:center;font-weight:900;text-decoration:none;margin:8px 0;transition:.15s}
.btn:active{transform:scale(.97)}
.g{background:linear-gradient(135deg,#00a859,#00d26a);color:#fff}
.o{background:linear-gradient(135deg,#ff8c00,#ffb700);color:#fff}
.b{background:#111;color:#fff}.r{background:#e11d48;color:#fff}
.badge{padding:6px 12px;border-radius:99px;font-size:11px;font-weight:800}
.ok{background:#dcfce7;color:#166534}.ko{background:#fee2e2;color:#991b1b}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
input,select,textarea{width:100%;padding:15px;border-radius:12px;border:1.5px solid #e5e7eb;margin:7px 0;font-size:15px}
.pill{padding:9px 15px;background:#f3f4f6;border-radius:99px;font-size:13px;text-decoration:none;color:#111;font-weight:700;display:inline-block;margin:4px}
</style>
"""

def layout(content):
    check_abonnement()
    hero=f"<div class='hero'><img src='https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=900'><div class='grad'></div><div class='txt'><h1>BABIARTISAN CI</h1><p>🇨🇮 Bâtiment • Moto • Auto • Vélo • Vigile • Nounou • Sage-femme<br><small>{WAVE} • Le N°1 des pros de confiance</small></p></div></div>"
    return f"<html><head>{CSS}</head><body>{hero}<div class='wrap'>{content}</div></body></html>"

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect('/admin')
        else:
            return layout("<div class='card' style='background:#fee2e2'><b>❌ Mauvais mot de passe</b><br><a href='/login'>Réessayer</a></div>")
    return layout("<div class='card'><h2>🔐 Admin Login</h2><form method='post'><input type='password' name='password' placeholder='Mot de passe admin' required><button class='btn b'>SE CONNECTER</button></form></div>")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/')
def home():
    ville=html.escape(request.args.get('ville','').strip())
    metier=html.escape(request.args.get('metier','').strip())
    c=get_db(); arts=c.execute("SELECT * FROM artisans ORDER BY vues DESC, id DESC").fetchall()
    if ville: arts=[a for a in arts if ville.lower() in a['ville'].lower()]
    if metier: arts=[a for a in arts if metier.lower() in a['metier'].lower()]
    contacts=c.execute("SELECT COUNT(*) as n FROM contacts").fetchone()['n']
    c.close()
    top=f"""<div class='card' style='text-align:center'><h2>👋 Trouve ton pro en 2 min !</h2><p style='color:#666;font-size:14px'>{len(arts)} artisans vérifiés • {contacts} mises en relation</p><form style='display:flex;gap:8px;margin-top:14px'><input name='ville' placeholder='📍 Ville' value='{ville}'><input name='metier' placeholder='🛠️ Métier' value='{metier}'><button class='btn g' style='width:110px'>🔍</button></form><div style='margin-top:14px'><a class='pill' href='/'>Tous</a><a class='pill' href='/?metier=maçon'>🧱 Maçon</a><a class='pill' href='/?metier=carreleur'>🟦 Carreleur</a><a class='pill' href='/?metier=peintre'>🎨 Peintre</a><a class='pill' href='/?metier=moto'>🏍️ Moto</a><a class='pill' href='/?metier=voiture'>🚗 Auto</a><a class='pill' href='/?metier=vélo'>🚲 Vélo</a><a class='pill' href='/?metier=vigile'>🛡️ Vigile</a><a class='pill' href='/?metier=nounou'>👶 Nounou</a></div></div><div class='grid2'><a class='btn g' href='#liste'>🔍 VOIR {len(arts)} PROS</a><a class='btn o' href='/devenir-artisan'>✨ DEVENIR ARTISAN</a></div>"""
    cards="<div id='liste'></div>"
    for a in arts[:150]:
        bloque=(a['dette'] or 0)>0 or a['status']!='DISPO'
        badge=f"<span class='badge ko'>🔒 {a['dette']}F dû</span>" if bloque else f"<span class='badge ok'>✅ DISPO • {a['rating']}⭐ • {a['vues']} vues</span>"
        if bloque:
            act=f"<div style='background:#fef2f2;padding:12px;border-radius:12px;text-align:center'><b style='color:#991b1b'>BLOQUÉ - Doit {a['dette']}F</b><br><small>Payer sur Wave {WAVE}</small></div>"
        else:
            act=f"<div class='grid2'><a class='btn g' href='/contact/{a['id']}' style='padding:12px'>💬 NÉGOCIER</a><a class='btn b' href='tel:{a['tel']}' style='padding:12px'>📞 APPELER</a></div>"
        cards+=f"<div class='card'><div style='display:flex;justify-content:space-between;align-items:center'><b>👷 {html.escape(a['nom'])}</b>{badge}</div><div style='color:#222;font-weight:700;margin:6px 0'>🛠️ {html.escape(a['metier'])} • 📍 {html.escape(a['ville'])}</div><div style='font-size:13px;color:#555;line-height:1.4'>{html.escape(a['description'] or '')}</div><div style='margin-top:12px'>{act}</div></div>"
    if not arts: cards+="<div class='card' style='text-align:center'><h3>🚀 Sois le premier !</h3><a class='btn o' href='/devenir-artisan'>JE M'INSCRIS</a></div>"
    return layout(top+cards)

@app.route('/contact/<int:id>')
def contact(id):
    c=get_db(); a=c.execute("SELECT * FROM artisans WHERE id=?",(id,)).fetchone()
    if a:
        c.execute("UPDATE artisans SET vues=vues+1 WHERE id=?",(id,))
        c.execute("INSERT INTO contacts(artisan_id,artisan_nom,date) VALUES(?,?,?)",(id,a['nom'],datetime.now().strftime("%d/%m/%Y %H:%M")))
        c.commit()
    c.close()
    if not a: abort(404)
    return redirect(f"https://wa.me/225{a['tel']}?text=Salut {a['nom']} 👋 Je cherche {a['metier']} à {a['ville']} via BabiArtisan CI. On peut négocier ?")

@app.route('/devenir-artisan',methods=['GET','POST'])
def devenir():
    if request.method=='POST':
        # SÉCURITÉ 3 : limiter la taille
        nom = html.escape(request.form['nom'][:50])
        metier = html.escape(request.form['metier'][:50])
        ville = html.escape(request.form['ville'][:50])
        tel = html.escape(request.form['tel'][:20])
        desc = html.escape(request.form['desc'][:300])
        c=get_db()
        c.execute("INSERT INTO artisans(nom,metier,ville,tel,description,dette,status,rating,date,last_pay,vues) VALUES(?,?,?,?,?,0,'DISPO',4.9,?,?,0)",
        (nom,metier,ville,tel,desc,datetime.now().strftime("%d/%m/%Y"),datetime.now().strftime("%d/%m/%Y")))
        c.commit(); c.close()
        return redirect('/')
    return layout("""... TON FORMULAIRE ...""")

@app.route('/admin')
@admin_required
def admin():
    c=get_db()
    arts=c.execute("SELECT * FROM artisans ORDER BY dette DESC, id DESC").fetchall()
    contacts=c.execute("SELECT * FROM contacts ORDER BY id DESC LIMIT 100").fetchall()
    total=len(arts); dette=sum(a['dette'] or 0 for a in arts)
    vues=sum(a['vues'] or 0 for a in arts)
    c.close()
    head=f"""
<div class='card' style='background:#111;color:#fff'><h2>🔐 ADMIN SÉCURISÉ</h2>
<div class='grid3' style='margin-top:12px;text-align:center'><div><b style='font-size:22px'>{total}</b><br><small>Artisans</small></div><div><b style='font-size:22px;color:#fbbf24'>{dette}F</b><br><small>À encaisser</small></div><div><b style='font-size:22px'>{vues}</b><br><small>Vues</small></div></div>
<p style='margin-top:12px;font-size:13px'>Wave: {WAVE} • {len(contacts)} contacts <a href='/logout' style='color:#fbbf24'>[Déconnexion]</a></p></div>
"""
    body="".join([f"<div class='card'><b>{a['id']}. {html.escape(a['nom'])} | {html.escape(a['metier'])} | {html.escape(a['ville'])} | {html.escape(a['tel'])}</b><br><small>Dette: <b style='color:red'>{a['dette']}F</b> | {a['status']} | Vues: {a['vues']}</small><div class='grid3' style='margin-top:10px'><a class='btn' style='background:#f59e0b;color:#fff;padding:10px;font-size:11px' href='/commission/{a['id']}/500'>+500F</a><a class='btn' style='background:#f59e0b;color:#fff;padding:10px;font-size:11px' href='/commission/{a['id']}/1000'>+1000F</a><a class='btn' style='background:#f59e0b;color:#fff;padding:10px;font-size:11px' href='/commission/{a['id']}/1500'>+1500F</a></div><div class='grid3'><a class='btn g' style='padding:10px;font-size:12px' href='/debloquer/{a['id']}'>✅ Payé</a><a class='btn b' style='padding:10px;font-size:12px' href='/bloquer/{a['id']}'>❌ +1000F</a><a class='btn r' style='padding:10px;font-size:12px' href='/supprimer/{a['id']}'>🗑️ Suppr</a></div></div>" for a in arts])
    return layout(head+body)

@app.route('/commission/<int:id>/<int:montant>')
@admin_required
def commission(id,montant):
    if montant not in [500,1000,1500,2000]: abort(400)
    c=get_db(); c.execute("UPDATE artisans SET dette=dette+?,status='BLOQUE' WHERE id=?",(montant,id)); c.commit(); c.close(); return redirect('/admin')
@app.route('/debloquer/<int:id>')
@admin_required
def debloquer(id):
    c=get_db(); c.execute("UPDATE artisans SET dette=0,status='DISPO',last_pay=? WHERE id=?",(datetime.now().strftime("%d/%m/%Y"),id)); c.commit(); c.close(); return redirect('/admin')
@app.route('/bloquer/<int:id>')
@admin_required
def bloquer(id):
    c=get_db(); c.execute("UPDATE artisans SET dette=dette+1000,status='BLOQUE' WHERE id=?",(id,)); c.commit(); c.close(); return redirect('/admin')
@app.route('/supprimer/<int:id>')
@admin_required
def supprimer(id):
    c=get_db(); c.execute("DELETE FROM artisans WHERE id=?",(id,)); c.commit(); c.close(); return redirect('/admin')

if __name__=='__main__':
    app.run(host='0.0.0.0',port=10000)
