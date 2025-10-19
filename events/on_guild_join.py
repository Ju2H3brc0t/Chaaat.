import discord
from discord.ext import commands
import os
import yaml
import json

class on_guild_join(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        os.makedirs(f'server_configs/{guild.id}', exist_ok=True)
        
        default_yaml = {
            'features': {
                'language': {
                    'default': 'en'
                },
                'counting': {
                    'enabled': False,
                    'channel_id': 0,
                    'reset_if_wrong_user': False
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
    await client.add_cog(on_guild_join(client))
