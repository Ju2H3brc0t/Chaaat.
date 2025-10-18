import discord
from discord import app_commands
from discord.ext import commands

class ping(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="ping", description="Check if the bot is still responding")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message('🏓 Pong!')

async def setup(client):
    await client.add_cog(ping(client))