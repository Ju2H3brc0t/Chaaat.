# Chaaat.

A Discord bot originally built for a single server, now capable of running across multiple servers through a per-server configuration system. Hosted and maintained by one person in their free time — feel free to fork or self-host.

---

## Features

### Leveling
Rewards active members with XP for each message sent. Automatically levels up users, assigns level-based roles (stackable or replacing), and announces level-ups in a dedicated channel. Supports boosted and excluded channels. Commands: `/level rank`, `/level leaderboard`.

### Birthdays
Checks daily for members whose birthday matches the current date, sends an announcement, and optionally gifts XP, a role, and a temporary role for the day.

### Counting
Members take turns counting in a dedicated channel. The bot validates the sequence, prevents consecutive messages from the same user, and saves progress. Optionally resets on mistakes.

### Welcome & Goodbye
Sends a message in a configured channel when a member joins or leaves the server.

### Member Role
Automatically assigns one or more roles when a new member joins.

### Bump Reminder
Detects Disboard bump messages and sends a reminder to staff 2 hours later.

### Auto-delete
Automatically deletes messages in specified channels after a configurable delay, to keep them clean.

### Tickets
Creates and manages support tickets in a dedicated category, with optional role mentions.

---

## Configuration

Each server has its own config file at `server_configs/<guild_id>/config.yaml`.

The web dashboard (Flask app on port 5000) provides a visual interface to edit settings after signing in with Discord. Alternatively, use the in-bot slash commands:

- `/config edit` — edit the server configuration
- `/config show` — display the current configuration as an embed

Server-specific data (counting scores, etc.) is stored in `server_configs/<guild_id>/data.json`.  
User-specific data (levels, XP) is stored in a SQLite database at `database.db`.

---

## Localization

The bot sends messages in the language configured per server. If no locale is available for a given language, it falls back to Google Translate — though results may occasionally be inaccurate.

---

## Commands

| Group | Command | Description |
|---|---|---|
| `/level` | `rank` | Show your current level and XP |
| `/level` | `leaderboard` | Show the server leaderboard |
| `/mod` | `timeout` / `kick` / `ban` | Moderation actions with reason and DM notification |
| `/dev` | — | Pull updates from GitHub, reload/load cogs, shut down the bot |
| `/config` | `edit` / `show` | Edit or display the server configuration |

---

## Setup

**Install dependencies**
```bash
pip install -r requirements.txt
```

**Run in background**
```bash
nohup python3 main.py > bot.log 2>&1 &
```

**Update to latest stable version**
```bash
git checkout main
git pull origin main
```

**Launch the web interface**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 website.app:app
```