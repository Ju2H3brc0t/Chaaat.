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

class Reload(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="reload", description="Hot-reload the command and event list of the bot")
    async def reload(self, interaction: discord.Interaction):
        if interaction.user.id == owner_id:    
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
                    response.append(f'📦 Loaded extension: {extension}')
                except Exception as e:
                    response.append(f'⚠️ Failed to load extension {extension}: {e}.')

            try:
                synced = await client.tree.sync()
                response.append(f'🌐 Synced {len(synced)} command(s)')
            except Exception as e:
                response.append(f"⚠️ Failed to sync commands: {e}")

            response_message = "\n".join(response)
            await interaction.response.send_message(f"```ml\n{response_message}\n```")

        else:
            await interaction.response.send_message("⛔️ You do not have permission to use this command.", ephemeral=True)

async def setup(client):
    await client.add_cog(Reload(client))