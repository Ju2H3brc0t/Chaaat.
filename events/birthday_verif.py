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

            config_path = f'server_configs/{dir}/config.yaml'

            try:
                with open(config_path, 'r') as yaml_file:
                    config = yaml.safe_load(yaml_file)
            except FileNotFoundError:
                print(f"⚠️ Config file not found for guild {dir}")
                continue

            for users in os.listdir(f'server_configs/{dir}'):
                if users.endswith('.json') and users != 'data.json':
                    user_data_path = f'server_configs/{dir}/{users}'
                    today = datetime.datetime.now().strftime("%d/%m")
                    
                    try:
                        with open(user_data_path, 'r') as json_file:
                            user_data = json.load(json_file)
                    except FileNotFoundError:
                        print(f"⚠️ User data file not found: {user_data_path}.")
                        continue
                    
                    birthday_enabled = bool(config['features']['birthday'].get('enabled'))

                    if birthday_enabled is True and user_data['birthday'] != "0":
                        birthday = user_data['birthday']
                        guild = self.client.get_guild(int(dir))
                        member = await guild.fetch_member(int(users.split('.')[0]))

                        if birthday == today:
                            if member:
                                channel_id = int(config['features']['birthday'].get('announcement_channel_id'))
                                channel = self.client.get_channel(channel_id)
                                language = config['features'].get('language')

                                gift_enabled = bool(config['features']['birthday']['gift'].get('enabled'))
                                
                                if user_data['last_gift'] != [0]:
                                    role_to_remove = []
                                    for role_id in user_data['last_gift']:
                                        role = member.guild.get_role(int(role_id))
                                        if role is not None:
                                            role_to_remove.append(role)
                                    if role_to_remove:
                                        await member.remove_roles(*role_to_remove)

                                if language == "fr":
                                    embed_title = f"Joyeux Anniversaire {member.display_name} !"
                                    embed_description = f"🎉🎂 On souhaite un joyeux anniversaire a <@{member.id}> !"
                                else:
                                    embed_title = f"Happy Birthday {member.display_name} !"
                                    embed_description = f"🎉🎂 We wish an happy birthday to <@{member.id}> !"
                                
                                embed = discord.Embed(
                                    title = embed_title,
                                    description = embed_description,
                                    color = discord.Color.pink(),
                                    timestamp = discord.utils.utcnow()
                                )
                                embed.set_thumbnail(url=member.display_avatar.url)

                                if gift_enabled is True:
                                    role_list = config['features']['birthday']['gift'].get('role')
                                    temporary_role_list = config['features']['birthday']['gift'].get('temporary_role')
                                    xp = config['features']['birthday']['gift'].get('xp')
                                    
                                    for role_id in role_list:
                                        role = member.guild.get_role(int(role_id))
                                        if role is not None:
                                            await member.add_roles(role)
                                    
                                    for role_id in temporary_role_list:
                                        role = member.guild.get_role(int(role_id))
                                        if role is not None:
                                            await member.add_roles(role)
                                    
                                    if xp > 0:
                                        current_xp = user_data.get('experience')
                                        user_data['experience'] = current_xp + xp

                                        with open(user_data_path, 'w') as json_file:
                                            json.dump(user_data, json_file, indent=4)
                                    
                                    if temporary_role_list != [0]:
                                        user_data['last_gift'] = temporary_role_list

                                        with open(user_data_path, 'w') as json_file:
                                            json.dump(user_data, json_file, indent=4)

                                await channel.send(embed=embed)

async def setup(client):
    await client.add_cog(BirthdayVerif(client))