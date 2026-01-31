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
    @app_commands.describe(date="Your birthday in DD/MM format")
    async def birthday(self, interaction: discord.Interaction, date: str):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild_id
        config_path = f'server_configs/{guild_id}/config.yaml'
        user_data_path = f'server_configs/{guild_id}/{interaction.user.id}.json'

        try:
            with open(config_path, 'r') as yaml_file:
                config = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            return await interaction.followup.send("⚠️ Config file not found for this server.", ephemeral=True)
        
        try:
            with open(user_data_path, 'r') as json_file:
                user_data = json.load(json_file)
        except FileNotFoundError:
            return await interaction.followup.send(f"⚠️ User data file not found for user {interaction.user.id} in guild {guild_id}.")
        
        language = str(config['features'].get('language'))
        birthday = date
        birthday_enabled = bool(config['features']['birthday'].get('enabled'))

        if birthday_enabled is True:
            try:
                datetime.strptime(date, "%d/%m")
            except ValueError:
                if language == "fr":
                    return await interaction.followup.send(f"❌ Date invalide, format JJ/MM attendu (ex: 25/12)", ephemeral=True)
                else:
                    return await interaction.followup.send(f"❌ Invalid date, DD/MM format required (ex: 25/12)", ephemeral=True)
            
            user_data['birthday'] = birthday
            with open(user_data_path, 'w') as json_file:
                json.dump(user_data, json_file, indent=4)
            if language == "fr":
                await interaction.followup.send(f"✅ Votre anniversaire a été enregistré comme le {date}.", ephemeral=True)
            else:
                await interaction.followup.send(f"✅ Your birthday has been registered as {date}.", ephemeral=True)
        else:
            if language == "fr":
                await interaction.followup.send("🧩 Cette fonctionalitée est désactivée sur ce serveur.", ephemeral=True)
            else:
                await interaction.followup.send("🧩 This feature is disabled on this server.", ephemeral=True)

async def setup(client):
    await client.add_cog(Birthday(client))