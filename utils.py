from deep_translator import GoogleTranslator
import aiosqlite
import yaml
import json
import os

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
    required_columns = {
        "warn": "INTEGER DEFAULT 0",
        "timeout_count": "INTEGER DEFAULT 0",
        "note": "TEXT",
        "xp": "INTEGER DEFAULT 0",
        "level": "INTEGER DEFAULT 0",
        "birthday": "TEXT",
        "previous_temporary_gift": "INTEGER",
    }

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                user_id INTEGER,
                guild_id INTEGER,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
    
        async with db.execute("PRAGMA table_info(user_data)") as cursor:
            existing_columns = [row[1] for row in await cursor.fetchall()]

        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                try:
                    await db.execute(f"ALTER TABLE user_data ADD COLUMN {column_name} {column_type}")
                except Exception as e:
                    print(f"⚠️ Failed to load database: {e}")
                    return

            await db.commit()
    
        protected_columns = ["user_id", "guild_id"]
        for column in existing_columns:
            if column not in required_columns and column not in protected_columns:
                try:
                    await db.execute(f"ALTER TABLE user_data DROP COLUMN {column}")
                except Exception as e:
                    print(f"⚠️ Failed to load database: {e}")
                    return
    
        print("📦 Database charged successfully")

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

def load_locale(language: str):
    path = f'locales/{language}.json'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

async def translate(text: str, dest_lng: str, **kwargs):
    if dest_lng == "en":
        return text.format(**kwargs) if kwargs else text

    locale = load_locale(language=dest_lng)
    template = locale.get(text, None)

    if template:
        return template.format(**kwargs) if kwargs else template
    
    result = GoogleTranslator(source='en', target=dest_lng).translate(text=text)
    return result