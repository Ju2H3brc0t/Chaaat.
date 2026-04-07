from utils import update_db, get_user_from_db, load_config, translate
import discord
from discord import app_commands
from discord.ext import commands
import datetime
import re

class Mod(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def parse_duration(self, duration_str: str) -> datetime.timedelta:
        if duration_str.isdigit():
            return datetime.timedelta(minutes=int(duration_str))
        
        pattern = r'(\d+)([hms])'
        matches = re.findall(pattern, duration_str)

        if not matches:
            return datetime.timedelta(minutes=0)
        
        total_seconds = 0
        for value, unit in matches:
            value = int(value)
            if unit == 'h':
                total_seconds += value * 3600
            elif unit == "m":
                total_seconds += value * 60
            elif unit == "s":
                total_seconds += value

        return datetime.timedelta(seconds=total_seconds)

    staff_group = app_commands.Group(name="staff", description="Commands for moderators")

    @staff_group.command(name="warn", description="Warn a member")
    @app_commands.describe(member="The member you want to warn", reason="The reason why the member is warned")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))

        dm_message_first_part = await translate(text="You have been warned in", dest_lng=language)
        dm_message_second_part = await translate(text="Reason :", dest_lng=language)
        dm_message = f'🚫 {dm_message_first_part} **{interaction.guild.name}**.\n{dm_message_second_part} {reason}'

        try:
            await member.send(dm_message)
        except discord.Forbidden:
            pass
        
        
        value = await get_user_from_db(data_to_get="warn", user_id=member.id, guild_id=interaction.guild_id)
        await update_db(column="warn", value=value+1, user_id=member.id, guild_id=interaction.guild_id)

        timeout_message = await translate(text="has been warned for", dest_lng=language)

        await interaction.response.send_message(f"✅ {member.mention} {timeout_message} \"{reason}\"")

    @staff_group.command(name="timeout", description="Temporarily prevents a member from messaging")
    @app_commands.describe(member="The member you want to timeout", duration="How long will the timeout be, in minutes", reason="The reason why the member is timed out from the server")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        
        until = discord.utils.utcnow() + await self.parse_duration(duration_str=duration)
        timestamp = discord.utils.format_dt(until, style='R')
        
        dm_message_first_part = await translate(text="You have been timed out from", dest_lng=language)
        dm_message_second_part = await translate(text="Reason :", dest_lng=language)
        dm_message_third_part = await translate(text="End of the sanction :", dest_lng=language)
        dm_message = f'🚫 {dm_message_first_part} **{interaction.guild.name}**.\n{dm_message_second_part} {reason}\n{dm_message_third_part} {timestamp}'

        try:
            await member.send(dm_message)
        except discord.Forbidden:
            pass

        await member.timeout(until, reason=reason)
        
        timeout_message_first_part = await translate(text="has been timed out for", dest_lng=language)
        timeout_message_second_part = await translate(text="minutes. Reason :", dest_lng=language)
        
        await interaction.response.send_message(f"✅ {member.mention} {timeout_message_first_part} {self.parse_duration(duration_str=duration)} {timeout_message_second_part} {reason}")
    
    @staff_group.command(name="kick", description="Exclude a user from the server")
    @app_commands.describe(member="The member you want to exclude", reason="The reason why the member is excluded from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        
        dm_message_first_part = await translate(text="You have been excluded from", dest_lng=language)
        dm_message = f'🚫 {dm_message_first_part} **{interaction.guild.name}**'

        try:
            await member.send(dm_message)
        except discord.Forbidden:
            pass

        await member.kick(reason=reason)
        
        kick_message = await translate(text="has been excluded. Reason :", dest_lng=language)
        
        await interaction.response.send_message(f"👢 {member.mention} {kick_message} {reason}")
    
    @staff_group.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(member="The member you want to ban", reason="The reason why the member is banned from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        
        dm_message_first_part = await translate(text="You have been defently banned from", dest_lng=language)
        dm_message = f'🚫 {dm_message_first_part} **{interaction.guild.name}**'

        try:
            await member.send(dm_message)
        except discord.Forbidden:
            pass

        await member.ban(reason=reason)
        ban_message = await translate(text="has been defently banned. Reason :", dest_lng=language)
        await interaction.response.send_message(f"🔨 {member.mention} {ban_message} {reason}")

async def setup(client):
    await client.add_cog(Mod(client))