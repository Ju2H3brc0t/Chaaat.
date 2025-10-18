import discord
from discord import app_commands
from discord.ext import commands
import os

owner_id_str = os.getenv('OWNER_USER_ID')
if not owner_id_str:
    print("‼️ Error: OWNER_USER_ID environment variable not set.")
    raise ValueError()
else:
    owner_id = int(owner_id_str)

class stop(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="stop", description="Shut down the bot")
    async def stop(self, interaction: discord.Interaction):
        if interaction.user.id == owner_id:
            await interaction.response.send_message("🪫 Shutting down...", ephemeral=True)
            await self.client.close()
        else:
            await interaction.response.send_message("⛔️ You do not have permission to use this command.", ephemeral=True)

async def setup(client):
    await client.add_cog(stop(client))