import discord
from discord.ext import commands
import shutil

class OnGuildRemove(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        shutil.rmtree(f'server_configs/{guild.id}')

async def setup(client):
    await client.add_cog(OnGuildRemove(client))

