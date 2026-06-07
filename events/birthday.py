from utils import DB_PATH, update_db, get_user_from_db, load_config, translate
import discord
from discord.ext import commands, tasks
import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import aiosqlite
import ast

class BirthdayVerification(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.birthday_loop.start()

    def cog_unload(self):
        self.birthday_loop.cancel()
    
    async def cleanup_temporary_roles(self, guild_id: int):
        async def get_active_temporary_roles_for_guild():
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute(
                    "SELECT user_id, previous_temporary_gift FROM user_data WHERE guild_id = ? AND previous_temporary_gift IS NOT NULL", 
                    (guild_id,)
                ) as cursor:
                    return await cursor.fetchall()
                
        active_temp_roles = await get_active_temporary_roles_for_guild()
        guild = self.client.get_guild(guild_id)
        if not guild: return

        for user_id, roles_string in active_temp_roles:
            try:
                member = await guild.fetch_member(user_id)
            except discord.HTTPException:
                await update_db(column="previous_temporary_gift", value=None, user_id=user_id, guild_id=guild_id)
                continue
            
            if roles_string:
                roles_ids = ast.literal_eval(roles_string)
                roles_to_remove = [guild.get_role(rid) for rid in roles_ids if guild.get_role(rid)]

                if roles_to_remove:
                    try:
                        await member.remove_roles(*roles_to_remove)
                    except discord.Forbidden:
                        pass
                    await update_db(column="previous_temporary_gift", value=None, user_id=user_id, guild_id=guild_id)

    async def check_and_run_birthdays(self):
        async def get_all_birthdays():
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT user_id, guild_id, birthday, previous_birthday FROM user_data WHERE birthday IS NOT NULL") as cursor:
                    return await cursor.fetchall()

        all_birthday = await get_all_birthdays()
        guild_configs = {}

        for user_id, guild_id, bday, last_bday_year in all_birthday:
            if guild_id not in guild_configs:
                guild_configs[guild_id] = await load_config(guild_id=guild_id, auto_create=True)
            
            config = guild_configs[guild_id]
            
            timezone_str = config['generals'].get('timezone', 'UTC')
            try:
                tz = ZoneInfo(timezone_str)
            except ZoneInfoNotFoundError:
                tz = ZoneInfo('UTC')

            now_in_tz = datetime.datetime.now(tz)
            current_hour = now_in_tz.hour
            current_year = now_in_tz.year
            today_in_tz = now_in_tz.strftime("%d/%m")

            if last_bday_year == current_year:
                continue

            if bday == today_in_tz and current_hour == 8:
                
                await self.cleanup_temporary_roles(guild_id)

                language = str(config['generals'].get('language'))
                birthday_enabled = bool(config['features']['birthday'].get('enabled'))
                
                if birthday_enabled:
                    channel_id = int(config['features']['birthday'].get('announcement_channel_id'))
                    guild = self.client.get_guild(guild_id)
                    if not guild: continue

                    channel = guild.get_channel(channel_id)
                    if channel:
                        try:
                            member = await guild.fetch_member(user_id)
                        except discord.HTTPException:
                            continue

                        embed_title = await translate(text="Happy Birthday !", dest_lng=language)
                        
                        config_text = config['features']['birthday'].get('text', "🎉🎂 Today we wish a happy birthday to {member}")
                        translated_text = await translate(text=config_text, dest_lng=language)
                        
                        embed_description = translated_text.replace("{member}", member.mention).replace("{guild}", guild.name)

                        embed = discord.Embed(
                            title=embed_title,
                            description=embed_description,
                            color=discord.Color.pink(),
                            timestamp=discord.utils.utcnow())
                        
                        await channel.send(embed=embed)
                    
                    gift_enabled = bool(config['features']['birthday']["gift"].get('enabled'))
                    if gift_enabled:
                        xp = int(config['features']['birthday']['gift'].get('xp'))
                        roles = [int(role) for role in config['features']['birthday']['gift'].get('roles', [])]
                        temporary_role = [int(role) for role in config['features']['birthday']['gift'].get('temporary_role', [])]

                        try:
                            user = await guild.fetch_member(user_id)
                        except discord.HTTPException:
                            continue

                        if xp > 0:
                            current_xp = await get_user_from_db(data_to_get="xp", user_id=user_id, guild_id=guild_id)
                            await update_db(column="xp", value=current_xp+xp, user_id=user_id, guild_id=guild_id)
                        
                        if roles:
                            roles_to_add = [guild.get_role(r) for r in roles if guild.get_role(r)]
                            try:
                                await user.add_roles(*roles_to_add)
                            except discord.Forbidden:
                                pass

                        if temporary_role:
                            roles_to_add = [guild.get_role(r) for r in temporary_role if guild.get_role(r)]
                            try:
                                await user.add_roles(*roles_to_add)
                            except discord.Forbidden:
                                pass
                            await update_db(column="previous_temporary_gift", value=str(temporary_role), user_id=user_id, guild_id=guild_id)

                await update_db(column="previous_birthday", value=current_year, user_id=user_id, guild_id=guild_id)

    @tasks.loop(hours=1)
    async def birthday_loop(self):
        await self.check_and_run_birthdays()

    @birthday_loop.before_loop
    async def before_verif(self):
        await self.client.wait_until_ready()

async def setup(client):
    await client.add_cog(BirthdayVerification(client))