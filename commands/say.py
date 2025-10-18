import discord
from discord import app_commands
from discord.ext import commands

class say(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="say", description="Make the bot say something")
    @app_commands.describe(message="The message for the bot to say")
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)
    
async def setup(client):
    await client.add_cog(say(client))