from googletrans import Translator
import yaml
import os

translator = Translator()

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
            'rewards': {'0': 0},
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

async def load_config(guild_id: int, auto_create: bool = True):
    path = f'server_configs/{guild_id}'
    file_path = f'{path}/config.yaml'

    if not os.path.exists(file_path):
        if auto_create:
            os.makedirs(path, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(DEFAULT_CONFIG, f, allow_unicode=True)
            return DEFAULT_CONFIG(f)
        else:
            return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load

async def translate(text: str, dest_lng: str):
    if dest_lng != "en":
        result = translator.translate(text, src='en', dest=dest_lng)
    else:
        result = text
    
    return result