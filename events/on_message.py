from utils import update_db, get_user_from_db, load_config, load_data, translate
import discord
from discord.ext import commands
from simpleeval import SimpleEval
from decimal import Decimal
import decancer_py as decancer
import requests
import asyncio
import json
import math
import os
import re

class OnMessage(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.api_url = f"https://api.groq.com/openai/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {os.getenv('GROQ_TOKEN')}", "Content-Type": "application/json"}
        self.evaluator = None
        self.counting_lock = asyncio.Lock()
    
    async def cog_load(self):
        self.evaluator = SimpleEval()
    
    async def automod_words(self, message, config, language):
        banned_words = config['features']['automod'].get('banned_words', [])
        if not banned_words:
            return False

        decancered_content = str(decancer.parse(message.content)).lower()

        for word in banned_words:
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            if re.search(pattern, decancered_content):
                try:
                    await message.delete()
                    
                    alert_text = await translate(text="⚠️ Your message contained a prohibited word and has been deleted.", dest_lng=language)
                    await message.channel.send(f"{message.author.mention}, {alert_text}", delete_after=5)
                    return True
                except discord.Forbidden:
                    pass
        return False

    async def automod_links(self, message, config, language):
        links_config = config['features']['automod'].get('banned_links', {})
        
        filter_all = bool(links_config.get('all', False))
        filter_discord = bool(links_config.get('discord_invites', False))
        custom_blacklist = links_config.get('others', [])

        urls = re.findall(r'(https?://[^\s]+)', message.content.lower())
        if not urls:
            return False

        trigger_link = False

        if filter_all:
            trigger_link = True
        elif filter_discord:
            for url in urls:
                if "discord.gg" in url or "discord.com/invite" in url:
                    trigger_link = True
                    break

        if not trigger_link and custom_blacklist:
            for url in urls:
                if any(domain.lower() in url for domain in custom_blacklist):
                    trigger_link = True
                    break

        if trigger_link:
            try:
                await message.delete()
                
                alert_text = await translate(text="⚠️ Links are not allowed here.", dest_lng=language)
                await message.channel.send(f"{message.author.mention}, {alert_text}", delete_after=5)
                return True
            except discord.Forbidden:
                pass

        return False

    async def automod(self, message):
        if message.author.bot:
            return False

        config = await load_config(guild_id=message.guild.id, auto_create=True)
        language = str(config['generals'].get('language', 'en'))

        if not config['generals']['staff'].get('use_discord_permissions', False):
            staff_ids = set(config['generals']['staff'].get('manage_tickets', [])) | set(config['generals']['staff'].get('moderate_users', []))
            is_staff = str(message.author.id) in staff_ids
        else:
            is_staff = message.author.guild_permissions.manage_messages or message.author.guild_permissions.moderate_members

        if is_staff:
            return False

        if await self.automod_words(message, config, language):
            return True
        if await self.automod_links(message, config, language):
            return True

        return False

    async def send_bump_message(self, channel, config, language):
        translated_phrase = await translate(text="It's time to do", dest_lng=language)
        ping_id = config['features']['bump_reminder'].get('ping', None)
        
        ping_str = ""
        if ping_id:
            if str(ping_id).lower() in ["everyone", "here"]:
                ping_str = f"@{ping_id}"
            else:
                ping_str = f"<@&{ping_id}>"

        final_message = f"**{translated_phrase} !** </bump:302050872383242240>\n> {ping_str}".strip()
        await channel.send(content=final_message)

    async def check_active_tasks(self):
        await self.client.wait_until_ready()

        base_path = 'server_configs'
        if not os.path.exists(base_path): return

        for guild_id_str in os.listdir(base_path):
            try:
                guild_id = int(guild_id_str)
            except ValueError:
                continue
                
            data = await load_data(guild_id=guild_id, auto_create=True)
            data_path = f'server_configs/{guild_id}/data.json'
            config = await load_config(guild_id=guild_id, auto_create=True)
            
            language = str(config['features'].get('language', config['generals'].get('language', 'en')))
            end_time = data.get('next_bump', None)
            enabled = bool(config['features']['bump_reminder'].get('enabled'))
            
            if enabled and end_time != "Anytime" and end_time:
                channel_id = int(config['features']['bump_reminder'].get('channel'))
                try:
                    channel = self.client.get_channel(channel_id) or await self.client.fetch_channel(channel_id)
                except Exception:
                    continue

                now = discord.utils.utcnow().timestamp()
                if end_time > now:
                    self.client.loop.create_task(self.start_bump_reminder(guild_id=guild_id, end_time=end_time, channel_id=channel_id, language=language))
                else:
                    await self.send_bump_message(channel=channel, config=config, language=language)
                    data['next_bump'] = "Anytime"
                    with open(data_path, 'w') as f:
                        json.dump(data, f, indent=4)

    async def bump_reminder(self, message):
        config = await load_config(guild_id=message.guild.id, auto_create=True)
        language = str(config['features'].get('language', config['generals'].get('language', 'en')))
        data = await load_data(guild_id=message.guild.id, auto_create=True)
        data_path = f'server_configs/{message.guild.id}/data.json'

        bump_reminder_enabled = bool(config['features']['bump_reminder'].get('enabled'))
        channel_id = int(config['features']['bump_reminder'].get('announcement_channel_id'))

        if message.author.id == 302050872383242240 and bump_reminder_enabled:
            end_time = discord.utils.utcnow().timestamp() + 7200
            data['next_bump'] = end_time
            with open(data_path, 'w') as f:
                json.dump(data, f, indent=4)
            
            self.client.loop.create_task(self.start_bump_reminder(guild_id=message.guild.id, end_time=end_time, channel_id=channel_id, language=language))

    async def start_bump_reminder(self, guild_id, end_time, channel_id, language):
        delay = end_time - discord.utils.utcnow().timestamp()
        if delay > 0:
            await asyncio.sleep(delay)

        guild = self.client.get_guild(guild_id) or await self.client.fetch_guild(guild_id)
        if guild:
            channel = self.client.get_channel(channel_id) or await guild.fetch_channel(channel_id)
            if channel:
                config = await load_config(guild_id=guild_id, auto_create=True)
                data = await load_data(guild_id=guild_id, auto_create=True)
                data_path = f'server_configs/{guild_id}/data.json'

                await self.send_bump_message(channel=channel, config=config, language=language)
                data['next_bump'] = "Anytime"
                with open(data_path, 'w') as f:
                    json.dump(data, f, indent=4)

    async def message_autodelete(self, message):
        config = await load_config(guild_id=message.guild.id, auto_create=True)

        autodelete_enabled = bool(config['features']['message_autodelete'].get('enabled'))
        autodelete_wait_duration = int(config['features']['message_autodelete'].get('wait'))

        if autodelete_enabled:
            async def autodelete():
                if message.channel.id in [int(cid) for cid in config['features']['message_autodelete'].get('channels_ids')]:
                    await asyncio.sleep(autodelete_wait_duration)
                    try:
                        await message.delete()
                    except discord.NotFound:
                        pass
        
            self.client.loop.create_task(autodelete())

    async def query_ai(self, message, prompt, system_prompt, groq_token):
        headers = {
            "Authorization": f"Bearer {groq_token}", 
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openai/gpt-oss-safeguard-20b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 250,
            "temperature": 0.5
        }

        response = await asyncio.to_thread(
            requests.post, self.api_url, headers=headers, json=payload, timeout=15
        )
        return response.json()

    async def ai(self, message):
        if message.author.bot or message.mention_everyone or message.role_mentions:
            return
            
        if not self.client.user.mentioned_in(message):
            return

        config = await load_config(guild_id=message.guild.id, auto_create=True)
        language = str(config['generals'].get('language', 'en'))
        
        ai_config = config['features'].get('ai', {})
        enabled = bool(ai_config.get('enabled', False))

        if enabled:
            user_prompt = message.content.replace(f'<@!{self.client.user.id}>', '').replace(f'<@{self.client.user.id}>', '').strip()

            if user_prompt:
                async with message.channel.typing():
                    try:
                        groq_token = ai_config.get('groq_token', '')
                        system_prompt = ai_config.get('prompt', 'You are a helpful assistant.')

                        data = await self.query_ai(
                            message=message, 
                            prompt=user_prompt, 
                            system_prompt=system_prompt, 
                            groq_token=groq_token
                        )
                        
                        if 'choices' in data and len(data['choices']) > 0:
                            answer = data['choices'][0]['message']['content'].strip()
                            
                            if len(answer) > 2000:
                                answer = answer[:1995] + "..."
                            await message.reply(answer)
                        else:
                            answer = await translate(text="⚠️ An unexpected error occured, please try again later...", dest_lng=language)
                            await message.reply(answer)
                            print(f"[IA Erreur API] : {data}")

                    except Exception as e:
                        answer = await translate(text="⚠️ An unexpected error occured, please try again later...", dest_lng=language)
                        await message.reply(answer)
                        print(f"[IA Erreur Exception] : {e}")

    async def leveling(self, message):
        config = await load_config(guild_id=message.guild.id, auto_create=True)
        language = str(config['features'].get('language', config['generals'].get('language', 'en')))

        leveling_config = config['features'].get('leveling', {})
        chats_config = leveling_config.get('chats', {})
        
        leveling_enabled = bool(chats_config.get('enabled', False))
        exclude_channels = [int(channel) for channel in chats_config.get('excluded_channels_ids', [])]
        boost_channels = [int(channel) for channel in chats_config.get('boosted_channels_ids', [])]
        
        if not leveling_enabled or message.author.bot:
            return

        current_level = await get_user_from_db(data_to_get="level", user_id=message.author.id, guild_id=message.guild.id)
        current_xp = await get_user_from_db(data_to_get="xp", user_id=message.author.id, guild_id=message.guild.id)
        
        xp = current_xp
        xp_required = 5 * (current_level ** 2)
        xp_per_message = int(chats_config.get('xp_per_messages', 1))
        
        if message.channel.id in exclude_channels:
            return
            
        if message.channel.id in boost_channels:
            xp_per_message *= 2
            
        xp += xp_per_message
        await update_db(column="xp", value=xp, user_id=message.author.id, guild_id=message.guild.id)

        if xp >= xp_required:
            new_level = current_level + 1
            await update_db(column="level", value=new_level, user_id=message.author.id, guild_id=message.guild.id)
            await update_db(column="xp", value=0, user_id=message.author.id, guild_id=message.guild.id)

            rewards = leveling_config.get('rewards', {})
            stackable = bool(leveling_config.get('rewards_stackable', False))
            channel_id = int(leveling_config.get('announcement_channel_id'))
            
            channel = self.client.get_channel(channel_id) or message.channel
            try:
                if not channel and channel_id:
                    channel = await self.client.fetch_channel(channel_id)
            except Exception:
                channel = message.channel

            role_id = rewards.get(str(new_level)) or rewards.get(new_level)
            role = message.guild.get_role(int(role_id)) if role_id else None

            if role:
                try:
                    if stackable:
                        await message.author.add_roles(role)
                    else:
                        previous_rewards_id = [int(rid) for lvl, rid in rewards.items() if int(lvl) != new_level]
                        roles_to_remove = [r for r in message.author.roles if r.id in previous_rewards_id]
                        if roles_to_remove:
                            await message.author.remove_roles(*roles_to_remove)
                        await message.author.add_roles(role)
                except discord.Forbidden:
                    pass

            next_xp_required = 5 * (new_level ** 2)
            
            embed_title = await translate(text="🎉 New level reached !", dest_lng=language)

            if role:
                raw_text = leveling_config.get('text_reward')
                embed_description = raw_text.format(
                    user=message.author.mention,
                    member=message.author.mention,
                    level=new_level,
                    role=role.mention,
                    need=next_xp_required
                )
            else:
                raw_text = leveling_config.get('text')
                embed_description = raw_text.format(
                    user=message.author.mention,
                    member=message.author.mention,
                    level=new_level,
                    need=next_xp_required
                )

            embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                colour=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="Chaaat", icon_url=message.author.display_avatar.url)
            
            await channel.send(embed=embed)

    async def counting(self, message):
        async with self.counting_lock:
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

            config = await load_config(guild_id=message.guild.id, auto_create=True)
            data = await load_data(guild_id=message.guild.id, auto_create=True)
            
            language = str(config.get('features', {}).get('language', config.get('generals', {}).get('language', 'en')))
            data_path = f'server_configs/{message.guild.id}/data.json'

            counting_config = config.get('features', {}).get('counting', {})
            counting_enabled = bool(counting_config.get('enabled', False))
            
            raw_channel_id = counting_config.get('channel_id')
            channel_id = int(raw_channel_id) if raw_channel_id else None
            checkpoints = bool(counting_config.get('checkpoints', False))
            
            raw_count = data.get('counting', None)
            current_count = Decimal(str(raw_count)) if raw_count is not None else Decimal(0)
            raw_user = data.get('last_user_id')
            last_user_id = int(raw_user) if raw_user is not None else None

            if counting_enabled and channel_id and channel_id == message.channel.id and not message.author.bot:
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
                elif not is_valid and message.author.id != last_user_id:
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
                elif message.author.id == last_user_id:
                    same_user_message = await translate(text="You can't count twice in a row.\n-# Next number is {expected_count}.", dest_lng=language, expected_count=current_count+1)
                    await message.channel.send(f"{message.author.mention}, {same_user_message}")
                else:
                    await message.add_reaction("❓")
                    unexpected_error_message = await translate(text="⚠️ An unexpected error occured, please try again later...", dest_lng=language)
                    await message.channel.send(unexpected_error_message)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild: return

        if await self.automod(message=message):
            return

        await self.counting(message=message)
        await self.leveling(message=message)
        await self.ai(message=message)
        await self.message_autodelete(message=message)
        await self.bump_reminder(message=message)
        
async def setup(client):
    await client.add_cog(OnMessage(client))