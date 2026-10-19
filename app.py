import os
from flask import Flask, request, redirect, url_for, session, render_template

app = Flask(__name__)

# --- CORRECTION ULTIME ANTI-BUG TÉLÉPHONE ---
# Même si ADMIN_PASSWORD est tapé en colonne dans Render, on le nettoie
def clean_env(var_name, default_value):
    raw = os.environ.get(var_name, default_value)
    # On enlève tout : espaces, retours à la ligne, tabulations
    cleaned = raw.replace("\n", "").replace("\r", "").replace(" ", "").replace("\t", "").strip()
    return cleaned

ADMIN_PASSWORD = clean_env("ADMIN_PASSWORD", "Djinwoo258")
SECRET_KEY = clean_env("SECRET_KEY", "babi-artisan-super-secret-2026")

app.secret_key = SECRET_KEY
# --- FIN CORRECTION ---

@app.route('/')
def home():
    return "Babi Artisan CI - Boutique en ligne"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = None
    if request.method == 'POST':
        # On nettoie aussi ce que l'utilisateur tape
        password_tape = request.form.get('password', '').strip().replace(" ", "")
        
        print(f"DEBUG: Mot de passe reçu: '{password_tape}'")
        print(f"DEBUG: Mot de passe attendu: '{ADMIN_PASSWORD}'")
        
        if password_tape == ADMIN_PASSWORD:
            session['admin_logged'] = True
            return redirect(url_for('dashboard'))
        else:
            error = "Mauvais mot de passe !"
    
    # Si tu as un fichier admin.html, il va s'afficher
    try:
        return render_template('admin.html', error=error)
    except:
        # Sinon, version simple sans template
        return f"""
        <h1>Admin Babi Artisan</h1>
        <form method="POST">
            <input type="password" name="password" placeholder="Mot de passe">
            <button type="submit">Connexion</button>
        </form>
        <p style="color:red">{error if error else ''}</p>
        <p>Mot de passe actuel configuré: {len(ADMIN_PASSWORD)} caractères</p>
        """

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin_logged'):
        return redirect(url_for('admin'))
    return "<h1>Bienvenue Djinwoo ! Dashboard OK</h1><a href='/admin/logout'>Déconnexion</a>"

@app.route('/admin/logout')
def logout():
    session.pop('admin_logged', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
