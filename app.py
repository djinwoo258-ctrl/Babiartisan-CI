from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime, timedelta

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
    conn.execute("CREATE TABLE IF NOT EXISTS artisans (id INTEGER PRIMARY KEY, nom TEXT, telephone TEXT, metier TEXT, ville TEXT, dette INTEGER DEFAULT 0, last_payment DATE DEFAULT CURRENT_DATE)")
    conn.execute("CREATE TABLE IF NOT EXISTS contrats (id INTEGER PRIMARY KEY, artisan_id INTEGER, client TEXT, montant INTEGER, commission INTEGER DEFAULT 500, statut TEXT DEFAULT 'pending', date DATE DEFAULT CURRENT_DATE)")
    conn.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, contrat_id INTEGER, sender TEXT, message TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c = conn.execute("SELECT COUNT(*) FROM artisans").fetchone()[0]
    if c==0:
        conn.execute("INSERT INTO artisans (nom,telephone,metier,ville,dette) VALUES (?,?,?,?,?)", ("Kone Peintre Pro","0101010101","Peintre","Cocody",500))
        conn.execute("INSERT INTO artisans (nom,telephone,metier,ville,dette) VALUES (?,?,?,?,?)", ("Awa Bouake","0702020202","Potterie","Bouake",0))
        conn.execute("INSERT INTO artisans (nom,telephone,metier,ville,dette) VALUES (?,?,?,?,?)", ("Koffi Korhogo","0503030303","Menuisier","Korhogo",0))
        conn.execute("INSERT INTO artisans (nom,telephone,metier,ville,dette) VALUES (?,?,?,?,?)", ("Fatou San Pedro","0404040404","Macon","San Pedro",0))
    conn.commit()
    conn.close()
init_db()

BASE_HEAD = "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap' rel='stylesheet'><style>*{font-family:Poppins,sans-serif;margin:0;box-sizing:border-box}body{background:#f4f6f8}.header{background:linear-gradient(135deg,#FF8C00,#008751);color:white;padding:18px;text-align:center;position:sticky;top:0;z-index:10}.card{background:white;border-radius:16px;padding:16px;margin:12px;box-shadow:0 4px 12px rgba(0,0,0,0.08)}.btn{padding:14px 20px;border-radius:12px;text-decoration:none;display:block;text-align:center;font-weight:700;margin:8px 0}.btn-green{background:#008751;color:white}.btn-red{background:#E30613;color:white}.btn-wave{background:#1DC4FF;color:white}.btn-om{background:#FF7900;color:white}.price{font-size:24px;font-weight:800;color:#FF8C00}.chat-box{height:300px;overflow-y:auto;background:#f0f2f5;border-radius:12px;padding:10px;margin:10px 0}.msg{padding:8px 12px;border-radius:12px;margin:6px 0;max-width:80%}.msg-client{background:#DCF8C6;margin-left:auto}.msg-artisan{background:white}.msg-admin{background:#FFE082;border-left:4px solid #FF8C00}</style>"

@app.route('/')
def index():
    html = BASE_HEAD + "<div class=header><h1>BABIARTISAN CI</h1><p>Les meilleurs artisans de Cote d'Ivoire<br>Bouake, Korhogo, San Pedro, Yamoussoukro, Abidjan...</p></div><div class=card style='text-align:center'><h2>Trouve un artisan en 2 min partout en CI</h2><a href='/artisans' class='btn btn-green'>VOIR LES ARTISANS DE CI</a><a href='/register' class='btn' style='background:white;border:2px solid #008751;color:#008751'>DEVENIR ARTISAN (Gratuit)</a><a href='/admin' class='btn' style='background:#222;color:white'>ADMIN - JE VOIS TOUS LES CONTRATS</a></div><div class=card><h3>Ton Business - Toute la CI</h3><p>1. Client demande artisan<br>2. Ils discutent DANS ton appli (tu vois tout)<br>3. Chantier fini = tu prends 500F + 1000F/mois<br><b>= 1000 artisans = 500 000F/jour !</b></p></div>"
    return html

@app.route('/artisans')
def artisans():
    conn = get_db()
    arts = conn.execute("SELECT * FROM artisans").fetchall()
    conn.close()
    html = BASE_HEAD + "<div class=header><h2>Artisans de toute la CI</h2><a href='/' style='color:white'>Accueil</a></div>"
    for a in arts:
        status = "BLOQUE" if a['dette']>0 else "DISPO"
        btn = f"<a href='/bloque/{a['id']}' class='btn btn-red'>PAYER {a['dette']}F</a>" if a['dette']>0 else f"<a href='/demander/{a['id']}' class='btn btn-green'>Demander et discuter</a>"
        html += f"<div class=card><b>{a['nom']} - {a['ville']}</b> - {status}<br>{a['metier']} - Dette {a['dette']}F<br>{btn}</div>"
    return html

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        conn = get_db()
        conn.execute("INSERT INTO artisans (nom,telephone,metier,ville) VALUES (?,?,?,?)",(request.form['nom'],request.form['tel'],request.form['metier'],request.form['ville']))
        conn.commit(); conn.close()
        return redirect('/artisans')
    return BASE_HEAD + "<div class=header><h2>Devenir Artisan - Toute CI</h2></div><form method=post class=card>Nom: <input name=nom required style='width:100%;padding:12px;margin:6px 0'><br>Tel: <input name=tel required style='width:100%;padding:12px;margin:6px 0'><br>Metier: <select name=metier style='width:100%;padding:12px'><option>Peintre</option><option>Menuisier</option><option>Plombier</option></select><br>Ville: <select name=ville style='width:100%;padding:12px'><option>Abidjan-Cocody</option><option>Bouake</option><option>Korhogo</option><option>Yamoussoukro</option><option>San Pedro</option><option>Daloa</option><option>Man</option><option>Abengourou</option></select><br><button class='btn btn-green' style='width:100%'>S'inscrire</button></form>"

@app.route('/demander/<int:id>', methods=['GET','POST'])
def demander(id):
    if request.method=='POST':
        conn = get_db()
        a = conn.execute("SELECT * FROM artisans WHERE id=?",(id,)).fetchone()
        if a['dette']>0:
            conn.close()
            return redirect(f'/bloque/{id}')
        conn.execute("INSERT INTO contrats (artisan_id,client,montant) VALUES (?,?,?)",(id, request.form['client'], int(request.form['montant'])))
        conn.commit()
        cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO messages (contrat_id,sender,message) VALUES (?,?,?)",(cid, "client", request.form.get('msg','Bonjour')))
        conn.commit(); conn.close()
        return redirect(f'/chat/{cid}')
    return BASE_HEAD + "<div class=header><h2>Demander</h2></div><form method=post class=card>Ton nom: <input name=client value='Nawa' style='width:100%;padding:12px'><br>Budget: <input name=montant value='60000' type=number style='width:100%;padding:12px'><br>Message: <textarea name=msg style='width:100%;padding:12px'>Salut, dispo demain a Cocody ?</textarea><br><button class='btn btn-green' style='width:100%'>Envoyer et discuter dans l'appli</button></form>"

@app.route('/chat/<int:cid>', methods=['GET','POST'])
def chat(cid):
    conn = get_db()
    if request.method=='POST':
        conn.execute("INSERT INTO messages (contrat_id,sender,message) VALUES (?,?,?)",(cid, request.form['sender'], request.form['message']))
        conn.commit()
    c = conn.execute("SELECT contrats.*, artisans.nom as anom, artisans.ville FROM contrats JOIN artisans ON artisans.id=contrats.artisan_id WHERE contrats.id=?",(cid,)).fetchone()
    msgs = conn.execute("SELECT * FROM messages WHERE contrat_id=? ORDER BY date ASC",(cid,)).fetchall()
    conn.close()
    if not c: return "Contrat introuvable"
    html_msgs = ""
    for m in msgs:
        cls = "msg-client" if m['sender']=='client' else "msg-artisan" if m['sender']=='artisan' else "msg-admin"
        html_msgs += f"<div class='msg {cls}'><b>{m['sender']}:</b> {m['message']}</div>"
    return BASE_HEAD + f"<div class=header><h3>Chat #{c['id']} - {c['anom']} ({c['ville']}) - {c['montant']}F - {c['statut']}</h3><a href='/admin' style='color:white'>ADMIN</a></div><div class=card><div class=chat-box>{html_msgs}</div><form method=post style='display:flex;gap:6px'><select name=sender style='padding:8px'><option value='client'>Client</option><option value='artisan'>Artisan</option></select><input name=message required placeholder='Message...' style='flex:1;padding:8px;border-radius:20px'><button class='btn btn-green' style='margin:0;padding:8px 12px'>Env</button></form><div style='display:flex;gap:6px;margin-top:10px'><a href='/accepter/{c['id']}' class='btn btn-green' style='flex:1'>ACCEPTER</a><a href='/fini/{c['id']}' class='btn' style='flex:1;background:orange;color:white'>FINI +500F</a></div></div>"

@app.route('/admin')
def admin():
    conn = get_db()
    arts = conn.execute("SELECT * FROM artisans").fetchall()
    for a in arts:
        try: last = datetime.strptime(a['last_payment'], '%Y-%m-%d')
        except: last = datetime.now()-timedelta(days=40)
        if (datetime.now()-last).days>=30:
            conn.execute("UPDATE artisans SET dette=dette+1000, last_payment=? WHERE id=?", (datetime.now().strftime('%Y-%m-%d'), a['id']))
    conn.commit()
    contrats = conn.execute("SELECT contrats.*, artisans.nom, artisans.ville FROM contrats JOIN artisans ON artisans.id=contrats.artisan_id ORDER BY contrats.id DESC").fetchall()
    artisans = conn.execute("SELECT * FROM artisans").fetchall()
    msgs_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    conn.close()
    html = BASE_HEAD + "<div class=header><h2>ADMIN - TU VOIS TOUT</h2><a href='/' style='color:white'>Accueil</a></div>"
    total = sum([a['dette'] for a in artisans])
    html += f"<div class=card style='background:linear-gradient(135deg,#008751,#FF8C00);color:white'><h3>Total a encaisser - Toute CI</h3><p style='font-size:32px'>{total}F</p><p>Wave: {WAVE_NUM} | OM: {OM_NUM}</p><p>{msgs_count} messages - Tu surveilles tout</p></div>"
    html += "<div class=card><h3>Contrats - Discussions</h3>"
    for c in contrats:
        html += f"<div style='border:1px solid #eee;padding:8px;margin:6px 0;border-radius:10px'><b>#{c['id']} {c['nom']} ({c['ville']})</b> - {c['montant']}F - {c['statut']}<br><a href='/chat/{c['id']}' class='btn btn-green' style='padding:6px'>VOIR DISCUSSION</a></div>"
    html += "</div><div class=card><h3>Artisans Dettes</h3>"
    for a in artisans:
        html += f"<div style='padding:6px 0;border-bottom:1px solid #eee'>{a['nom']} ({a['ville']}) - <b style='color:red'>{a['dette']}F</b> <a href='/bloque/{a['id']}'>Voir</a> | <a href='/payer/{a['id']}/admin'>Paye</a></div>"
    html += "</div>"
    return html

@app.route('/accepter/<int:cid>')
def accepter(cid):
    conn = get_db(); conn.execute("UPDATE contrats SET statut='accepted' WHERE id=?",(cid,)); conn.execute("INSERT INTO messages (contrat_id,sender,message) VALUES (?,?,?)",(cid,"admin","Contrat accepte par ADMIN")); conn.commit(); conn.close(); return redirect(f'/chat/{cid}')

@app.route('/fini/<int:cid>')
def fini(cid):
    conn = get_db(); c = conn.execute("SELECT * FROM contrats WHERE id=?",(cid,)).fetchone()
    if c: conn.execute("UPDATE contrats SET statut='fini' WHERE id=?",(cid,)); conn.execute("UPDATE artisans SET dette=dette+? WHERE id=?",(c['commission'], c['artisan_id'])); conn.execute("INSERT INTO messages (contrat_id,sender,message) VALUES (?,?,?)",(cid,"admin",f"Chantier fini ! +{c['commission']}F")); conn.commit()
    conn.close(); return redirect('/admin')

@app.route('/bloque/<int:aid>')
def bloque(aid):
    conn = get_db(); a = conn.execute("SELECT * FROM artisans WHERE id=?",(aid,)).fetchone(); conn.close()
    return BASE_HEAD + f"<div style='background:#E30613;color:white;padding:16px;text-align:center'><h2>COMPTE BLOQUE - {a['ville']}</h2></div><div class=card style='text-align:center;border:2px solid #E30613'><h3>{a['nom']}</h3><p>Dette: {a['dette']} FCFA</p></div><div class=card><div style='background:#E6F6FF;padding:12px;border-radius:10px;border-left:4px solid #1DC4FF'><b>Wave</b><br>{a['dette']}F au <b>{WAVE_NUM}</b></div><div style='background:#FFF3E6;padding:12px;border-radius:10px;border-left:4px solid #FF7900;margin-top:8px'><b>OM</b><br>{a['dette']}F au <b>{OM_NUM}</b></div><a href='/payer/{a['id']}/wave' class='btn btn-wave'>J AI PAYE WAVE</a><a href='/payer/{a['id']}/om' class='btn btn-om'>J AI PAYE OM</a></div>"

@app.route('/payer/<int:aid>/<type_pay>')
def payer(aid, type_pay):
    conn = get_db(); a = conn.execute("SELECT * FROM artisans WHERE id=?",(aid,)).fetchone()
    dette = a['dette'] if a else 0
    conn.execute("UPDATE artisans SET dette=0, last_payment=? WHERE id=?", (datetime.now().strftime('%Y-%m-%d'), aid)); conn.commit(); conn.close()
    return BASE_HEAD + f"<div style='padding:40px 20px;text-align:center;background:white;min-height:100vh'><div style='font-size:80px'>OK</div><h1 style='color:#008751'>PAIEMENT RECU !</h1><p>{a['nom']} de {a['ville']} a paye {dette}F via {type_pay.upper()}<br>Wave {WAVE_NUM} / OM {OM_NUM}</p><div class=card style='background:#D4EDDA'>SMS: Merci {a['nom']} ! Paiement {dette}F recu. Compte DEBLOQUE pour toute la CI. Prochain 1000F fin du mois.</div><a href='/artisans' class='btn btn-green'>RETOUR DEBLOQUE</a></div>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
