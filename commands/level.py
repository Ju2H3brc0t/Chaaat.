from utils import DB_PATH, load_config, get_user_from_db, translate
import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite

class Level(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    async def get_user_rank(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_PATH) as db:
            query = '''
                SELECT COUNT(*) + 1
                FROM user_data
                WHERE guild_id = ? AND xp > (
                    SELECT xp FROM user_data WHERE user_id = ? AND guild_id = ?
                )
            '''
            async with db.execute(query, (interaction.guild_id, interaction.user.id, interaction.guild_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                return 0

    async def get_leaderboard(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_PATH) as db:
            query = '''
                SELECT user_id, xp, level
                FROM user_data
                WHERE guild_id = ?
                ORDER BY xp DESC
                LIMIT 10
            '''

            async with db.execute(query, (interaction.guild_id,)) as cursor:
                return await cursor.fetchall()

    level_group = app_commands.Group(name="level", description="Commands about the leveling system")

    @level_group.command(name="rank", description="Get your level, your point and your position in the rankings")
    async def rank(self, interaction: discord.Interaction):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))

        level_enabled = bool(config['features']['leveling'].get('enabled'))

        if level_enabled:
            await interaction.response.defer(ephemeral=True)

            current_lvl = await get_user_from_db(data_to_get="level", user_id=interaction.user.id, guild_id=interaction.guild_id)
            current_xp = await get_user_from_db(data_to_get="xp", user_id=interaction.user.id, guild_id=interaction.guild_id)
            xp_required = 5*(current_lvl**2)
            xp_to_next = xp_required - current_xp
            rank = await self.get_user_rank(interaction)

            embed_title = await translate(text="📊 Level and Experience", dest_lng=language)
            embed_desciption = await translate(text="You are currently at level **{current_lvl}** with **{current_xp}** points.\nTo advance to the next level you need **{xp_to_next}** more experience points.\n\nYour currently number **{rank}** at the the rankings.", dest_lng=language, current_lvl=current_lvl, current_xp=current_xp, xp_to_next=xp_to_next, rank=rank)

            embed = discord.Embed(title=embed_title,
                description=embed_desciption,
                color=discord.Color.gold())
        
            embed.set_footer(text="Chaaat", icon_url=interaction.user.display_avatar.url)

            await interaction.followup.send(embed=embed)
        else:
            not_activated_message = await translate(text="🧩 This feature is disabled on this server.", dest_lng=language)
            await interaction.response.send_message(not_activated_message)
    
    @level_group.command(name="leaderboard", description="Get the experience leaderboard of the server")
    async def leaderboard(self, interaction: discord.Interaction):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))

        level_enabled = bool(config['features']['leveling'].get('enabled'))

        if level_enabled:
            await interaction.response.defer(ephemeral=True)

            top_players = await self.get_leaderboard(interaction)

            if not top_players:
                no_data_message = await translate(text="⁉️ No data available for now, please try again later...", dest_lng=language)
                await interaction.followup.send(no_data_message, ephemeral=True)
                return
        
            description = ""
            for index, (user_id, xp, level) in enumerate(top_players, start=1):
                guild = interaction.guild
                member = await guild.fetch_member(user_id)
                description_first_part = f"**{index}.** {member.mention} -"
                description_second_part = await translate(text="**Level {level} ({xp} XP)**", dest_lng=language, level=level, xp=xp)
                description += f"{description_first_part} {description_second_part}\n"
        
            embed_title = await translate(text="🏆 Leaderboard for the server", dest_lng=language)

            embed = discord.Embed(
                title=f"{embed_title} {interaction.guild.name}",
                description=description,
                color=discord.Color.gold())
        
            footer_text = await translate(text="Keep discussing to climb the rankings !", dest_lng=language)
            embed.set_footer(text=footer_text)

            await interaction.followup.send(embed=embed)
        
        else:
            not_activated_message = await translate(text="🧩 This feature is disabled on this server.", dest_lng=language)
            await interaction.response.send_message(not_activated_message)

async def setup(client):
    await client.add_cog(Level(client))