import discord
from discord import app_commands
from discord.ext import commands
import yaml
import os

owner_id_str = os.getenv('OWNER_USER_ID')
if not owner_id_str:
    print("‼️ Error: OWNER_USER_ID environment variable not set.")
    raise ValueError()
else:
    owner_id = int(owner_id_str)

class Stop(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="stop", description="Shut down the bot")
    async def stop(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        config_path = f'server_configs/{guild_id}/config.yaml'

        try:
            with open(config_path, 'r') as yaml_file:
                config = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            print(f"⚠️ Config file not found for guild {guild_id}.")
            return

        language = str(config['features']['language'].get('default'))

        if interaction.user.id == owner_id:
            if language == "fr":
                await interaction.response.send_message("🪫 Arrêt en cours...", ephemeral=True)
            else:
                await interaction.response.send_message("🪫 Shutting down...", ephemeral=True)
            await self.client.close()
        else:
            if language == "fr":
                await interaction.response.send_message("⛔️ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            else:
                await interaction.response.send_message("⛔️ You do not have permission to use this command.", ephemeral=True)

async def setup(client):
    await client.add_cog(Stop(client))