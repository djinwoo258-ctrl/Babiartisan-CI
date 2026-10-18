from flask import Flask, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = 'batiartisan_v2.db'
WAVE_NUM = "0596003270"
OM_NUM = "0709996974"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS artisans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT, metier TEXT, ville TEXT, tel TEXT, 
        description TEXT, dette INTEGER DEFAULT 0, status TEXT DEFAULT 'DISPO', date TEXT)""")
    conn.commit()
    conn.close()
init_db()

BASE_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta property="og:title" content="BabiArtisan CI - Artisans de CI">
<meta property="og:description" content="Trouve un artisan en 2 min partout en Côte d'Ivoire">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:sans-serif}
body{background:#f1f5f1}
.header{background:linear-gradient(135deg,#00a859,#ff8c00);color:white;padding:18px;text-align:center;font-weight:900}
.card{background:white;margin:10px;border-radius:16px;padding:12px;box-shadow:0 4px 12px rgba(0,0,0,.08)}
.btn{display:block;padding:14px;border-radius:12px;text-align:center;font-weight:800;text-decoration:none;margin:8px 0}
.green{background:#00a859;color:white} .red{background:#e11d48;color:white} .black{background:#111;color:white}
.badge{font-size:11px;padding:2px 7px;border-radius:10px;background:#eee}
</style>
"""

@app.route('/')
def home():
    conn = get_db()
    artisans = conn.execute("SELECT * FROM artisans ORDER BY id DESC").fetchall()
    conn.close()
    html = f"<html><head>{BASE_STYLE}</head><body>"
    html += "<div class='header'>BABIARTISAN CI 🇨🇮<br><span style='font-size:12px;font-weight:400'>Les meilleurs artisans de Côte d'Ivoire</span></div>"
    html += "<div class='card'><h3 style='text-align:center'>Trouve un artisan en 2 min partout en CI</h3>"
    html += "<a class='btn green' href='/artisans'>VOIR LES ARTISANS DE CI</a>"
    html += "<a class='btn' style='border:2px solid #00a859;color:#00a859' href='/devenir-artisan'>DEVENIR ARTISAN (Gratuit)</a>"
    html += "<a class='btn black' href='/admin'>ADMIN - JE VOIS TOUS LES CONTRATS</a></div>"
    for a in artisans:
        dette = a['dette'] if a['dette'] else 0
        status = a['status']
        if status == 'BLOQUE' or dette>0:
            btn = f"<a class='btn red' href='https://wa.me/225{WAVE_NUM}?text=Je veux payer ma dette {dette}F - {a['nom']}'>PAYER {dette}F</a>"
            badge = "<span class='badge' style='background:#fee;color:#e11d48'>BLOQUE</span>"
        else:
            btn = f"<a class='btn green' href='https://wa.me/225{a['tel']}'>Demander et discuter</a>"
            badge = "<span class='badge' style='background:#dcfce7;color:#00a859'>DISPO</span>"
        html += f"<div class='card'><b>{a['nom']} - {a['ville']}</b> - {badge}<br><small>{a['metier']} - Dette {dette}F</small>{btn}</div>"
    html += "</body></html>"
    return html

@app.route('/artisans')
def artisans(): return home()

@app.route('/devenir-artisan', methods=['GET','POST'])
def devenir():
    if request.method == 'POST':
        conn = get_db()
        conn.execute("INSERT INTO artisans (nom,metier,ville,tel,description,dette,status,date) VALUES (?,?,?,?,?,0,'DISPO',?)",
                     (request.form['nom'],request.form['metier'],request.form['ville'],request.form['tel'],request.form['desc'],datetime.now().strftime("%d/%m/%Y")))
        conn.commit(); conn.close()
        return redirect('/')
    return f"<html><head>{BASE_STYLE}</head><body><div class='card'><h2>Devenir Artisan</h2><form method='post'><input name='nom' placeholder='Nom' required style='width:100%;padding:12px;margin:6px 0'><select name='metier' style='width:100%;padding:12px'><option>Peintre</option><option>Menuisier</option><option>Maçon</option><option>Plomberie</option><option>Electricité</option></select><input name='ville' placeholder='Ville' required style='width:100%;padding:12px;margin:6px 0'><input name='tel' placeholder='Tel WhatsApp' required style='width:100%;padding:12px'><textarea name='desc' placeholder='Description' style='width:100%;padding:12px'></textarea><button class='btn green'>S'INSCRIRE</button></form><a href='/'>Retour</a></div></body></html>"

@app.route('/admin')
def admin():
    conn = get_db()
    arts = conn.execute("SELECT * FROM artisans").fetchall()
    conn.close()
    html = f"<html><head>{BASE_STYLE}</head><body><div class='header'>ADMIN BABIARTISAN</div>"
    for a in arts:
        html += f"<div class='card'>{a['nom']} - {a['ville']} - Dette:{a['dette']}F - <a href='/debloquer/{a['id']}'>✅ Débloquer (payer)</a> | <a href='/bloquer/{a['id']}'>❌ Bloquer</a> | <a href='/supprimer/{a['id']}'>🗑️ Supprimer</a></div>"
    html += "<div class='card'><a class='btn black' href='/'>Retour accueil</a></div></body></html>"
    return html

@app.route('/debloquer/<int:id>')
def debloquer(id):
    conn = get_db()
    conn.execute("UPDATE artisans SET status='DISPO', dette=0 WHERE id=?", (id,))
    conn.commit(); conn.close()
    return redirect('/admin')

@app.route('/bloquer/<int:id>')
def bloquer(id):
    conn = get_db()
    conn.execute("UPDATE artisans SET status='BLOQUE', dette=500 WHERE id=?", (id,))
    conn.commit(); conn.close()
    return redirect('/admin')

@app.route('/supprimer/<int:id>')
def supprimer(id):
    conn = get_db()
    conn.execute("DELETE FROM artisans WHERE id=?", (id,))
    conn.commit(); conn.close()
    return redirect('/admin')

if __name__ == '__main__':
    app.run()
