from utils import init_db
from ui.tickets import TicketLauncher
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import os
import traceback

load_dotenv()

token = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix='!', intents=intents)

initial_extensions = []
folders = ['commands', 'events']

if token is None:
    print("‼️ Error: DISCORD_BOT_TOKEN environment variable not set.")
    raise ValueError()
else:
    print("🔑 Bot token found.")
    token_str = str(token)

@client.event
async def on_ready():
    if not initial_extensions:
        try:
            await init_db()
        except Exception as e:
            print(f"⚠️ Failed to load database: {e}")
            traceback.print_exc()
        
        for folder in folders:
            for filename in os.listdir(folder):
                if filename.endswith('.py') and not filename.startswith('__'):
                    initial_extensions.append(f'{folder}.{filename[:-3]}')
        
        for extension in initial_extensions:
            try:
                await client.load_extension(extension)
                print(f'📂 Loaded extension: {extension}')
            except Exception as e:
                print(f'⚠️ Failed to load extension {extension}: {e}.')
                traceback.print_exc()
        
        client.add_view(TicketLauncher())
        print("📩 Ticket view registered (Persistent)")

        try:
            synced = await client.tree.sync()
            print(f'🌐 Synced {len(synced)} command(s)')
        except Exception as e:
            print(f'⚠️ Failed to sync commands: {e}')
            traceback.print_exc()
    
    print(f'✅ Logged in as {client.user}')

@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"❌ Slash command error: {error}")
    traceback.print_exc()
    if not interaction.response.is_done():
        await interaction.response.send_message(f"Error: `{error}`", ephemeral=True)

async def main():
    async with client:
        await client.start(token_str)

if __name__ == '__main__':
    asyncio.run(main())