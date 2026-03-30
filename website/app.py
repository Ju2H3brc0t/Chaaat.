from flask import Flask, redirect, request, session, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24)  # Change par une vraie clé secrète en production

# -------------------------------------------------------
# ⚙️ Configuration — remplace par tes vraies valeurs
# -------------------------------------------------------
CLIENT_ID     = "TON_CLIENT_ID"
CLIENT_SECRET = "TON_CLIENT_SECRET"
REDIRECT_URI  = "http://localhost:5000/callback"

DISCORD_API   = "https://discord.com/api/v10"
OAUTH2_URL    = (
    f"https://discord.com/oauth2/authorize"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&response_type=code"
    f"&scope=identify+guilds"
)

# -------------------------------------------------------
# Routes OAuth2
# -------------------------------------------------------

@app.route("/login")
def login():
    """Redirige l'utilisateur vers Discord pour s'authentifier."""
    return redirect(OAUTH2_URL)


@app.route("/callback")
def callback():
    """Discord redirige ici après connexion avec un code."""
    code = request.args.get("code")
    if not code:
        return "Erreur : code manquant", 400

    # Échange le code contre un access_token
    token_res = requests.post(
        f"{DISCORD_API}/oauth2/token",
        data={
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if not token_res.ok:
        return f"Erreur lors de l'échange du token : {token_res.text}", 400

    token_data = token_res.json()
    access_token = token_data["access_token"]

    # Récupère le profil Discord de l'utilisateur
    user_res = requests.get(
        f"{DISCORD_API}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    user = user_res.json()

    # Récupère les serveurs de l'utilisateur
    guilds_res = requests.get(
        f"{DISCORD_API}/users/@me/guilds",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    guilds = guilds_res.json()

    # Filtre : uniquement les serveurs où l'utilisateur est admin (permission 0x8)
    admin_guilds = [
        g for g in guilds
        if (int(g["permissions"]) & 0x8) == 0x8
    ]

    # Stocke dans la session
    session["user"]   = {"id": user["id"], "username": user["username"], "avatar": user.get("avatar")}
    session["guilds"] = admin_guilds

    return redirect("http://localhost/servers.html")


@app.route("/api/me")
def me():
    """Retourne le profil de l'utilisateur connecté."""
    if "user" not in session:
        return jsonify({"error": "Non connecté"}), 401
    return jsonify(session["user"])


@app.route("/api/guilds")
def guilds():
    """Retourne les serveurs où l'utilisateur est admin."""
    if "guilds" not in session:
        return jsonify({"error": "Non connecté"}), 401
    return jsonify(session["guilds"])


@app.route("/api/logout")
def logout():
    """Déconnecte l'utilisateur."""
    session.clear()
    return jsonify({"status": "ok"})


# -------------------------------------------------------
# Lancement
# -------------------------------------------------------
if __name__ == "__main__":
    print("✅ Serveur Flask démarré sur http://localhost:5000")
    app.run(port=5000, debug=True)
