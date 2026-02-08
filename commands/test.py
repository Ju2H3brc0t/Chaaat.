import discord
from discord.ext import commands
from discord import app_commands

class Test(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="Test", description="c'est le test de Melvilou !!")
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("Whoaw t'es un bg !!", ephemeral=True)

async def setup(client):
    await client.add_cog(Test(client))

    