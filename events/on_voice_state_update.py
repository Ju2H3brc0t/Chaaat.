from utils import update_db, get_user_from_db, load_config, translate
import discord
from discord.ext import commands, tasks
import time

class OnVoiceStateUpdate(commands.Cog):
    def __init__(self, client):
        self.client = client
        self._voice_join_times: dict[tuple[int, int], float] = {}
        self._afk_since: dict[tuple[int, int], float] = {}
        self.voice_xp_loop.start()
        self.afk_check_loop.start()

    def cog_unload(self):
        self.voice_xp_loop.cancel()
        self.afk_check_loop.cancel()


    def _is_muted(self, member: discord.Member) -> bool:
        """Micro coupé (self ou serveur)."""
        v = member.voice
        return bool(v and (v.self_mute or v.mute))

    def _is_deafened(self, member: discord.Member) -> bool:
        """Sourdine (self ou serveur)."""
        v = member.voice
        return bool(v and (v.self_deaf or v.deaf))

    def _is_afk(self, member: discord.Member, config: dict) -> bool:
        """Retourne True si le membre doit être considéré AFK selon la config."""
        stop_on_mute     = bool(config['features']['leveling'].get('voice_stop_on_mute', False))
        stop_on_deafened = bool(config['features']['leveling'].get('voice_stop_on_deafened', False))

        muted    = self._is_muted(member)
        deafened = self._is_deafened(member)

        if stop_on_mute and stop_on_deafened:
            return muted or deafened
        if stop_on_mute:
            return muted
        if stop_on_deafened:
            return deafened
        return False

    def _is_eligible_for_xp(self, member: discord.Member, config: dict) -> bool:
        """Retourne True si le membre peut gagner de l'XP vocal en ce moment."""
        if member.bot:
            return False
        v = member.voice
        if not v or not v.channel:
            return False
        if self._is_afk(member, config):
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
            self._afk_since.pop(key, None)

        if after.channel is not None and self._is_afk(member, config):
            if key in self._voice_join_times:
                elapsed = time.time() - self._voice_join_times.pop(key)
                await self._grant_voice_xp(member, elapsed, config)
            if key not in self._afk_since:
                self._afk_since[key] = time.time()

        if after.channel is not None and not self._is_afk(member, config):
            self._afk_since.pop(key, None)
            if self._is_eligible_for_xp(member, config) and key not in self._voice_join_times:
                self._voice_join_times[key] = time.time()

        if after.channel is not None:
            humans_after = [m for m in after.channel.members if not m.bot]
            if len(humans_after) >= 2:
                for m in after.channel.members:
                    if m.bot or m.id == member.id:
                        continue
                    k = (member.guild.id, m.id)
                    if self._is_eligible_for_xp(m, config) and k not in self._voice_join_times:
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

            if not self._is_eligible_for_xp(member, config):
                if key in self._voice_join_times:
                    elapsed = now - self._voice_join_times.pop(key)
                    await self._grant_voice_xp(member, elapsed, config)
                continue

            interval = int(config['features']['leveling'].get('voice_xp_interval_seconds', 60))
            elapsed  = now - self._voice_join_times[key]

            if elapsed >= interval:
                self._voice_join_times[key] = now
                await self._grant_voice_xp(member, interval, config)

    @voice_xp_loop.before_loop
    async def before_voice_xp_loop(self):
        await self.client.wait_until_ready()


    @tasks.loop(seconds=30)
    async def afk_check_loop(self):
        now = time.time()
        for key in list(self._afk_since.keys()):
            guild_id, user_id = key
            guild = self.client.get_guild(guild_id)
            if not guild:
                self._afk_since.pop(key, None)
                continue

            member = guild.get_member(user_id)
            if not member or not member.voice or not member.voice.channel:
                self._afk_since.pop(key, None)
                continue

            config = await load_config(guild_id=guild_id, auto_create=True)

            if not bool(config['features']['leveling'].get('voice_afk_enabled', False)):
                self._afk_since.pop(key, None)
                continue

            if not self._is_afk(member, config):
                self._afk_since.pop(key, None)
                continue

            afk_delay   = int(config['features']['leveling'].get('voice_afk_delay_minutes', 10)) * 60
            afk_channel_id = config['features']['leveling'].get('voice_afk_channel_id', None)

            if now - self._afk_since[key] >= afk_delay:
                self._afk_since.pop(key, None)
                if afk_channel_id:
                    afk_channel = guild.get_channel(int(afk_channel_id))
                    if afk_channel and member.voice.channel != afk_channel:
                        try:
                            await member.move_to(afk_channel)
                        except discord.Forbidden:
                            print(f"[VoiceAFK] Permission manquante pour déplacer {member}.")
                        except discord.HTTPException as e:
                            print(f"[VoiceAFK] Erreur HTTP : {e}")

    @afk_check_loop.before_loop
    async def before_afk_check_loop(self):
        await self.client.wait_until_ready()


    async def _grant_voice_xp(self, member: discord.Member, elapsed_seconds: float, config: dict):
        try:
            language        = str(config['features'].get('language'))
            xp_per_interval = int(config['features']['leveling'].get('voice_xp_per_interval', 1))
            interval        = int(config['features']['leveling'].get('voice_xp_interval_seconds', 60))

            xp_gain = max(1, round(xp_per_interval * (elapsed_seconds / interval))) if elapsed_seconds >= (interval * 0.5) else 0

            if xp_gain <= 0:
                return

            current_xp    = await get_user_from_db(data_to_get="xp",    user_id=member.id, guild_id=member.guild.id)
            current_level = await get_user_from_db(data_to_get="level", user_id=member.id, guild_id=member.guild.id)
            new_xp        = current_xp + xp_gain
            xp_required   = 5 * (current_level ** 2)

            await update_db(column="xp", value=new_xp, user_id=member.id, guild_id=member.guild.id)

            if new_xp >= xp_required:
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
            print(f"[VoiceXP] Erreur : {e}")
            import traceback
            traceback.print_exc()


async def setup(client):
    await client.add_cog(OnVoiceStateUpdate(client))