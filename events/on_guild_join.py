from utils import DEFAULT_CONFIG, DEFAULT_JSON, add_users_to_db
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
        
        with open(f'server_configs/{guild.id}/config.yaml', 'w') as yaml_file:
            yaml.dump(DEFAULT_CONFIG, yaml_file)

        with open(f'server_configs/{guild.id}/data.json', 'w') as json_file:
            json.dump(DEFAULT_JSON, json_file, indent=4)

        await guild.chunk()
        for member in guild.members:
            if not member.bot:
                await add_users_to_db(member.id, guild.id)

async def setup(client):
    await client.add_cog(OnGuildJoin(client))
