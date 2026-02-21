from utils import load_config, update_db, translate
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class Birthday(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @app_commands.command(name="birthday", description="Register or modify your birthday")
    @app_commands.describe(date="Your birthday in DD/MM format")
    async def birthday(self, interaction: discord.Interaction, date: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))

        birthday_enabled = bool(config['features']['birthday'].get('enabled'))

        birthday = date

        if birthday_enabled:
            await interaction.response.defer(ephemeral=True)
            try:
                datetime.strptime(date, "%d/%m")
            except ValueError:
                value_error_message = await translate(text="❌ Invalid date, DD/MM format required (ex: 25/12)", dest_lng=language)
                return await interaction.followup.send(value_error_message, ephemeral=True)
        
            await update_db(column='birthday', value=birthday, user_id=interaction.user_id, guild_id=interaction.guild_id)
        
            success_message = await translate(text=f"✅ Your birthday has been registered as {date}.")
            await interaction.followup.send(success_message, ephemeral=True)
        else:
            not_activated_message = await translate(text="🧩 This feature is disabled on this server.", dest_lng=language)
            await interaction.response.send_message(not_activated_message)

async def setup(client):
    await client.add_cog(Birthday(client))