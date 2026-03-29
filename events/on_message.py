from utils import update_db, get_user_from_db, load_config, load_data, translate
import discord
from discord.ext import commands
from simpleeval import SimpleEval
from decimal import Decimal
import requests
import asyncio
import json
import math
import os

class OnMessage(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.api_url = f"https://api.groq.com/openai/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {os.getenv('GROQ_TOKEN')}", "Content-Type": "application/json"}
        self.evaluator = None
    
    async def cog_load(self):
        self.evaluator = SimpleEval()
    
    async def check_active_tasks(self):
        await self.client.wait_until_ready()

        base_path = 'server_configs'
        if not os.path.exists(base_path): return

        for guild_id_str in os.listdir(base_path):
            guild_id = int(guild_id_str)
            data = await load_data(guild_id=guild_id, auto_create=True)
            data_path = f'server_configs/{guild_id}/data.json'
            config = await load_config(guild_id=guild_id, auto_create=True)
            language = str(config['features'].get('language'))

            end_time = data.get('next_bump', None)
            enabled = bool(config['features']['bump_reminder'].get('enabled'))
            channel_id = int(config['features']['bump_reminder'].get('channel'))
            channel = await self.client.fetch_channel(channel_id)

            if enabled and end_time != "Anytime":
                now = discord.utils.utcnow().timestamp()
                if end_time > now:
                    self.client.loop.create_task(self.start_bump_reminder(guild_id=guild_id, end_time=end_time, channel_id=channel_id, language=language))
                else:
                    embed_title = await translate(text="⏰ It's bump time !", dest_lng=language)
                    embed_description = await translate("Two hours passed since the last bump, you can bump the server again", dest_lng=language)

                    embed = discord.Embed(title=embed_title,
                        description=embed_description,
                        colour=discord.Color.blurple(),
                        timestamp=discord.utils.utcnow())
            
                    await channel.send(embed=embed)
                    data['next_bump'] = "Anytime"
                    with open(data_path, 'w') as f:
                        json.dump(data, f, indent=4)

    async def message_autodelete(self, message):
        config = await load_config(guild_id=message.guild.id, auto_create=True)

        autodelete_enabled = bool(config['features']['message_autodelete'].get('enabled'))
        autodelete_wait_duration = int(config['features']['message_autodelete'].get('wait'))

        if autodelete_enabled:
            async def autodelete():
                if message.channel.id in [int(cid) for cid in config['features']['message_autodelete'].get('channels_id')]:
                    await asyncio.sleep(autodelete_wait_duration)
                    try:
                        await message.delete()
                    except discord.NotFound:
                        pass
        
            self.client.loop.create_task(autodelete())

    async def bump_reminder(self, message):
        config = await load_config(guild_id=message.guild.id, auto_create=True)
        language = str(config['features'].get('language'))
        data = await load_data(guild_id=message.guild.id, auto_create=True)
        data_path = f'server_configs/{message.guild.id}/data.json'

        bump_reminder_enabled = bool(config['features']['bump_reminder'].get('enabled'))
        channel = int(config['features']['bump_reminder'].get('channel'))

        if message.author.id == 302050872383242240 and bump_reminder_enabled:
            end_time = discord.utils.utcnow().timestamp() + 7200

            data['next_bump'] = end_time
            with open(data_path, 'w') as f:
                json.dump(data, f, indent=4)
            
            self.client.loop.create_task(self.start_bump_reminder(guild_id=message.guild.id, end_time=end_time, channel_id=channel, language=language))

    async def start_bump_reminder(self, guild_id, end_time, channel_id, language):
        delay = end_time - discord.utils.utcnow().timestamp()
        await asyncio.sleep(delay)

        guild = await self.client.fetch_guild(guild_id)
        if guild:
            channel = await guild.fetch_channel(channel_id)
            if channel:
                data = await load_data(guild_id=guild_id, auto_create=True)
                data_path = f'server_configs/{guild_id}/data.json'

                embed_title = await translate(text="⏰ It's bump time !", dest_lng=language)
                embed_description = await translate(text="Two hours passed since the last bump, you can bump the server again", dest_lng=language)

                embed = discord.Embed(title=embed_title,
                    description=embed_description,
                    colour=discord.Color.blurple(),
                    timestamp=discord.utils.utcnow())
            
                await channel.send(embed=embed)
                data['next_bump'] = "Anytime"
                with open(data_path, 'w') as f:
                    json.dump(data, f, indent=4)

    async def query_ai(self, message, prompt):
        config = await load_config(guild_id=message.guild.id, auto_create=True)
        language = str(config['features'].get('language'))

        history = []
        async for msg in message.channel.history(limit=50, before=message):
            history.append({
                "role": "assistant",
                "content": f"{msg.author.display_name} : {msg.content}"
            })
            
        history.reverse()

        system_prompt = f"You are a bot on a Discord server, your username is '{str(self.client.user)[:-5]}'. A user is talking to you, reply to them. Here are some rules to help you: Reply directly and concisely (no more than 3 or 4 sentences), remain neutral and integrated into the conversation, NEVER use meta-comments like 'As an AI', 'Sure!', or 'Here is your answer', START your response immediately with the first word of your actual answer, NEVER prefix your response with your own name or username (for exemple do not write {str(self.client.user)[:-5]} : ...), respond directly without any prefix and always reply in the same language as the user's message."
        payload = {
            "model": "openai/gpt-oss-safeguard-20b",
            "messages": [
                {"role": "system", "content": system_prompt},
                *history,
                {"role": "user", "content": f"{message.author.display_name} : {prompt}"}
            ],
            "max_tokens": 250,
            "temperature": 0.5
        }
        response = await asyncio.to_thread(
            requests.post, self.api_url, headers = self.headers, json = payload, timeout = 15
        )
        return response.json()

    async def ai(self, message):
        config = await load_config(guild_id=message.guild.id, auto_create=True)
        language = str(config['features'].get('language'))

        if self.client.user.mentioned_in(message):
            user_prompt = message.content.replace(f'<@!{self.client.user.id}>', '').replace(f'<@{self.client.user.id}>', '').strip()

            if user_prompt:
                async with message.channel.typing():
                    try:
                        data = await self.query_ai(prompt=user_prompt, message=message)
                        if 'choices' in data:
                            answer = data['choices'][0]['message']['content'].strip()
                        else:
                            answer = await translate(text="⚠️ An unexpected error occured, please try again later...", dest_lng=language)
                            print(data)

                        if len(answer) > 2000:
                            answer = answer[:1990] + "..."
                        await message.reply(answer)
                    except Exception:
                        answer = await translate(text="⚠️ An unexpected error occured, please try again later...", dest_lng=language)
                        await message.reply(answer)

    async def leveling(self, message):
        config = await load_config(guild_id=message.guild.id, auto_create=True)
        language = str(config['features'].get('language'))

        leveling_enabled = bool(config['features']['leveling'].get('enabled'))
        exclude_channels = [int(channel) for channel in config['features']['leveling'].get('exclude_channels')]
        boost_channels = [int(channel) for channel in config['features']['leveling'].get('boost_channels')]
        current_level = await get_user_from_db(data_to_get="level", user_id=message.author.id, guild_id=message.guild.id)
        current_xp = await get_user_from_db(data_to_get="xp", user_id=message.author.id, guild_id=message.guild.id)
        xp = current_xp
        xp_required = 5*(current_level**2)
        rewards = config['features']['leveling'].get('rewards')
        stackable = config['features']['leveling'].get('rewards_stackable')
        channel_id = int(config['features']['leveling'].get('announcement_channel_id'))
        channel = message.guild.get_channel(channel_id)

        if leveling_enabled and not message.author.bot:
            if not message.channel.id in exclude_channels and not message.channel.id in boost_channels: 
                await update_db(column="xp", value=current_xp + 1, user_id=message.author.id, guild_id=message.guild.id)
                xp = current_xp + 1
            elif not message.channel.id in exclude_channels and message.channel.id in boost_channels: 
                await update_db(column="xp", value=current_xp + 2, user_id=message.author.id, guild_id=message.guild.id)
                xp = current_xp + 2
            if xp >= xp_required:
                await update_db(column="level", value=current_level + 1, user_id=message.author.id, guild_id=message.guild.id)
                role_id = rewards.get(str(current_level + 1)) or rewards.get(current_level + 1)
                if role_id:
                    role = message.guild.get_role(int(role_id))
                    if role:
                        if stackable:
                            await message.author.add_roles(role)
                        else:
                            previous_rewards_id = [int(rid) for lvl, rid in rewards.items() if int(lvl) != current_level + 1]
                            roles_to_remove = [role for role in message.author.roles if role.id in previous_rewards_id]
                            await message.author.remove_roles(*roles_to_remove)
                            await message.author.add_roles(role)
                        embed_title = await translate(text="🎉 New level reached !", dest_lng=language)
                        embed_description_first_part = await translate(text="Congratulation", dest_lng=language)
                        embed_description_second_part = await translate(text=", you reached level **{level}** and have earned the role", dest_lng=language)
                        embed_description_second_part = embed_description_second_part.format(level=current_level+1)
                        embed_description_third_part = await translate(text="To advance to the next level you need **{need}** more experience points", dest_lng=language)
                        embed_description_third_part = embed_description_third_part.format(need=5*((current_level+1)**2))
                        embed_description = f'{embed_description_first_part} {message.author.mention}{embed_description_second_part} {role.mention} !\n{embed_description_third_part}'

                        embed = discord.Embed(title=embed_title,
                            description=embed_description,
                            colour=discord.Color.gold(),
                            timestamp=discord.utils.utcnow())
                        
                        embed.set_footer(text="Chaaat", icon_url=message.author.display_avatar.url)

                        await channel.send(embed=embed)

                        return
                else:
                    embed_title = await translate(text="🎉 New level reached !", dest_lng=language)
                    embed_description_first_part = await translate(text="Congratulation", dest_lng=language)
                    embed_description_second_part = await translate(text=", you reached level **{level}**", dest_lng=language)
                    embed_description_second_part = embed_description_second_part.format(level=current_level+1)
                    embed_description_third_part = await translate(text="To advance to the next level you need **{need}** more experience points", dest_lng=language)
                    embed_description_third_part = embed_description_third_part.format(need=5*((current_level+1)**2))
                    embed_description = f'{embed_description_first_part} {message.author.mention}{embed_description_second_part} !\n{embed_description_third_part}'

                    embed = discord.Embed(title=embed_title,
                        description=embed_description,
                        colour=discord.Color.gold(),
                        timestamp=discord.utils.utcnow())

                    embed.set_footer(text="Chaaat", icon_url=message.author.display_avatar.url)

                    await channel.send(embed=embed)

    async def counting(self, message):
        config = await load_config(guild_id=message.guild.id, auto_create=True)
        language = str(config['features'].get('language'))
        data = await load_data(guild_id=message.guild.id, auto_create=True)
        data_path = f'server_configs/{message.guild.id}/data.json'

        counting_enabled = bool(config['features']['counting'].get('enabled'))
        channel_id = int(config['features']['counting'].get('channel_id'))
        checkpoints = bool(config['features']['counting'].get('checkpoints'))
        raw_count = data.get('counting', None)
        current_count = Decimal(str(raw_count)) if raw_count is not None else Decimal(0)
        raw_user = data.get('last_user_id')
        last_user_id = int(raw_user) if raw_user is not None else None

        s = SimpleEval()
        s.names = {
            "pi": Decimal("3.14159265358979323846"),
            "π": Decimal("3.14159265358979323846"),
            "e": Decimal("2.71828182845904523536"),
            "tau": Decimal("6.28318530717958647692"),
            "τ": Decimal("6.28318530717958647692"),
            "phi": Decimal("1.61803398874989484820"),
            "φ": Decimal("1.61803398874989484820"),
        }
        s.functions = {
            "sqrt": math.sqrt,
            "abs": abs,
            "fact": math.factorial,
            "cos": math.cos,
            "sin": math.sin,
            "bin": lambda x: int(str(int(x)), 2),
            "hex": lambda x: int(str(int(x)), 16)
        }

        if counting_enabled and channel_id == message.channel.id and not message.author.bot:
            if current_count == None:
                unexpected_error_message = await translate(text="⚠️ An unexpected error occured, please try again later...", dest_lng=language)
                await message.channel.send(unexpected_error_message)
                return 

            try:
                clean_content = message.content.strip().replace(",", ".").replace("`", "")
                result = await asyncio.wait_for(asyncio.to_thread(s.eval, clean_content), timeout=0.5)
                count = Decimal(str(result))

            except asyncio.TimeoutError:
                timeout_message = await translate(text="🥀 This calculation is too complex.\n-# Next number is {expected_count}.", dest_lng=language, expected_count=current_count+1)
                await message.channel.send(timeout_message)
                return
            except (ValueError, NameError, SyntaxError):
                return
            
            if current_count % 100 == 0:
                is_checkpoint = True
            else:
                is_checkpoint = False

            if (current_count + 1) % 100 == 0:
                will_be_checkpoint = True
            else:
                will_be_checkpoint = False

            previous_checkpoint = current_count - (current_count % 100)

            is_valid = current_count < count <= current_count+1

            if is_valid and message.author.id != last_user_id:
                await message.add_reaction("✅")
                if count == 100: await message.add_reaction("💯")
                if checkpoints and will_be_checkpoint: await message.add_reaction("🚩")
                data['counting'] = str(count)
                data['last_user_id'] = message.author.id
                with open(data_path, 'w') as f:
                    json.dump(data, f, indent=4)
            elif not is_valid or message.author.id == last_user_id:
                await message.add_reaction("❌")
                if checkpoints:
                    if is_checkpoint:
                        wrong_but_is_checkpoint = await translate(text="made a mistake, but the preceding number is a checkpoint.\n-# Next number is {expected_count}.", dest_lng=language, expected_count=current_count+1)
                        await message.channel.send(f"{message.author.mention} {wrong_but_is_checkpoint}")
                        data['counting'] = str(previous_checkpoint)
                        data['last_user_id'] = None
                        with open(data_path, 'w') as f:
                            json.dump(data, f, indent=4)
                        return
                    wrong_but_checkpoint = await translate(text="made a mistake, the counter has returned to the previous checkpoint.\n-# Next number is {previous_checkpoint}.", dest_lng=language, previous_checkpoint=previous_checkpoint+1)
                    await message.channel.send(f"{message.author.mention} {wrong_but_checkpoint}")
                    data['counting'] = str(previous_checkpoint)
                    data['last_user_id'] = None
                    with open(data_path, 'w') as f:
                        json.dump(data, f, indent=4)
                else:
                    wrong_message = await translate(text=f"made a mistake, the counter has been reset.\n-# Next number is 1.", dest_lng=language)
                    await message.channel.send(f"{message.author.mention} {wrong_message}")
                    data['counting'] = str(0)
                    data['last_user_id'] = None
                    with open(data_path, 'w') as f:
                        json.dump(data, f, indent=4)
            else:
                await message.add_reaction("❓")
                unexpected_error_message = await translate(text="⚠️ An unexpected error occured, please try again later...", dest_lng=language)
                await message.channel.send(unexpected_error_message)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        await self.counting(message=message)
        await self.leveling(message=message)
        await self.ai(message=message)
        await self.message_autodelete(message=message)
        await self.bump_reminder(message=message)
        
async def setup(client):
    await client.add_cog(OnMessage(client))