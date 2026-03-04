import discord
from discord import app_commands
from discord.ext import commands

class Misc(commands.Cog):
    def __init__(self, client):
        self.client = client

    misc_group = app_commands.Group(name="misc", description="Various commands")

    @misc_group.command(name="ping", description="Show bot's latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.client.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong ! ({latency}ms)")

    @misc_group.command(name="say", description="Make the bot say something")
    @app_commands.describe(message="The text teh bot has to say")
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)

async def setup(client):
    await client.add_cog(Misc(client))