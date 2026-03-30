import discord
from discord.ext import commands
from flask import Flask, request, jsonify
from tinydb import TinyDB, Query
import threading
import bcrypt
 
# Configuration du Bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
 
# Base de données locale pour les mots de passe
db = TinyDB('passwords.json')
User = Query()
 
# --- UTILITAIRES ---
 
def hash_password(password: str) -> str:
    """Hash un mot de passe en clair avec bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')
 
def verify_password(password: str, hashed: str) -> bool:
    """Vérifie qu'un mot de passe correspond au hash stocké."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
 
# --- COMMANDES DISCORD ---
 
@bot.command()
@commands.has_permissions(administrator=True)
async def setpass(ctx, nouveau_mdp: str):
    """Commande pour que l'admin change le mot de passe de son serveur.
    
    Usage : !setpass MonNouveauMotDePasse
    Le mot de passe est hashé avant d'être stocké.
    """
    guild_id = str(ctx.guild.id)
 
    # Supprimer le message de l'admin immédiatement pour ne pas exposer le mdp
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
 
    hashed = hash_password(nouveau_mdp)
    db.upsert({'guild_id': guild_id, 'password': hashed}, User.guild_id == guild_id)
 
    await ctx.author.send(f"✅ Mot de passe mis à jour pour **{ctx.guild.name}** !")
 
@bot.command()
@commands.has_permissions(administrator=True)
async def delpass(ctx):
    """Supprime le mot de passe du serveur.
    
    Usage : !delpass
    """
    guild_id = str(ctx.guild.id)
    removed = db.remove(User.guild_id == guild_id)
 
    if removed:
        await ctx.send("🗑️ Mot de passe supprimé pour ce serveur.")
    else:
        await ctx.send("⚠️ Aucun mot de passe trouvé pour ce serveur.")
 
# --- PARTIE API (Le pont avec le site) ---
 
app = Flask(__name__)
 
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
 
# --- ROUTE DE TEST (à supprimer en production) ---
# Permet de créer un mot de passe de test sans le bot Discord
# Appel : POST http://localhost:5000/dev/setpass
# Body  : {"guild_id": "123456789", "password": "monmotdepasse"}
 
@app.route('/dev/setpass', methods=['POST'])
def dev_setpass():
    """Route de test uniquement — à retirer en production !"""
    data = request.json
    guild_id = data.get('guild_id')
    password = data.get('password')
 
    if not guild_id or not password:
        return jsonify({"status": "fail", "message": "Données manquantes"}), 400
 
    hashed = hash_password(password)
    db.upsert({'guild_id': guild_id, 'password': hashed}, User.guild_id == guild_id)
 
    return jsonify({"status": "success", "message": f"Mot de passe défini pour {guild_id}"}), 200
 
# --- LANCEMENT ---
 
def run_api():
    app.run(port=5000, debug=False)
 
if __name__ == '__main__':
    threading.Thread(target=run_api, daemon=True).start()
    # Commenter la ligne suivante pour tester sans le bot Discord
    bot.run('TON_TOKEN_DISCORD')
 