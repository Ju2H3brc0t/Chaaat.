import discord
from discord.ext import commands
import asyncio
import yaml
import json

class OnMessage(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_message(self, message):
    
        if message.author.bot:
            return

        guild_id = message.guild.id
        config_path = f'server_configs/{guild_id}/config.yaml'
        data_path = f'server_configs/{guild_id}/data.json'
        user_data_path = f'server_configs/{guild_id}/{message.author.id}.json'

        try:
            with open(config_path, 'r') as yaml_file:
                config = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            print(f"⚠️ Config file not found for guild {guild_id}.")
            return

        try:
            with open(data_path, 'r') as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            print(f"⚠️ Data file not found for guild {guild_id}.")
            return

        try:
            with open(user_data_path, 'r') as json_file:
                user_data = json.load(json_file)
        except FileNotFoundError:
            print(f"⚠️ User data file not found for user {message.author.id} in guild {guild_id}.")
            return

        counting_enabled = bool(config['features']['counting'].get('enabled'))
        reset_if_wrong_user = bool(config['features']['counting'].get('reset_if_wrong_user'))

        level_enabled = bool(config['features']['leveling'].get('enabled'))
        rewards = config['features']['leveling'].get('rewards')
        rewards_stackable = bool(config['features']['leveling'].get('rewards_stackable'))
        excluded_channels = config['features']['leveling'].get('exclude_channels')
        boosted_channels = config['features']['leveling'].get('boost_channels')
        announcement_enabled = bool(config['features']['leveling']['announcement'].get('enabled'))
        announcement_channel_id = int(config['features']['leveling']['announcement'].get('channel_id'))

        autodelete_enabled = bool(config['features']['message_autodelete'].get('enabled'))
        autodelete_duration = int(config['features']['message_autodelete'].get('wait_m'))

        bump_reminder_enabled = bool(config['features']['bump_reminder'].get('enabled'))
        bump_reminder_channel_id = int(config['features']['bump_reminder'].get('channel_id'))


        language = str(config['features'].get('language'))

        if counting_enabled is True:
            channel_id = int(config['features']['counting'].get('channel_id'))
            current_count = int(data.get('counting', 0))
            if message.channel.id == channel_id:
                expected_count = int(current_count + 1)
                last_user_id = data.get('last_user_id', 0)
                try:
                    user_count = int(message.content)
                except ValueError:
                    if language == "fr":
                        await message.channel.send(f"{message.author.mention}, veuillez envoyer un nombre valide.\n-# Le nombre suivant est {expected_count}.")
                    else:
                        await message.channel.send(f"{message.author.mention}, please send a valid number.\n-# Next number is {expected_count}.")
                    return

                if user_count != expected_count:
                    await message.add_reaction("❌")
                    if language == "fr":
                        await message.channel.send(f"{message.author.mention} a fait une erreur, le compteur a été réinitialisé.\n-# Le nombre suivant est 1.")
                    else:
                        await message.channel.send(f"{message.author.mention} made a mistake, the counter was reset.\n-# Next number is 1.")
                    data['counting'] = 0
                    data['last_user_id'] = 0
                    with open(data_path, 'w') as json_file:
                        json.dump(data, json_file, indent=4)
                elif message.author.id == last_user_id:
                    await message.add_reaction("❌")
                    if reset_if_wrong_user == True:
                        data['counting'] = 0
                        data['last_user_id'] = 0
                        with open(data_path, 'w') as json_file:
                            json.dump(data, json_file, indent=4)
                        if language == "fr":
                            await message.channel.send(f"{message.author.mention}, vous ne pouvez pas compter deux nombres d'affilée, le compteur a été réinitialisé.\n-# Le nombre suivant est 1.")
                    elif language == "fr" and reset_if_wrong_user == False:
                        await message.channel.send(f"{message.author.mention}, vous ne pouvez pas compter deux nombres d'affilée !\n-# Le nombre suivant est {expected_count}.")
                    elif language != "fr" and reset_if_wrong_user == False:
                        await message.channel.send(f"{message.author.mention}, you cannot count two numbers in a row!\n-# Next number is {expected_count}.")
                elif user_count == expected_count and user_count == 100 and message.author.id != last_user_id:
                    await message.add_reaction("💯")
                    data['counting'] = int(expected_count)
                    data['last_user_id'] = message.author.id
                    with open(data_path, 'w') as json_file:
                        json.dump(data, json_file, indent=4)
                elif user_count == expected_count and message.author.id != last_user_id:
                    await message.add_reaction("✅")
                    data['counting'] = int(expected_count)
                    data['last_user_id'] = message.author.id
                    with open(data_path, 'w') as json_file:
                        json.dump(data, json_file, indent=4)
                else:
                    await message.add_reaction("❓")
                    if language == "fr":
                        await message.channel.send(f"⚠️ {message.author.mention}, une erreur inattendue est survenue, veuillez réessayer plus tard.")
                    else:
                        await message.channel.send(f"⚠️ {message.author.mention}, an unexpected error occurred, please try again later.")
        
        if level_enabled is True:
            if not excluded_channels or message.channel.id not in excluded_channels:
                current_lvl = int(user_data.get('level'))
                current_xp = int(user_data.get('experience'))
                reward_role = None

                xp_to_next = 5 * (current_lvl ** 2) + 50 * current_lvl + 100
                next_lvl = current_lvl +1

                if current_lvl >= 100:
                    return
                
                if current_xp >= xp_to_next:
                    user_data['level'] = int(current_lvl + 1)
                    user_data['experience'] = int(current_xp - xp_to_next)
                    with open(user_data_path, 'w') as json_file:
                        json.dump(user_data, json_file, indent=4)
                    if rewards is not None:
                        levels = sorted(map(int, rewards.keys()))

                        if next_lvl in levels:
                            role_id = message.guild.get_role(int(rewards[str(next_lvl)]))

                            if role_id is not None:
                                if rewards_stackable is True:
                                    await message.author.add_roles(role_id)
                                else:
                                    index = levels.index(next_lvl)

                                    if index == 0:
                                        default_role = message.guild.get_role(int(config['features']['leveling'].get('default_level')))
                                        if default_role and default_role in message.author.roles:
                                            await message.author.remove_roles(default_role)
                                    else:
                                        previous_lvl = levels[index - 1]
                                        previous_role = message.guild.get_role(int(rewards[str(previous_lvl)]))
                                        if previous_role and previous_role in message.author.roles:
                                            await message.author.remove_roles(previous_role)
                                    
                                    await message.author.add_roles(role_id)
                                reward_role = role_id

                    if announcement_enabled is True:
                        channel = message.guild.get_channel(announcement_channel_id)
                        xp_to_next_in_announcement = 5 * (next_lvl ** 2) + 50 * next_lvl + 100
                        if language == "fr":
                            if reward_role is not None:
                                embed_title = "🎉 Nouveau niveau atteint !"
                                embed_description = f"Félicitations {message.author.mention}, vous avez atteint le niveau **{next_lvl}** !\nPour passer au niveau suivant, vous avez besoin de **{xp_to_next_in_announcement}** exp.\n\n-#🏅 Vous avez gagné le rôle {reward_role.mention}."
                            else:
                                embed_title = "🎉 Nouveau niveau atteint !"
                                embed_description = f"Félicitations {message.author.mention}, vous avez atteint le niveau **{next_lvl}** !\nPour passer au niveau suivant, vous avez besoin de **{xp_to_next_in_announcement}** exp."
                        else:
                            if reward_role is not None:
                                embed_title = "🎉 New level reached!"
                                embed_description = f"Congratulations {message.author.mention}, you have reached level **{next_lvl}**!\nTo advance to the next level, you need **{xp_to_next_in_announcement}** exp.\n\n-#🏅 You have earned the role {reward_role.mention}."
                            else:
                                embed_title = "🎉 New level reached!"
                                embed_description = f"Congratulations {message.author.mention}, you have reached level **{next_lvl}**!\nTo advance to the next level, you need **{xp_to_next_in_announcement}** exp."

                        embed = discord.Embed(title=embed_title,
                                            description=embed_description,
                                            colour=discord.Color.gold(),
                                            timestamp=discord.utils.utcnow())
                        
                        embed.set_footer(text="Chaaat", icon_url=message.author.display_avatar.url)

                        await channel.send(embed=embed)
                
                else:
                    xp_gain = 0
                    if not boosted_channels or message.channel.id not in boosted_channels:
                        xp_gain = 1
                    else:
                        xp_gain = 2
                    user_data['experience'] = int(current_xp + xp_gain)
                    with open(user_data_path, 'w') as json_file:
                        json.dump(user_data, json_file, indent=4)

        if autodelete_enabled is True:
            async def autodelete():
                if message.channel.id in config['features']['message_autodelete'].get('channels_id'):
                    await asyncio.sleep(60*autodelete_duration)
                    await message.delete()
        
            self.client.loop.create_task(autodelete())
        
        if bump_reminder_enabled is True:
            if message.author.id == 302050872383242240:
                async def reminder():
                    channel = message.guild.get_channel(bump_reminder_channel_id)
                    await asyncio.sleep(7200)
                    if language == "fr":
                        await channel.send("📲 Il est l'heure de bumper le serveur")
                    else:
                        await channel.send("📲 It's time to bump the server")

                self.client.loop.create_task(reminder())

async def setup(client):
    await client.add_cog(OnMessage(client))