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

class Reload(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="reload", description="Hot-reload the command and event list of the bot")
    async def reload(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id == owner_id:
            guild_id = interaction.guild_id
            config_path = f'server_configs/{guild_id}/config.yaml'

            try:
                with open(config_path, 'r') as yaml_file:
                    config = yaml.safe_load(yaml_file)
            except FileNotFoundError:
                print(f"⚠️ Config file not found for guild {guild_id}.")
                return await interaction.followup.send(f'⚠️ Config file not found for guild {guild_id}.')
            
            language = str(config['features'].get('language'))

            extensions = []
            folders = ['commands', 'events']
            response = []

            client = self.client

            for folder in folders:
                for filename in os.listdir(folder):
                    if filename.endswith('.py'):
                        extensions.append(f'{folder}.{filename[:-3]}')
        
            for extension in extensions:
                try:
                    await client.reload_extension(extension)
                    if language == "fr":
                        response.append(f'📦 Extension chargé: {extension}')
                    else:
                        response.append(f'📦 Loaded extension: {extension}')
                except Exception as e:
                    if language == "fr":
                        response.append(f'⚠️ Erreur lors du chargement de l\'extension {extension}: {e}')
                    else:
                        response.append(f'⚠️ Failed to load extension {extension}: {e}.')

            try:
                synced = await client.tree.sync()
                if language == "fr":
                    response.append(f'🌐 {len(synced)} commande(s) synchronisée')
                else:
                    response.append(f'🌐 Synced {len(synced)} command(s)')
            except Exception as e:
                if language == "fr":
                    response.append(f'⚠️ Erreur lors de la synchronisation des extensions: {e}')
                else:
                    response.append(f"⚠️ Failed to sync commands: {e}")

            response_message = "\n".join(response)
            await interaction.followup.send(f"```ml\n{response_message}\n```")

        else:
            await interaction.response.send_message("⛔️ You do not have permission to use this command.", ephemeral=True)

async def setup(client):
    await client.add_cog(Reload(client))