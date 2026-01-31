import discord
from discord.ext import commands, tasks
from datetime import datetime
import json
import yaml
import os

class BirthdayVerification(commands.Cog):
    def __init__(self, client):
        self.client = client

    @tasks.loop(time=datetime.time(hour=8, minute=0, second=0))
    async def verify_birthdays(self):
        for dir in os.listdir('./server_configs'):
            for users in os.listdir(f'./server_configs/{dir}'):
                if users.endswith('.json'):
                    user_data_path = f'./server_configs/{dir}/{users}'
                    config_path = f'./server_configs/{dir}/config.yaml'
                    today = datetime.now().strftime("%d/%m")

                    try:
                        with open(config_path, 'r') as yaml_file:
                            config = yaml.safe_load(yaml_file)
                    except FileNotFoundError:
                        print(f"⚠️ Config file not found for guild {dir}.")
                        continue

                    try:
                        with open(user_data_path, 'r') as json_file:
                            user_data = json.load(json_file)
                    except FileNotFoundError:
                        print(f"⚠️ User data file not found: {user_data_path}.")
                        continue

                    birthday_enabled = bool(config['features']['birthday'].get('enabled'))
                    if birthday_enabled is True and 'birthday' in user_data:
                        birthday_str = user_data['birthday']
                        birthday_date = datetime.strptime(birthday_str, "%%d/%m/%Y")

                        if birthday_date.strftime("%d/%m") == today:
                            guild = self.client.get_guild(int(dir))
                            member = guild.get_member(int(users.split('.')[0]))
                            if member:
                                channel_id = int(config['features']['birthday'].get('announcement_channel_id'))
                                channel = self.client.get_channel(channel_id)
                                language = config['features'].get('language', 'en')

                                if language == 'fr':
                                    embed_title = "Joyeux Anniversaire !"
                                    embed_description = f"🎉🎂 Bon anniversaire à {member.mention} !"
                                else:
                                    embed_title = "Happy Birthday!"
                                    embed_description = f"🎉🎂 Happy birthday to {member.mention} !"

                                embed = discord.Embed(
                                    title=embed_title,
                                    description=embed_description,
                                    color=discord.Color.pink(),
                                    timestamp=discord.utils.utcnow()
                                )
                                embed.set_thumbnail(url=member.display_avatar.url)
                                await channel.send(embed=embed)
            

            

async def setup(client):
    await client.add_cog(BirthdayVerification(client))
