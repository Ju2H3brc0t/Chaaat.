from googletrans import Translator
import aiosqlite
import yaml
import json
import os

translator = Translator()

DB_PATH = "database.db"

DEFAULT_CONFIG = {
    "features": {
        "birthday": {
            "announcement_channel_id": 0,
            "enabled": False,
            "gift": {
                "enabled": False,
                "role": [],
                "temporary_role": [],
                "xp": 0
            }
        },
        "bump_reminder": {
            "channel": 0,
            "enabled": False
        },
        "counting": {
            "channel_id": 0,
            "checkpoints": False,
            "enabled": False
        },
        "goodbye": {
            "channel_id": 0,
            "enabled": False
        },
        "language": "en",
        "leveling": {
            "announcement_channel_id": 0,
            "boost_channels": [],
            "enabled": True,
            "exclude_channels": [],
            "rewards": {
                "0": 0
            },
            "rewards_stackable": False
        },
        "member_role": {
            "enabled": False,
            "role_id": []
        },
        "message_autodelete": {
            "channels_id": [],
            "enabled": False,
            "wait": 0
        },
        "welcome": {
            "channel_id": 0,
            "enabled": False
        }
    }
}

DEFAULT_JSON = {
    "counting": 0,
    "last_user_id": 0,
    "next_bump": "Anytime"
}

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                user_id INTEGER,
                guild_id INTEGER,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                birthday TEXT,
                previous_temporary_gift INTEGER,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')

        await db.commit()

async def add_users_to_db(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO user_data (user_id, guild_id) VALUES (?, ?)",
            (user_id, guild_id)
        )
        await db.commit()

async def update_db(column: str, value, user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await add_users_to_db(user_id=user_id, guild_id=guild_id)

        query = f"UPDATE user_data SET {column} = ? WHERE user_id = ? AND guild_id = ?"
        await db.execute(query, (value, user_id, guild_id))

        await db.commit()

async def get_user_from_db(data_to_get: str, user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            f"SELECT {data_to_get} FROM user_data WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        ) as cursor:
            row = await cursor.fetchone()

    if row:
        return row[0]
    else:
        await add_users_to_db(user_id=user_id, guild_id=guild_id)
        return await get_user_from_db(data_to_get=data_to_get, user_id=user_id, guild_id=guild_id)

async def remove_guild_from_db(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM user_data WHERE guild_id = ?", (guild_id,))

        await db.commit()

async def remove_user_from_db(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM user_data WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))

        await db.commit()

async def load_config(guild_id: int, auto_create: bool = True):
    path = f'server_configs/{guild_id}'
    file_path = f'{path}/config.yaml'

    if not os.path.exists(file_path):
        if auto_create:
            os.makedirs(path, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(DEFAULT_CONFIG, f, allow_unicode=True)
            return DEFAULT_CONFIG
        else:
            return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

async def load_data(guild_id: int, auto_create: bool = True):
    path = f'server_configs/{guild_id}'
    file_path = f'{path}/data.json'

    if not os.path.exists(file_path):
        if auto_create:
            os.makedirs(path, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_JSON, f, allow_unicode=True)
            return DEFAULT_JSON
        else:
            return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

async def translate(text: str, dest_lng: str):
    if dest_lng != "en":
        result = translator.translate(text, src='en', dest=dest_lng)
        return result.text
    else:
        result = text
        return result