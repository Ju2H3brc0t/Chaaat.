import discord
from discord.ext import commands
import os
import yaml
import json

class OnGuildJoin(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        os.makedirs(f'server_configs/{guild.id}', exist_ok=True)
        
        default_yaml = {
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
                    'rewards': {
                        '0': 0
                    },
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

        default_json = {
            'counting': 0,
            'last_user_id': 0
        }

        with open(f'server_configs/{guild.id}/config.yaml', 'w') as yaml_file:
            yaml.dump(default_yaml, yaml_file)

        with open(f'server_configs/{guild.id}/data.json', 'w') as json_file:
            json.dump(default_json, json_file, indent=4)

async def setup(client):
    await client.add_cog(OnGuildJoin(client))
