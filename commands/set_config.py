import discord
from discord import app_commands
from discord.ext import commands
import yaml

class SetConfig(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @app_commands.command(name="set_config", description="Update configuration for the server")
    async def set_config(self, interaction: discord.Interaction, path:str):
        guild_id = interaction.guild_id
        config_path = f'server_configs/{guild_id}/config.yaml'

        try:
            with open(config_path, 'r') as yaml_file:
                config = yaml.safe_load(yaml_file) or {}
        except FileNotFoundError:
            await interaction.response.send_message("⚠️ Config file not found for this server.", ephemeral=True)
            return

        if "features" not in config:
            await interaction.response.send_message("⚠️ Invalid config format (no 'features' keys).", ephemeral=True)
            return

        language = str(config['features'].get('language'))

        if 'features' not in config or not isinstance(config['features'], dict):
            if language == "fr":
                await interaction.response.send_message("⚠️ Format de configuration invalide (pas de clés 'features').", ephemeral=True)
            else:
                await interaction.response.send_message("⚠️ Invalid config format (no 'features' keys).", ephemeral=True)
            return

        keys = path.split(':')
        if len(keys) < 2:
            await interaction.response.send_message("⚠️ Path must be in the format 'feature:option:value'.", ephemeral=True)
            return
        
        *dict_path, value = keys

        ref = config['features']
        for key in dict_path[:-1]:
            if key not in ref or not isinstance(ref[key], dict):
                if language == "fr":
                    await interaction.response.send_message(f"⚠️ La fonctionnalité '{key}' n'existe pas.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"⚠️ Feature '{key}' does not exist.", ephemeral=True)
                return
            ref = ref[key]
        
        final_key = dict_path[-1]
        if final_key not in ref:
            if language == "fr":
                await interaction.response.send_message(f"⚠️ L'option '{final_key}' n'existe pas dans la fonctionnalité.", ephemeral=True)
            else:
                await interaction.response.send_message(f"⚠️ Option '{final_key}' does not exist in the feature.", ephemeral=True)
            return
        
        new_value = yaml.safe_load(value)
        ref[final_key] = new_value

        with open(config_path, 'w') as yaml_file:
            yaml.safe_dump(config, yaml_file)

        await interaction.response.send_message(f"✅ Configuration updated")

async def setup(client):
    await client.add_cog(SetConfig(client))
