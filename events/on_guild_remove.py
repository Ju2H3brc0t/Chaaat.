import discord
from discord.ext import commands
import shutil
import yaml
import json

class on_guild_remove(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        shutil.rmtree(f'server_configs/{guild.id}')

async def setup(client):
    await client.add_cog(on_guild_remove(client))

