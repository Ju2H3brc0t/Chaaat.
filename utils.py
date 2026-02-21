from googletrans import Translator
import aiosqlite
import yaml
import json
import os

translator = Translator()

DB_PATH = "database.db"

DEFAULT_CONFIG = {
    'features': {
        'counting': {
            'channel_id': 0,
            'enabled': False,
            'reset_if_wrong_user': False
        },
        'language': 'en',
        'member_role': {
            'enabled': False,
            'role_id': [0]
        },
        'leveling': {
            'enabled': False,
            'exclude_channels': [0],
            'boost_channels': [0],
            'default_level': 0,
            'rewards': {'0': 0, '1': 1},
            'rewards_stackable': False,
            'announcement': {
                'enabled': False,
                'channel_id': 0
            }
        },
        'welcome': {
            'enabled': False,
            'channel_id': 0
        },
        'goodbye': {
            'enabled': False,
            'channel_id': 0
        },
        'birthday': {
            'enabled': False,
            'announcement_channel_id': 0,
            'gift': {
                'enabled': False,
                'role': [0],
                'temporary_role': [0],
                'xp': 0
            }
        }
    }
}

DEFAULT_JSON = {
    'counting': 0,
    'last_user_id': 0
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
        return yaml.safe_load

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
        return json.load

async def translate(text: str, dest_lng: str):
    if dest_lng != "en":
        result = translator.translate(text, src='en', dest=dest_lng)
    else:
        result = text
    
    return result