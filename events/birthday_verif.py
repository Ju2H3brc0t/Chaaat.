import discord
from discord.ext import commands, tasks
import datetime
import json
import yaml
import os

class BirthdayVerif(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.verif_birthday.start()
    
    def cog_unload(self):
        self.verif_birthday.cancel()
    
    @tasks.loop(time=datetime.time(hour=8, minute=0))
    async def verif_birthday(self):
        for dir in os.listdir(f'server_configs'):
            for users in os.listdir(f'server_configs/{dir}'):
                if users.endswith('.json'):
                    user_data_path = f'server_configs/{dir}/{users}'
                    config_path = f'server_configs/{dir}/config.yaml'
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

                    if birthday_enabled is True and user_data['birthday'] != "0":
                        birthday = user_data['birthday']

                        if birthday == today:
                            guild = self.client.get_guild(int(dir))
                            member = guild.get_member(int(users.split('.')[0]))

                            if member:
                                channel_id = int(config['features']['birthday'].get('announcement_channel_id'))
                                channel = self.client.get_channel(channel_id)
                                language = config['features'].get('language')

                                if language == "fr":
                                    embed_title = f"Joyeux Anniversaire {member.mention} !"
                                    embed_description = f"🎉🎂 On souhaite un joyeux anniversaire a {member.mention} !"
                                else:
                                    embed_title = f"Happy Birthday {member.mention} !"
                                    embed_description = f"🎉🎂 We wish an happy birthday to {member.mention} !"
                                
                                embed = discord.Embed(
                                    title = embed_title,
                                    description = embed_description,
                                    color = discord.Color.pink(),
                                    timestamp = discord.utils.utcnow()
                                )
                                embed.set_thumbnail(url=member.display_avatar.url)
                                await channel.send(embed=embed)

async def setup(client):
    await client.add_cog(BirthdayVerif(client))