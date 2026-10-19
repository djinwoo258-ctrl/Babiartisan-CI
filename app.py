from flask import Flask, request, redirect
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB='babiartisan_v9.db'
WAVE="0596003270"
OM="0709996974"

def get_db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    c=get_db()
    c.execute("""CREATE TABLE IF NOT EXISTS artisans(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT, metier TEXT, ville TEXT, tel TEXT, description TEXT,
    dette INTEGER DEFAULT 0, status TEXT DEFAULT 'DISPO', rating REAL DEFAULT 4.9,
    date TEXT, last_pay TEXT)""")
    c.commit(); c.close()
init_db()

def check_abonnement():
    c=get_db(); arts=c.execute("SELECT * FROM artisans").fetchall()
    for a in arts:
        try:
            d=datetime.strptime(a['last_pay'] or a['date'], "%d/%m/%Y")
            if datetime.now() - d > timedelta(days=30):
                if a['status']=='DISPO':
                    c.execute("UPDATE artisans SET dette=dette+1000,status='BLOQUE' WHERE id=?",(a['id'],))
        except: pass
    c.commit(); c.close()

CSS="""
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="logo.png"><link rel="apple-touch-icon" href="logo.png">
<title>BabiArtisan CI</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,sans-serif}
body{background:#f6f8f6}
.hero{position:relative;width:100%;height:380px;overflow:hidden}
.hero img{width:100%;height:100%;object-fit:cover;object-position:top}
.hero .grad{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.1),rgba(0,0,0,.7))}
.hero .txt{position:absolute;bottom:20px;left:16px;right:16px;color:#fff}
.hero .txt h1{font-size:32px;font-weight:900}
.wrap{max-width:720px;margin:0 auto;padding:0 12px 90px}
.card{background:#fff;border-radius:20px;padding:16px;margin:12px 0;box-shadow:0 10px 40px rgba(0,0,0,.07)}
.btn{display:block;width:100%;padding:16px;border-radius:14px;text-align:center;font-weight:900;text-decoration:none;margin:8px 0}
.g{background:linear-gradient(135deg,#00a859,#00d26a);color:#fff}
.o{background:linear-gradient(135deg,#ff8c00,#ffb700);color:#fff}
.b{background:#111;color:#fff}.r{background:#e11d48;color:#fff}
.badge{padding:5px 12px;border-radius:99px;font-size:11px;font-weight:800}
.ok{background:#dcfce7;color:#166534}.ko{background:#fee2e2;color:#991b1b}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
input,select,textarea{width:100%;padding:14px;border-radius:12px;border:1.5px solid #e5e7eb;margin:6px 0;font-size:15px}
.pill{padding:8px 14px;background:#f3f4f6;border-radius:99px;font-size:13px;text-decoration:none;color:#111;font-weight:600;display:inline-block;margin:4px}
.pill.active{background:#111;color:#fff}
</style>
"""

def layout(content):
    check_abonnement()
    hero=f"""<div class='hero'><img src='hero.jpg' onerror="this.src='https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=900'"><div class='grad'></div><div class='txt'><h1>BABIARTISAN CI</h1><p>🇨🇮 Tous les pros: Bâtiment • Moto • Auto • Vélo • Vigile • Nounou</p></div></div>"""
    return f"<html><head>{CSS}</head><body>{hero}<div class='wrap'>{content}<div class='card' style='background:#111;color:#fff;text-align:center'><b>🇨🇮 Fait pour la CI avec ❤️</b><br><small>Wave: {WAVE} | Tous métiers gardés !</small></div></div></body></html>"

@app.route('/')
def home():
    ville=request.args.get('ville','').strip()
    metier=request.args.get('metier','').strip()
    c=get_db(); arts=c.execute("SELECT * FROM artisans ORDER BY id DESC").fetchall()
    if ville: arts=[a for a in arts if ville.lower() in a['ville'].lower()]
    if metier: arts=[a for a in arts if metier.lower() in a['metier'].lower()]
    c.close()
    top=f"""<div class='card' style='text-align:center'><h2>👋 Besoin d'un pro ?</h2><p style='color:#666;font-size:14px'>Du maçon au mécanicien moto, trouve en 2 min</p><form style='display:flex;gap:8px;margin-top:12px'><input name='ville' placeholder='📍 Ville' value='{ville}'><input name='metier' placeholder='🛠️ Métier' value='{metier}'><button class='btn g' style='width:110px'>🔍</button></form><div style='margin-top:12px'><a class='pill' href='/'>Tous</a><a class='pill' href='/?metier=maçon'>🧱 Maçon</a><a class='pill' href='/?metier=carreleur'>🟦 Carreleur</a><a class='pill' href='/?metier=moto'>🏍️ Moto</a><a class='pill' href='/?metier=voiture'>🚗 Auto</a><a class='pill' href='/?metier=vélo'>🚲 Vélo</a></div></div><div class='grid2'><a class='btn g' href='#liste'>🔍 VOIR {len(arts)}</a><a class='btn o' href='/devenir-artisan'>✨ DEVENIR ARTISAN</a></div>"""
    cards="<div id='liste'></div>"
    for a in arts[:100]:
        bloque=(a['dette'] or 0)>0 or a['status']!='DISPO'
        if bloque:
            badge=f"<span class='badge ko'>🔒 {a['dette']}F</span>"
            act=f"<a class='btn r' href='/debloquer/{a['id']}'>💳 PAYER {a['dette']}F</a>"
        else:
            badge=f"<span class='badge ok'>✅ DISPO • {a['rating']}⭐</span>"
            act=f"<a class='btn g' href='https://wa.me/225{a['tel']}?text=Salut {a['nom']} besoin de {a['metier']} via BabiArtisan'>💬 WHATSAPP</a>"
        cards+=f"<div class='card'><div style='display:flex;justify-content:space-between'><b>👷 {a['nom']}</b>{badge}</div><div style='color:#444;font-size:13px'>🛠️ {a['metier']} • 📍 {a['ville']}</div><div style='font-size:13px;color:#666'>{a['description'] or ''}</div><div style='margin-top:10px'>{act}</div></div>"
    return layout(top+cards)

@app.route('/devenir-artisan',methods=['GET','POST'])
def devenir():
    if request.method=='POST':
        c=get_db()
        c.execute("INSERT INTO artisans(nom,metier,ville,tel,description,dette,status,rating,date,last_pay) VALUES(?,?,?,?,?,0,'DISPO',4.9,?,?)",
        (request.form['nom'],request.form['metier'],request.form['ville'],request.form['tel'],request.form['desc'],datetime.now().strftime("%d/%m/%Y"),datetime.now().strftime("%d/%m/%Y")))
        c.commit(); c.close()
        return redirect('/')
    form="""
<div class='card'><h2>📝 Inscription 30 sec - Gratuit</h2>
<p style='color:#666;font-size:13px'>1000F/mois d'abonnement + 1% commission par marché</p>
<form method='post'>
<input name='nom' placeholder='👤 Nom complet' required>
<select name='metier' required>
<option value=''>🛠️ Choisis ton métier</option>
<option>Peintre bâtiment</option>
<option>Menuisier</option>
<option>Maçon</option>
<option>Carreleur / Carreleur</option>
<option>Plombier</option>
<option>Électricien</option>
<option>Soudeur / Ferronnier</option>
<option>Climatisation / Froid</option>
<option>Vigile / Sécurité</option>
<option>Nounou / Baby-sitter</option>
<option>Sage-femme / Infirmière</option>
<option>Mécanicien Moto</option>
<option>Mécanicien Voiture</option>
<option>Mécanicien Vélo</option>
<option>Autre artisan</option>
</select>
<input name='ville' placeholder='📍 Ville + quartier' required>
<input name='tel' placeholder='📱 WhatsApp' required>
<textarea name='desc' placeholder='💼 Décris ton travail...' rows=4 required></textarea>
<button class='btn o'>🚀 JE M'INSCRIS GRATUIT</button>
</form><a class='btn b' href='/'>← Retour</a></div>
"""
    return layout(form)

@app.route('/admin')
def admin():
    c=get_db(); arts=c.execute("SELECT * FROM artisans ORDER BY id DESC").fetchall()
    total=len(arts); dette=sum(a['dette'] or 0 for a in arts); c.close()
    head=f"<div class='card'><h2>🔐 ADMIN - {total} artisans - {dette}F à encaisser</h2></div>"
    body="".join([f"<div class='card'><b>{a['nom']} | {a['metier']} | {a['ville']} | {a['tel']} - Dette {a['dette']}F</b><br><div class='grid3' style='margin-top:8px'><a class='btn' style='background:#f59e0b;color:#fff;padding:8px;font-size:11px' href='/commission/{a['id']}/500'>+500F (50k)</a><a class='btn' style='background:#f59e0b;color:#fff;padding:8px;font-size:11px' href='/commission/{a['id']}/1000'>+1000F (100k)</a><a class='btn' style='background:#f59e0b;color:#fff;padding:8px;font-size:11px' href='/commission/{a['id']}/1500'>+1500F (150k)</a></div><div class='grid3'><a class='btn g' style='padding:8px;font-size:12px' href='/debloquer/{a['id']}'>✅ Débloquer</a><a class='btn b' style='padding:8px;font-size:12px' href='/bloquer/{a['id']}'>❌ Bloquer 1000F</a><a class='btn r' style='padding:8px;font-size:12px' href='/supprimer/{a['id']}'>🗑️ Suppr</a></div></div>" for a in arts])
    return layout(head+body)

@app.route('/commission/<int:id>/<int:montant>')
def commission(id,montant):
    c=get_db(); c.execute("UPDATE artisans SET dette=dette+?,status='BLOQUE' WHERE id=?",(montant,id)); c.commit(); c.close(); return redirect('/admin')
@app.route('/debloquer/<int:id>')
def debloquer(id):
    c=get_db(); c.execute("UPDATE artisans SET dette=0,status='DISPO',last_pay=? WHERE id=?",(datetime.now().strftime("%d/%m/%Y"),id)); c.commit(); c.close(); return redirect('/admin')
@app.route('/bloquer/<int:id>')
def bloquer(id):
    c=get_db(); c.execute("UPDATE artisans SET dette=dette+1000,status='BLOQUE' WHERE id=?",(id,)); c.commit(); c.close(); return redirect('/admin')
@app.route('/supprimer/<int:id>')
def supprimer(id):
    c=get_db(); c.execute("DELETE FROM artisans WHERE id=?",(id,)); c.commit(); c.close(); return redirect('/admin')

if __name__=='__main__':
    app.run(host='0.0.0.0',port=10000)
