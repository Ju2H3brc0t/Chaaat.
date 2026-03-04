from utils import remove_guild_from_db
from discord.ext import commands
import shutil
import os

class OnGuildRemove(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if os.path.exists(f'server_configs/{guild.id}'): shutil.rmtree(f'server_configs/{guild.id}')
        await remove_guild_from_db(guild_id=guild.id)

async def setup(client):
    await client.add_cog(OnGuildRemove(client))
