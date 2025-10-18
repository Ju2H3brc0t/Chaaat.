import discord
from discord import app_commands
from discord.ext import commands
import yaml
import os

class setconfig(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @app_commands.command(name="set_config", description="Set a configuration option for the server")
    @app_commands.describe(feature="The name of the feature to configure", option="The option to modify", value="The value to set the option to")
    async def set_config(self, interaction: discord.Interaction, feature: str, option: str, value: str):
        guild_id = interaction.guild_id
        config_path = f'server_configs/{guild_id}/config.yaml'

        if not os.path.exists(config_path):
            await interaction.response.send_message("⚠️ Config file not found for this server.", ephemeral=True)
            return

        with open(config_path, 'r') as yaml_file:
            config = yaml.safe_load(yaml_file) or {}

        if 'features' not in config or not isinstance(config['features'], dict):
            await interaction.response.send_message("⚠️ Format de config invalide (pas de clé 'features').", ephemeral=True)
            return

        if feature not in config['features']:
            await interaction.response.send_message(f"⚠️ Feature '{feature}' does not exist in the configuration.", ephemeral=True)
            return

        feature_config = config['features'][feature]
        if feature_config is None:
            feature_config = {}
            config['features'][feature] = feature_config

        raw = value.strip().strip(',')
        parsed_value = None
        lowered = raw.lower()
        if lowered in ('true', 'false'):
            parsed_value = lowered == 'true'
        else:
            try:
                parsed_value = int(raw)
            except ValueError:
                parsed_value = raw

        feature_config[option] = parsed_value

        with open(config_path, 'w') as yaml_file:
            yaml.safe_dump(config, yaml_file, sort_keys=False)

        await interaction.response.send_message(
            f"✅ Configuration updated: `{feature}.{option}` → `{parsed_value}`")

async def setup(client):
    await client.add_cog(setconfig(client))
