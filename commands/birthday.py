import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import json
import yaml

class Birthday(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @app_commands.command(name="birthday", description="Register or modify your birthday")
    @app_commands.describe(date="Your birthday in DD/MM/YYYY format")
    async def birthday(self, interaction: discord.Interaction, date: str):
        guild_id = interaction.guild_id
        config_path = f'server_configs/{guild_id}/config.yaml'
        user_data_path = f'server_configs/{guild_id}/{interaction.user.id}.json'

        try:
            with open(config_path, 'r') as yaml_file:
                config = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            await interaction.response.send_message("⚠️ Config file not found for this server.", ephemeral=True)
            return

        try:
            with open(user_data_path, 'r') as json_file:
                user_data = json.load(json_file)
        except FileNotFoundError:
            print(f"⚠️ User data file not found for user {interaction.author.id} in guild {guild_id}.")
            return
        
        language = str(config['features'].get('language'))
        birthday = datetime.strptime(date, "%d/%m/%Y")
        birthday_enabled = bool(config['features']['birthday'].get('enabled'))
        if birthday_enabled is True:
            user_data['birthday'] = birthday
            with open(user_data_path, 'w') as json_file:
                json.dump(user_data, json_file, indent=4)   # À ajouter: confirmation -> 'language'
            if language == 'fr':
                await interaction.response.send_message(f"✅ Votre anniversaire a été enregistré comme le {date}.", ephemeral=True)
            else:
                await interaction.response.send_message(f"✅ Your birthday has been registered as {date}.", ephemeral=True)


async def setup(client):
    await client.add_cog(Birthday(client))