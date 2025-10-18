import discord
from discord import app_commands
from discord.ext import commands
import yaml

class config(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="view_config", description="Display the current server configuration")
    async def config(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        config_path = f'server_configs/{guild_id}/config.yaml'

        try:
            with open(config_path, 'r') as yaml_file:
                config = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            await interaction.response.send_message("⚠️ Config file not found for this server.", ephemeral=True)
            return

        config_message = "Current Server Configuration:\n"
        for feature, settings in config.get('features', {}).items():
            config_message += f"**{feature.capitalize()}**:\n"
            for key, value in settings.items():
                config_message += f"- {key}: {value}\n"

        await interaction.response.send_message(config_message, ephemeral=True)

async def setup(client):
    await client.add_cog(config(client))
