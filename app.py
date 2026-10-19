from flask import Flask, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = 'babiartisan_v3.db'
WAVE = "0596003270"
OM = "0709996974"

def get_db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = get_db()
    c.execute("""CREATE TABLE IF NOT EXISTS artisans(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT, metier TEXT, ville TEXT, tel TEXT, description TEXT,
    dette INTEGER DEFAULT 0, status TEXT DEFAULT 'DISPO', rating REAL DEFAULT 4.9, date TEXT)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ville ON artisans(ville)")
    c.commit(); c.close()
init_db()

CSS = """
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BabiArtisan CI - Artisans de confiance CI</title>
<meta name="theme-color" content="#00a859">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}
body{background:#f6f8f6;color:#111}
.top{background:linear-gradient(135deg,#00a859 0%,#ff8c00 100%);color:#fff;padding:28px 18px;text-align:center}
.top h1{font-size:26px;letter-spacing:1px}
.top p{opacity:.95;margin-top:6px;font-size:14px}
.wrap{max-width:700px;margin:0 auto;padding:0 12px 80px}
.card{background:#fff;border-radius:22px;padding:16px;margin:12px 0;box-shadow:0 8px 30px rgba(0,0,0,.06);border:1px solid #eef2ee}
.btn{display:block;width:100%;padding:16px;border-radius:14px;text-align:center;font-weight:900;text-decoration:none;margin:8px 0;border:none;cursor:pointer}
.g{background:linear-gradient(135deg,#00a859,#00d26a);color:#fff}
.o{background:linear-gradient(135deg,#ff8c00,#ffb700);color:#fff}
.b{background:#111;color:#fff}
.badge{padding:5px 12px;border-radius:99px;font-size:11px;font-weight:800}
.ok{background:#dcfce7;color:#166534}.ko{background:#fee2e2;color:#991b1b}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
input,select,textarea{width:100%;padding:14px;border-radius:12px;border:1.5px solid #e5e7eb;margin:6px 0;font-size:14px}
.stats{display:flex;justify-content:space-around;margin:12px 0;text-align:center}
.stats b{font-size:22px;color:#00a859;display:block}
.pulse{animation:pulse 2s infinite}
@keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.02)}100%{transform:scale(1)}}
</style>
"""

def layout(content):
    return f"<html><head>{CSS}</head><body><div class='top'><div style='font-size:44px'>🔨🇨🇮</div><h1>BABIARTISAN CI</h1><p>La plateforme N°1 des artisans de confiance en Côte d'Ivoire</p></div><div class='wrap'>{content}<div class='card' style='background:#111;color:#fff;text-align:center'><b>🇨🇮 Fait pour la CI avec ❤️</b><br><small>Wave: {WAVE} | OM: {OM} | Support 24h/24</small><br><small>500+ artisans déjà inscrits • Paiement sécurisé</small></div></div></body></html>"

@app.route('/')
def home():
    ville = request.args.get('ville','').strip()
    metier = request.args.get('metier','').strip()
    c=get_db()
    q="SELECT * FROM artisans WHERE status='DISPO' OR dette=0"
    arts=c.execute("SELECT * FROM artisans ORDER BY id DESC").fetchall()
    if ville: arts=[a for a in arts if ville.lower() in a['ville'].lower()]
    if metier: arts=[a for a in arts if metier.lower() in a['metier'].lower()]
    total=len(arts)
    c.close()
    
    hero = f"""<div class='card' style='text-align:center'>
    <h2>👋 Tu cherches un bon artisan ?</h2><p style='color:#666;font-size:14px;margin:8px 0'>Trouve un pro vérifié près de toi en 2 minutes. Négocie direct sur WhatsApp !</p>
    <div class='stats'><div><b>500+</b><small>Artisans vérifiés</small></div><div><b>24h</b><small>Intervention rapide</small></div><div><b>4.9⭐</b><small>Clients satisfaits</small></div></div>
    <form style='display:flex;gap:8px;margin-top:10px'><input name='ville' placeholder='📍 Ville (ex: Yopougon)' value='{ville}'><input name='metier' placeholder='🛠️ Métier' value='{metier}'><button class='btn g' style='width:120px'>🔍 Chercher</button></form>
    </div>
    <div class='grid2'><a class='btn g pulse' href='/artisans'>🔍 VOIR ARTISANS ({total})</a><a class='btn o pulse' href='/devenir-artisan'>✨ DEVENIR ARTISAN GRATUIT</a></div>
    <div class='card'><b>🔥 Les plus demandés:</b><div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:6px'>
    <a class='badge ok' href='/?metier=peintre'>🎨 Peintre</a><a class='badge ok' href='/?metier=menuisier'>🪚 Menuisier</a><a class='badge ok' href='/?metier=macon'>🧱 Maçon</a><a class='badge ok' href='/?metier=plom'>🔧 Plombier</a><a class='badge ok' href='/?metier=elect'>💡 Electricien</a></div></div>"""
    
    cards=""
    for a in arts[:50]:
        dette=a['dette'] or 0
        bloque = dette>0 or a['status']!='DISPO'
        if bloque:
            badge="<span class='badge ko'>🔒 BLOQUÉ - 500F à payer</span>"
            action=f"<a class='btn' style='background:#e11d48;color:white' href='/debloquer/{a['id']}'>💳 PAYER {dette or 500}F VIA WAVE/OM POUR DÉBLOQUER</a><small style='color:#666'>Le client peut toujours te voir mais doit payer pour être contacté</small>"
        else:
            badge=f"<span class='badge ok'>✅ DISPO • {a['rating']}⭐</span>"
            action=f"<a class='btn g' href='https://wa.me/225{a['tel']}?text=Salut {a['nom']} je viens de BabiArtisan CI, j ai besoin de {a['metier']} a {a['ville']}'>💬 NÉGOCIER SUR WHATSAPP - {a['nom']}</a><div style='display:flex;gap:8px;margin-top:6px'><a class='btn b' style='flex:1;padding:10px;font-size:12px' href='tel:{a['tel']}'>📞 Appeler</a><a class='btn' style='flex:1;background:#eef;padding:10px;font-size:12px' href='/?ville={a['ville']}'>📍 Voir à {a['ville']}</a></div>"
        cards+=f"<div class='card'><div style='display:flex;justify-content:space-between;align-items:center'><b>👷 {a['nom']}</b>{badge}</div><div style='color:#666;font-size:13px;margin:6px 0'>🛠️ {a['metier']} • 📍 {a['ville']} • 📅 {a['date']}</div><div style='font-size:13px;margin:6px 0'>{a['description'] or ''}</div>{action}</div>"
    
    if not arts:
        cards="<div class='card' style='text-align:center'><h3>🚀 Sois le premier artisan de ta ville !</h3><p style='color:#666'>Les clients cherchent déjà, inscris-toi gratuitement</p><a class='btn o' href='/devenir-artisan'>✨ JE M'INSCRIS MAINTENANT - GRATUIT</a></div>"
    
    return layout(hero+cards)

@app.route('/artisans')
def list_art(): return home()

@app.route('/devenir-artisan', methods=['GET','POST'])
def devenir():
    if request.method=='POST':
        c=get_db()
        c.execute("INSERT INTO artisans(nom,metier,ville,tel,description,dette,status,rating,date) VALUES(?,?,?,?,?,0,'DISPO',4.9,?)",
        (request.form['nom'],request.form['metier'],request.form['ville'],request.form['tel'],request.form['desc'],datetime.now().strftime("%d/%m/%Y %H:%M")))
        c.commit(); c.close()
        return redirect('/?ok=1')
    form=f"""<div class='card' style='text-align:center;background:linear-gradient(135deg,#00a859,#00d26a);color:white'><h2>🎉 Rejoins 500+ artisans qui gagnent +3 clients / semaine</h2><p>Inscription 100% gratuite • Pas de commission au début • Clients garantis</p></div>
    <div class='card'><h3>📝 Inscription en 30 secondes</h3>
    <form method='post'><input name='nom' placeholder='👤 Nom complet (ex: Kone Ibrahim)' required><select name='metier' required><option value=''>🛠️ Choisis ton métier</option><option>🎨 Peintre bâtiment</option><option>🪚 Menuisier bois/alu</option><option>🧱 Maçon / carreleur</option><option>🔧 Plombier</option><option>💡 Électricien</option><option>❄️ Froid / Climatisation</option><option>🔩 Soudeur</option><option>🪞 Vitrier</option></select><input name='ville' placeholder='📍 Ville + quartier (ex: Abidjan Yopougon)' required><input name='tel' placeholder='📱 Numéro WhatsApp (ex: 07...)' required><textarea name='desc' placeholder='💼 Décris ton travail, tes prix, ton expérience... Ex: Je fais peinture, enduit, déco depuis 5 ans, prix à partir de 2000F/m2' rows=4></textarea>
    <button class='btn o pulse'>🚀 JE DEVIENS ARTISAN - C'EST GRATUIT</button><small style='color:#666'>En t'inscrivant tu acceptes de payer 500F par mois pour rester visible (après 7 jours gratuits)</small></form>
    <div class='grid2' style='margin-top:12px'><div class='card' style='background:#f0fdf4;text-align:center'><b>💰</b><br><small>Gagne 50k-200k / mois en plus</small></div><div class='card' style='background:#fff7ed;text-align:center'><b>🤝</b><br><small>Négocie direct avec client</small></div></div>
    <a class='btn b' href='/'>← Retour accueil</a></div>"""
    return layout(form)

@app.route('/admin')
def admin():
    c=get_db()
    arts=c.execute("SELECT * FROM artisans ORDER BY id DESC").fetchall()
    total=len(arts)
    dette=sum(a['dette'] or 0 for a in arts)
    bloques=len([a for a in arts if a['dette']>0])
    c.close()
    head=f"""<div class='card'><h2>🔐 ADMIN - Tous les contrats</h2><div class='stats'><div><b>{total}</b><small>Artisans</small></div><div><b>{dette}F</b><small>Dettes</small></div><div><b>{bloques}</b><small>Bloqués</small></div></div></div>"""
    body=""
    for a in arts:
        body+=f"<div class='card'><b>{a['nom']} - {a['ville']} - {a['metier']} - {a['tel']}</b><br><small>Dette: {a['dette']}F | Status: {a['status']} | {a['date']}</small><br><div style='display:flex;gap:6px;margin-top:8px'><a class='btn g' style='padding:8px;font-size:12px' href='/debloquer/{a['id']}'>✅ Débloquer</a><a class='btn' style='padding:8px;font-size:12px;background:#f59e0b;color:white' href='/bloquer/{a['id']}'>❌ Bloquer 500F</a><a class='btn' style='padding:8px;font-size:12px;background:#e11d48;color:white' href='/supprimer/{a['id']}'>🗑️ Suppr</a></div></div>"
    return layout(head+body+"<a class='btn b' href='/'>Retour</a>")

@app.route('/debloquer/<int:id>')
def debloquer(id):
    c=get_db(); c.execute("UPDATE artisans SET dette=0,status='DISPO' WHERE id=?", (id,)); c.commit(); c.close(); return redirect('/admin')
@app.route('/bloquer/<int:id>')
def bloquer(id):
    c=get_db(); c.execute("UPDATE artisans SET dette=500,status='BLOQUE' WHERE id=?", (id,)); c.commit(); c.close(); return redirect('/admin')
@app.route('/supprimer/<int:id>')
def supprimer(id):
    c=get_db(); c.execute("DELETE FROM artisans WHERE id=?", (id,)); c.commit(); c.close(); return redirect('/admin')

if __name__=='__main__':
    app.run(host='0.0.0.0', port=10000)
