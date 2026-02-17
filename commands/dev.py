from utils import load_config, translate
import discord
from discord import app_commands
from discord.ext import commands
import subprocess
import os

class Dev(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def get_devs_ids(self):
        env_devs = os.getenv('DEVS_USER_IDS')
        if not env_devs:
            print("‼️ Error: OWNER_USER_ID environment variable not set.")
            devs_ids = []
        else:
            devs_ids = [int(uid.strip()) for uid in env_devs.split(',')]
        return devs_ids

    @app_commands.command(name="dev", description="Useful commands for the developpers of the bot")
    @app_commands.describe(action="Which action you want to perform")
    @app_commands.check.has_permissions(administrator=True)
    @app_commands.choices(action=[
        app_commands.Choice(name="Shutdown", value="stop"),
        app_commands.Choice(name="Update (from Github)", value="update"),
        app_commands.Choice(name="Reload", value="reload")
    ])

    async def shutdown(self, interaction: discord.Interaction):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language', 'en'))

        response_text = await translate(text="🪫 Shutting down...", dest_lng=language)
        
        await interaction.followup.send(response_text, ephemeral=True)

        await self.client.close()
    
    async def update(self, interaction: discord.Interaction):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language', 'en'))

        try:
            subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
            process = subprocess.run(["git", "pull", "origin", "main"], check=True, capture_output=True, text=True)
            log_git = process.stdout if process.stdout else "Already up to date."

            intro_subprocess_text = await translate(text=f"✅ Update successful:", dest_lng=language)
            subprocess_text = f"{intro_subprocess_text}\n```{log_git}```"

            await interaction.followup.send(subprocess_text, ephemeral=True)
        except subprocess.CalledProcessError as e:
            intro_error_message = await translate(text="❌ Git Error: ", dest_lng=language)
            error_msg = f"{intro_error_message}{e.stderr.decode()}"

            await interaction.followup.send(error_msg, ephemeral=True)
    
    async def reload(self, interaction: discord.Interaction):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language', 'en'))

        folders = ['commands', 'events']
        extensions = []
        response = []

        client = self.client

        for folder in folders:
            for filename in os.listdir(folder):
                if filename.endswith('.py'):
                    extensions.append(f'{folder}.{filename[:-3]}')

        for extension in extensions:
            try:
                if extension in client.extensions:
                    await client.reload_extension(extension)

                    intro_reloaded_extension_message = await translate(text="📁 Reloaded extension: ", dest_lng=language)
                    loaded_extension_message = f"{intro_reloaded_extension_message}{extension}"

                    response.append(loaded_extension_message)
                else:
                    await client.load_extension(extension)

                    intro_loaded_extension_message = await translate(text="📂 Loaded extension: ", dest_lng=language)
                    loaded_extension_message = f"{intro_loaded_extension_message}{extension}"

            except Exception as e:
                intro_error_loaded_extenion_message = await translate(text="⚠️ Failed to load extension ", dest_lng=language)
                error_loaded_extension_message = f"{intro_error_loaded_extenion_message}{extension}: {e}"

                response.append(error_loaded_extension_message)

        try:
            synced = await client.tree.sync()
            
            synced_message = await translate(text=f"🌐 Synced {len(synced)} command(s)", dest_lng=language)

            response.append(synced_message)
        except Exception as e:
            intro_error_synced_message = await translate(text="⚠️ Failed to sync commands: ", dest_lng=language)
            error_synced_message = f"{intro_error_synced_message}{e}"

            response.append(error_synced_message)

        response_message = "\n".join(response)
        await interaction.followup.send(f"```ml\n{response_message}\n```")

    async def command(self, interaction: discord.Interaction, action: str):
        config = await load_config(guild_id=interaction, auto_create=True)
        language = str(config['features'].get('language', 'en'))

        refused_text = await translate(text="⛔️ You do not have permission to use this command.", dest_lng=language)
        
        if interaction.user.id not in await self.get_devs_ids():
            await interaction.response.send_message(refused_text, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        if action == "stop":
            await self.shutdown(interaction)

        elif action == "update":
            await self.update(interaction)

        elif action == "reload":
            await self.reload(interaction)

async def setup(client):          
    await client.add_cog(Dev(client))