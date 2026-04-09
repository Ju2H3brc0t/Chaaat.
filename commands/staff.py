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

    @staff_group.command(name="clear", description="Clear a certain amount of messages in the channel")
    @app_commands.describe(amount="The amount of messages you want to delete")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))

        await interaction.channel.purge(limit=amount)
        clear_message = await translate(text="messages have been deleted", dest_lng=language) # Need to be added to locale
        await interaction.response.send_message(f"🧹 {amount} {clear_message}", ephemeral=True)

    @staff_group.command(name="profile", description="Display the profile of a member")
    @app_commands.describe(member="The member whose profile you want to display")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def profile(self, interaction: discord.Interaction, member: discord.Member):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        warn_value = await get_user_from_db(data_to_get="warn", user_id=member.id, guild_id=interaction.guild_id)
        timeout_value = await get_user_from_db(data_to_get="timeout_count", user_id=member.id, guild_id=interaction.guild_id)
        note_value = await get_user_from_db(data_to_get="note", user_id=member.id, guild_id=interaction.guild_id)

        embed = discord.Embed(title="Profile", colour=discord.Colour.blurple)
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name=await translate(text="Username", dest_lng=language), value=member.name, inline=True)
        embed.add_field(name=await translate(text="Display Name", dest_lng=language), value=member.display_name, inline=True) 
        embed.add_field(name=await translate(text="Nickname", dest_lng=language), value=member.nick if member.nick else "None", inline=True) 
        embed.add_field(name=await translate(text="Date of account creation", dest_lng=language), value=member.created_at.strftime("%d/%m/%Y %H:%M"), inline=True) 
        embed.add_field(name=await translate(text="Date of joining the server", dest_lng=language), value=member.joined_at.strftime("%d/%m/%Y %H:%M"), inline=True) 
        embed.add_field(name="\u200b", value="\u200b") 
        embed.add_field(name=await translate(text="Sanctions on the server", dest_lng=language), value=f"`{warn_value} warn(s) | {timeout_value} timeout(s)`", inline=True) 
        embed.add_field(name="\u200b", value="\u200b") 
        embed.add_field(name=await translate(text="Note of the moderators", dest_lng=language), value=f"*{note_value}*", inline=True) 

        await interaction.response.send_message(embed=embed)

    @staff_group.command(name="note", description="Add or edit a note on a member's profile")
    @app_commands.describe(member="The member whose note you want to add or edit", note="The note you want to add or edit")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def note(self, interaction: discord.Interaction, member: discord.Member, note: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))

        response_message = await translate(text="✅ Note added for", dest_lng=language)

        await update_db(column="note", value=note, user_id=member.id, guild_id=interaction.guild_id)
        await interaction.response.send_message(f"{response_message} {member.mention}", ephemeral=True)

    @staff_group.command(name="warn", description="Warn a member")
    @app_commands.describe(member="The member you want to warn", reason="The reason why the member is warned")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))

        embed_title = await translate(text="Sanction", dest_lng=language)
        embed_message_first_part = await translate(text="You have been warned in the server", dest_lng=language)
        embed_message_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{embed_message_first_part} **{interaction.guild.name}**\n{embed_message_second_part} {reason}", color=discord.Color.orange())

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass
        
        value = await get_user_from_db(data_to_get="warn", user_id=member.id, guild_id=interaction.guild_id)
        await update_db(column="warn", value=value+1, user_id=member.id, guild_id=interaction.guild_id)

        embed_title = await translate(text="Sanction", dest_lng=language)
        embed_message_first_part = await translate(text="has been warned in the server", dest_lng=language)
        embed_message_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{member.mention} {embed_message_first_part}\n{embed_message_second_part} {reason}", color=discord.Color.orange())

        await interaction.response.send_message(embed=embed)

    @staff_group.command(name="timeout", description="Temporarily prevents a member from messaging")
    @app_commands.describe(member="The member you want to timeout", duration="How long will the timeout be, in minutes", reason="The reason why the member is timed out from the server")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        
        until = discord.utils.utcnow() + await self.parse_duration(duration_str=duration)
        timestamp = discord.utils.format_dt(until, style='R')
        
        embed_title = await translate(text="Sanction", dest_lng=language)
        embed_first_part = await translate(text="You have been timed out from the server", dest_lng=language)
        embed_second_part = await translate(text="Reason :", dest_lng=language)
        embed_third_part = await translate(text="End of the sanction :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{embed_first_part} **{interaction.guild.name}**\n{embed_second_part} {reason}\n{embed_third_part} {timestamp}", color=discord.Color.orange())

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass
        
        value = await get_user_from_db(data_to_get="timeout_count", user_id=member.id, guild_id=interaction.guild_id)
        await update_db(column="timeout_count", value=value+1, user_id=member.id, guild_id=interaction.guild_id)

        await member.timeout(until, reason=reason)
        
        embed_title = await translate(text="Sanction", dest_lng=language)
        embed_first_part = await translate(text="has been timed out from the server", dest_lng=language)
        embed_second_part = await translate(text="Reason :", dest_lng=language)
        embed_third_part = await translate(text="End of the sanction :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{member.mention} {embed_first_part}\n{embed_second_part} {reason} | {embed_third_part} {timestamp}", color=discord.Color.orange())

        await interaction.response.send_message(embed=embed)
    
    @staff_group.command(name="kick", description="Exclude a user from the server")
    @app_commands.describe(member="The member you want to exclude", reason="The reason why the member is excluded from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        
        embed_title = await translate(text="Sanction", dest_lng=language)
        embed_first_part = await translate(text="You have been kicked from the server", dest_lng=language)
        embed_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{embed_first_part} **{interaction.guild.name}**\n{embed_second_part} {reason}", color=discord.Color.orange())

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        await member.kick(reason=reason)
        
        embed_title = await translate(text="Sanction", dest_lng=language)
        embed_first_part = await translate(text="has been kicked from the server", dest_lng=language)
        embed_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{member.mention} {embed_first_part}\n{embed_second_part} {reason}", color=discord.Color.orange())
        
        await interaction.response.send_message(embed=embed)
    
    @staff_group.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(member="The member you want to ban", reason="The reason why the member is banned from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        
        embed_title = await translate(text="Sanction", dest_lng=language)
        embed_first_part = await translate(text="You have been banned from the server", dest_lng=language)
        embed_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{embed_first_part} **{interaction.guild.name}**\n{embed_second_part} {reason}", color=discord.Color.orange())

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        await member.ban(reason=reason)

        embed_title = await translate(text="Sanction", dest_lng=language)
        embed_first_part = await translate(text="has been banned from the server", dest_lng=language)
        embed_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{member.mention} {embed_first_part}\n{embed_second_part} {reason}", color=discord.Color.orange())
        
        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Mod(client))