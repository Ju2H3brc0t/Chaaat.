from flask import Flask, request, jsonify
from flask_cors import CORS
from tinydb import TinyDB, Query
import bcrypt
 
# -------------------------------------------------------
# VERSION TEST — sans bot Discord, sans token
# -------------------------------------------------------
 
db = TinyDB('passwords.json')
User = Query()
app = Flask(__name__)
CORS(app)  # ← autorise les requêtes depuis le navigateur
 
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
 
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
 
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({"status": "fail", "message": "Données manquantes"}), 400
 
    guild_id = data.get('guild_id')
    password_tente = data.get('password')
 
    if not guild_id or not password_tente:
        return jsonify({"status": "fail", "message": "guild_id ou password manquant"}), 400
 
    result = db.get(User.guild_id == guild_id)
 
    if result and verify_password(password_tente, result['password']):
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "fail", "message": "Identifiants incorrects"}), 401
 
# ⚠️ À supprimer en production !
@app.route('/dev/setpass', methods=['POST'])
def dev_setpass():
    data = request.json
    guild_id = data.get('guild_id')
    password = data.get('password')
 
    if not guild_id or not password:
        return jsonify({"status": "fail", "message": "Données manquantes"}), 400
 
    hashed = hash_password(password)
    db.upsert({'guild_id': guild_id, 'password': hashed}, User.guild_id == guild_id)
 
    return jsonify({"status": "success", "message": f"Mot de passe défini pour {guild_id}"}), 200
 
if __name__ == '__main__':
    print("✅ Serveur Flask démarré sur http://localhost:5000")
    print("📝 Route de test disponible : POST /dev/setpass")
    app.run(port=5000, debug=True)
 