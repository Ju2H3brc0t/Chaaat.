import discord
from discord.ext import commands

class on_guild_join(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f'➕ Joined new guild: {guild.name} (ID: {guild.id})')