import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import os

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

for folder in folders:
    for filename in os.listdir(folder):
        if filename.endswith('.py'):
            initial_extensions.append(f'{folder}.{filename[:-3]}')

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')
    try:
        synced = await client.tree.sync()
        print(f'🌐 Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'⚠️ Failed to sync commands: {e}')

async def main():
    for extension in initial_extensions:
        try:
            await client.load_extension(extension)
            print(f'📦 Loaded extension: {extension}')
        except Exception as e:
            print(f'⚠️ Failed to load extension {extension}: {e}.')
        
    await client.start(token_str)

if __name__ == '__main__':
    asyncio.run(main())