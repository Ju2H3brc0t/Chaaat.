from utils import DB_PATH, update_db, get_user_from_db, load_config, translate
import discord
from discord.ext import commands, tasks
import datetime
import aiosqlite

class BirthdayVerif(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.verif_birthday.start()

    def cog_unload(self):
        self.verif_birthday.cancel()
    
    @tasks.loop(time=datetime.time(hour=12, minute=0))
    async def verif_birthday(self):
        async def get_all_birhtdays():
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT user_id, guild_id, birthday FROM user_data WHERE birthday IS NOT NULL") as cursor:
                    return await cursor.fetchall()
        
        today = datetime.datetime.now().strftime("%d/%m")
        all_birthday = await get_all_birhtdays()

        for user_id, guild_id, bday in all_birthday:
            if bday == today:
                config = await load_config(guild_id=guild_id, auto_create=True)
                language = str(config['features'].get('language'))

                birthday_enabled = bool(config['features']['birthday'].get('enabled'))
                if birthday_enabled:
                    channel_id = int(config['features']['birthday'].get('channel_id'))
                    guild = self.client.get_guild(guild_id)
                    if not guild: continue

                    channel = guild.get_channel(channel_id)
                    if channel:
                        embed_title = await translate(text=f"Happy Birthday !", dest_lng=language)
                        embed_description = await translate(text=f"🎉🎂 Today we wish an happy birthday to <span class=notranslate><@{user_id}></span>", dest_lng=language)

                        embed = discord.Embed(
                            title=embed_title,
                            description=embed_description,
                            color=discord.Color.pink(),
                            timestamp=discord.utils.utcnow())
                        
                        await channel.send(embed=embed)
                    
                    gift_enabled = bool(config['features']['birthday']["gift"].get('enabled'))
                    if gift_enabled:
                        xp = int(config['features']['birthday']['gift'].get('xp'))

                        if xp > 0:
                            current_xp = await get_user_from_db(data_to_get="xp", user_id=user_id, guild_id=guild_id)

                            await update_db(column="xp", value=current_xp+xp, user_id=user_id, guild_id=guild_id)
    
    @verif_birthday.before_loop
    async def befor_verif(self):
        await self.client.wait_until_ready()

async def setup(client):
    await client.add_cog(BirthdayVerif(client))