from flask import Flask, redirect, request, session, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os
import yaml

load_dotenv()

def get_my_public_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except Exception as e:
        print(f"Erreur lors de la récupération de l'IP : {e}")
        return "127.0.0.1"

PUBLIC_IP = get_my_public_ip()

app = Flask(__name__, static_folder='.')
CORS(app, supports_credentials=True, origins=[f"http://{PUBLIC_IP}:5000"])

app.secret_key = os.getenv("APP_SECRET_KEY")

CLIENT_ID     = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI  = f"http://{PUBLIC_IP}:5000/callback"

DISCORD_API   = "https://discord.com/api/v10"
OAUTH2_URL    = (
    f"https://discord.com/oauth2/authorize"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&response_type=code"
    f"&scope=identify+guilds"
)

BOT_TOKEN   = os.getenv("DISCORD_BOT_TOKEN")

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR  = os.path.dirname(BASE_DIR)                    
CONFIGS_DIR = os.path.join(PARENT_DIR, "server_configs")

DEFAULT_CONFIG = {
    "features": {
        "birthday": {
            "announcement_channel_id": 0,
            "enabled": False,
            "gift": {"enabled": False, "role": [], "temporary_role": [], "xp": 0}
        },
        "bump_reminder": {"channel": 0, "enabled": False},
        "counting": {"channel_id": 0, "checkpoints": False, "enabled": False},
        "goodbye": {"channel_id": 0, "enabled": False},
        "language": "en",
        "leveling": {
            "announcement_channel_id": 0,
            "boost_channels": [],
            "enabled": False,
            "exclude_channels": [],
            "rewards": {"0": 0},
            "rewards_stackable": False
        },
        "member_role": {"enabled": False, "role_id": []},
        "linked_roles": {},
        "message_autodelete": {"channels_id": [], "enabled": False, "wait": 0},
        "welcome": {"channel_id": 0, "enabled": False}
    }
}

def get_config_path(guild_id):
    return os.path.join(CONFIGS_DIR, str(guild_id), "config.yaml")

def load_config(guild_id):
    path = get_config_path(guild_id)
    if not os.path.exists(path):
        return DEFAULT_CONFIG
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or DEFAULT_CONFIG

def stringify_ids(obj):
    """Recursively convert large integers (Discord IDs) to strings to prevent YAML precision loss."""
    if isinstance(obj, dict):
        return {k: stringify_ids(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [stringify_ids(i) for i in obj]
    elif isinstance(obj, int) and obj > 2**32:
        return str(obj)
    return obj

def save_config(guild_id, config):
    path = get_config_path(guild_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(stringify_ids(config), f, allow_unicode=True, default_flow_style=False)

@app.route("/")
def index():
    return redirect("/login.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory('.', filename)

@app.route("/login")
def login():
    return redirect(OAUTH2_URL)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Erreur : code manquant", 400

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
        return f"Erreur token : {token_res.text}", 400

    access_token = token_res.json()["access_token"]

    user = requests.get(f"{DISCORD_API}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}).json()

    guilds = requests.get(f"{DISCORD_API}/users/@me/guilds",
        headers={"Authorization": f"Bearer {access_token}"}).json()

    admin_guilds = [g for g in guilds if (int(g["permissions"]) & 0x8) == 0x8]

    session["user"]   = {"id": user["id"], "username": user["username"], "avatar": user.get("avatar")}
    session["guilds"] = admin_guilds

    return redirect("/servers.html")

@app.route("/api/me")
def me():
    if "user" not in session:
        return jsonify({"error": "Non connecté"}), 401
    return jsonify(session["user"])

@app.route("/api/guilds")
def guilds_route():
    if "guilds" not in session:
        return jsonify({"error": "Non connecté"}), 401
    return jsonify(session["guilds"])

@app.route("/api/logout")
def logout():
    session.clear()
    return jsonify({"status": "ok"})

@app.route("/api/guild/<guild_id>/channels")
def guild_channels(guild_id):
    if "guilds" not in session:
        return jsonify({"error": "Non connecté"}), 401
    if guild_id not in [g["id"] for g in session["guilds"]]:
        return jsonify({"error": "Accès refusé"}), 403

    r = requests.get(f"{DISCORD_API}/guilds/{guild_id}/channels",
        headers={"Authorization": f"Bot {BOT_TOKEN}"})
    if not r.ok:
        return jsonify({"error": "Impossible de récupérer les salons"}), 502

    channels = [
        {"id": c["id"], "name": c["name"], "type": c["type"]}
        for c in r.json()
        if c["type"] in (0, 4, 5, 15)
    ]
    channels.sort(key=lambda c: c["name"].lower())
    return jsonify(channels)

@app.route("/api/guild/<guild_id>/roles")
def guild_roles(guild_id):
    if "guilds" not in session:
        return jsonify({"error": "Non connecté"}), 401
    if guild_id not in [g["id"] for g in session["guilds"]]:
        return jsonify({"error": "Accès refusé"}), 403

    r = requests.get(f"{DISCORD_API}/guilds/{guild_id}/roles",
        headers={"Authorization": f"Bot {BOT_TOKEN}"})
    if not r.ok:
        return jsonify({"error": "Impossible de récupérer les rôles"}), 502

    roles = [
        {"id": ro["id"], "name": ro["name"], "color": ro["color"]}
        for ro in r.json()
        if ro["name"] != "@everyone"
    ]
    roles.sort(key=lambda ro: ro["name"].lower())
    return jsonify(roles)

@app.route("/api/bot-guilds")
def bot_guilds():
    if "guilds" not in session:
        return jsonify({"error": "Non connecté"}), 401

    r = requests.get(f"{DISCORD_API}/users/@me/guilds",
        headers={"Authorization": f"Bot {BOT_TOKEN}"})
    if not r.ok:
        return jsonify([])

    bot_guild_ids = {g["id"] for g in r.json()}
    return jsonify(list(bot_guild_ids))

@app.route("/api/config/<guild_id>", methods=["GET"])
def get_config(guild_id):
    if "guilds" not in session:
        return jsonify({"error": "Non connecté"}), 401

    guild_ids = [g["id"] for g in session["guilds"]]
    if guild_id not in guild_ids:
        return jsonify({"error": "Accès refusé"}), 403

    return jsonify(load_config(guild_id))

@app.route("/api/config/<guild_id>", methods=["POST"])
def post_config(guild_id):
    if "guilds" not in session:
        return jsonify({"error": "Non connecté"}), 401

    guild_ids = [g["id"] for g in session["guilds"]]
    if guild_id not in guild_ids:
        return jsonify({"error": "Accès refusé"}), 403

    if not os.path.exists(get_config_path(guild_id)):
        return jsonify({"error": "Aucune configuration existante pour ce serveur. Le bot doit d'abord rejoindre le serveur."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Données invalides"}), 400

    save_config(guild_id, data)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print(f"✅ Serveur Flask démarré sur http://{PUBLIC_IP}:5000")
    app.run(host="0.0.0.0", port=5000)