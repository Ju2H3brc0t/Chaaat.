import discord
from discord.ext import commands
import yaml
import json

class on_message(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_message(self, message):
    
        if message.author.bot:
            return

        guild_id = message.guild.id
        config_path = f'server_configs/{guild_id}/config.yaml'
        data_path = f'server_configs/{guild_id}/data.json'

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

        counting_enabled = bool(config['features']['counting'].get('enabled'))
        reset_if_wrong_user = bool(config['features']['counting'].get('reset_if_wrong_user'))
        language = str(config['features']['language'].get('default'))

        if counting_enabled is True:
            channel_id = int(config['features']['counting']['channel_id'])
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
                    if language == "fr":
                        await message.channel.send(f"{message.author.mention}, vous ne pouvez pas compter deux nombres d'affilée !\n-# Le nombre suivant est {expected_count}.")
                    else:
                        await message.channel.send(f"{message.author.mention}, you cannot count two numbers in a row!\n-# Next number is {expected_count}.")
                    if reset_if_wrong_user == True:
                        data['counting'] = 0
                        data['last_user_id'] = 0
                        with open(data_path, 'w') as json_file:
                            json.dump(data, json_file, indent=4)
                    else:
                        await message.channel.send(f"{message.author.mention}, you cannot count two numbers in a row!\n-# Next number is {expected_count}.")
                elif user_count == expected_count == 100 and message.author.id != last_user_id:
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

async def setup(client):
    await client.add_cog(on_message(client))