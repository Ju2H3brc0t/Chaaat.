# 🤖 Chaaat. - Documentation

## 🧩 Presentation

Originally designed for a single specific server, this bot is now capable of being on several different Discord servers thanks to a dedicated configuration system. This bot is hosted and maintained voluntarily by a single person in their free time, however you are free to take over the code or add the bot to your server.

## ⚙️ Features

### 🛠️ Technical features

#### 🔧 Dynamic configuration

 - Each server has a dedicated configuration folder: 
 `server_configs/<guild_id>/config.yaml`

 - The `config.yaml` file contains the configuration of the various features.

 - A slash command (`/set_config`) allows you to modify your server configuration.

 - A command (`/view_config`) allows you to display the current configuration in a readable embed.

#### 💾 Data storage

 - Server-specific data (like score counting) is stored in `server_configs/<guild_id>/data.json`.

 - User-specific data (like current level) is stored in `server_configs/<guild_id>/<user_id>.json`

 - Automatic read/write at each affected event.

---

### 🎮 Practical features

- A counting feature allows members to take turns counting in a specific channel.
    The bot:
    - verifies that the numerical sequence is correct,
    - prevents duplicate messages from the same user,
    - optionally resets the counter on mistakes,
    - saves progress in `data.json`.

- A leveling system reward members for being active.
    The bot:
    - grant experience points for each messages sent,
    - supports boosted and excluded channels,
    - automatically levels up users when enought XP is reached,
    - assigns level-based roles defined in the server configuration,
    - can stack role or replace the previous one,
    - sends a level-up announcement embed in a dedicated channel.

- A feature for automatically adding on or multiple "member" role when a user join the server, based on the server configuration

---

## 💻 Useful bash command

### 🔁 Update the bot to his last stable version

```bash
cd "path/to/bot"
git checkout main
git pull origin main
```

### 🚀 Run the bot in background

```bash
nohup python3 main.py > bot.log 2>&1 &
```

### 📦 Install dependencies

```bash
pip install -r requirements.txt
```

If you have to force the update:

```bash
pip install -U -r requirements.txt
```