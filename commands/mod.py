from utils import load_config, translate
import discord
from discord import app_commands
from discord.ext import commands
import datetime

class Mod(commands.Cog):
    def __init__(self, client):
        self.client = client

    mod_group = app_commands.Group(name="mod", description="Commands for moderators")

    @mod_group.command(name="timeout", description="Temporarily prevents a member from messaging")
    @app_commands.describe(member="The member you want to timeout", minutes="How long will the timeout be, in minutes", reason="The reason why the member is timed out from the server")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        
        duration = datetime.timedelta(minutes=minutes)
        unban_time = discord.utils.utcnow() + duration
        timestamp = discord.utils.format_dt(unban_time, style='R')
        
        dm_message_first_part = await translate(text="You have been timed out from", dest_lng=language)
        dm_message_second_part = await translate(text="Reason :", dest_lng=language)
        dm_message_third_part = await translate(text="End of the sanction :", dest_lng=language)
        dm_message = f'🚫 {dm_message_first_part} **{interaction.guild.name}**.\n{dm_message_second_part} {reason}\n{dm_message_third_part} {timestamp}'

        try:
            await member.send(dm_message)
        except discord.Forbidden:
            pass

        await member.timeout(duration=duration, reason=reason)
        
        timeout_message_first_part = await translate(text="has been timed out for", dest_lng=language)
        timeout_message_second_part = await translate(text="minutes. Reason :", dest_lng=language)
        
        await interaction.response.send_message(f"✅ {member.mention} {timeout_message_first_part} {minutes} {timeout_message_second_part} {reason}")
    
    @mod_group.command(name="kick", description="Exclude a user from the server")
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
    
    @mod_group.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(member="The member you want to ban", reason="The reason why the member is banned from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        
        dm_message_first_part = await translate(text="You have been defently banned from")
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