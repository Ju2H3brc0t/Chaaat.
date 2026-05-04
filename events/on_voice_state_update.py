from utils import update_db, get_user_from_db, load_config, translate
import discord
from discord.ext import commands, tasks
import time

class OnVoiceStateUpdate(commands.Cog):
    def __init__(self, client):
        self.client = client
        self._voice_join_times: dict[tuple[int, int], float] = {}
        self.voice_xp_loop.start()

    def cog_unload(self):
        self.voice_xp_loop.cancel()

    def _is_afk(self, member: discord.Member) -> bool:
        v = member.voice
        if not v:
            return False
        return v.self_mute or v.mute or v.self_deaf or v.deaf

    def _is_eligible_for_xp(self, member: discord.Member) -> bool:
        if member.bot:
            return False
        v = member.voice
        if not v or not v.channel:
            return False
        if self._is_afk(member):
            return False
        humans = [m for m in v.channel.members if not m.bot]
        return len(humans) >= 2

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.bot:
            return

        config = await load_config(guild_id=member.guild.id, auto_create=True)
        if not bool(config['features']['leveling'].get('enabled')):
            return
        if not bool(config['features']['leveling'].get('voice_xp_enabled', False)):
            return

        key = (member.guild.id, member.id)

        if before.channel is not None and (after.channel is None or before.channel != after.channel):
            if key in self._voice_join_times:
                elapsed = time.time() - self._voice_join_times.pop(key)
                await self._grant_voice_xp(member, elapsed, config)

        if after.channel is not None and self._is_afk(member):
            if key in self._voice_join_times:
                elapsed = time.time() - self._voice_join_times.pop(key)
                await self._grant_voice_xp(member, elapsed, config)
        if after.channel is not None and not self._is_afk(member):
            if self._is_eligible_for_xp(member) and key not in self._voice_join_times:
                self._voice_join_times[key] = time.time()

        if after.channel is not None:
            humans_after = [m for m in after.channel.members if not m.bot]
            if len(humans_after) >= 2:
                for m in after.channel.members:
                    if m.bot or m.id == member.id:
                        continue
                    k = (member.guild.id, m.id)
                    if self._is_eligible_for_xp(m) and k not in self._voice_join_times:
                        self._voice_join_times[k] = time.time()

        if before.channel is not None:
            humans_before = [m for m in before.channel.members if not m.bot]
            if len(humans_before) < 2:
                for m in before.channel.members:
                    if m.bot:
                        continue
                    k = (member.guild.id, m.id)
                    if k in self._voice_join_times:
                        elapsed = time.time() - self._voice_join_times.pop(k)
                        await self._grant_voice_xp(m, elapsed, config)

    @tasks.loop(seconds=1)
    async def voice_xp_loop(self):
        now = time.time()
        for key in list(self._voice_join_times.keys()):
            guild_id, user_id = key
            guild = self.client.get_guild(guild_id)
            if not guild:
                self._voice_join_times.pop(key, None)
                continue

            member = guild.get_member(user_id)
            if not member:
                self._voice_join_times.pop(key, None)
                continue

            config = await load_config(guild_id=guild_id, auto_create=True)

            if not bool(config['features']['leveling'].get('enabled')):
                self._voice_join_times.pop(key, None)
                continue
            if not bool(config['features']['leveling'].get('voice_xp_enabled', False)):
                self._voice_join_times.pop(key, None)
                continue

            if not self._is_eligible_for_xp(member):
                elapsed = now - self._voice_join_times.pop(key)
                await self._grant_voice_xp(member, elapsed, config)
                continue

            interval = int(config['features']['leveling'].get('voice_xp_interval_seconds', 120))
            elapsed  = now - self._voice_join_times[key]

            if elapsed >= interval:
                self._voice_join_times[key] = now
                await self._grant_voice_xp(member, interval, config)

    @voice_xp_loop.before_loop
    async def before_voice_xp_loop(self):
        await self.client.wait_until_ready()

    async def _grant_voice_xp(self, member: discord.Member, elapsed_seconds: float, config: dict):
        try:
            language  = str(config['features'].get('language'))
            interval  = int(config['features']['leveling'].get('voice_xp_interval_seconds', 120))

            xp_gain = 1 if elapsed_seconds >= (interval * 0.5) else 0

            if xp_gain <= 0:
                return

            current_xp    = await get_user_from_db(data_to_get="xp",    user_id=member.id, guild_id=member.guild.id)
            current_level = await get_user_from_db(data_to_get="level", user_id=member.id, guild_id=member.guild.id)
            xp            = current_xp + xp_gain
            xp_required   = 5*(current_level**2)

            await update_db(column="xp", value=xp, user_id=member.id, guild_id=member.guild.id)

            if xp >= xp_required:
                new_level  = current_level + 1
                await update_db(column="level", value=new_level, user_id=member.id, guild_id=member.guild.id)

                rewards    = config['features']['leveling'].get('rewards')
                stackable  = config['features']['leveling'].get('rewards_stackable')
                channel_id = int(config['features']['leveling'].get('announcement_channel_id'))
                channel    = member.guild.get_channel(channel_id)
                role_id    = rewards.get(str(new_level)) or rewards.get(new_level)

                if role_id:
                    role = member.guild.get_role(int(role_id))
                    if role:
                        if stackable:
                            await member.add_roles(role)
                        else:
                            prev_ids = [int(rid) for lvl, rid in rewards.items() if int(lvl) != new_level]
                            await member.remove_roles(*[r for r in member.roles if r.id in prev_ids])
                            await member.add_roles(role)

                        if channel:
                            t1 = await translate(text="🎉 New level reached !", dest_lng=language)
                            p1 = await translate(text="Congratulation", dest_lng=language)
                            p2 = await translate(text=", you reached level **{level}** and earned the role", dest_lng=language, level=new_level)
                            p3 = await translate(text="To advance to the next level you need **{need}** more experience points", dest_lng=language, need=5*(new_level**2))
                            p4 = await translate(text="*(thanks to your time in voice channels 🎙️)*", dest_lng=language)
                            embed = discord.Embed(title=t1, description=f"{p1} {member.mention}{p2} {role.mention} !\n{p3}\n{p4}", colour=discord.Color.gold(), timestamp=discord.utils.utcnow())
                            embed.set_footer(text="Chaaat", icon_url=member.display_avatar.url)
                            await channel.send(embed=embed)
                else:
                    if channel:
                        t1 = await translate(text="🎉 New level reached !", dest_lng=language)
                        p1 = await translate(text="Congratulation", dest_lng=language)
                        p2 = await translate(text=", you reached level **{level}**", dest_lng=language, level=new_level)
                        p3 = await translate(text="To advance to the next level you need **{need}** more experience points", dest_lng=language, need=5*(new_level**2))
                        p4 = await translate(text="*(thanks to your time in voice channels 🎙️)*", dest_lng=language)
                        embed = discord.Embed(title=t1, description=f"{p1} {member.mention}{p2} !\n{p3}\n{p4}", colour=discord.Color.gold(), timestamp=discord.utils.utcnow())
                        embed.set_footer(text="Chaaat", icon_url=member.display_avatar.url)
                        await channel.send(embed=embed)

        except Exception as e:
            import traceback
            traceback.print_exc()


async def setup(client):
    await client.add_cog(OnVoiceStateUpdate(client))



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