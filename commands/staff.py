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

    async def permissions(self, interaction: discord.Interaction, config: dict, required_permissions: str) -> bool:
        staff_config = config.get('generals', {}).get('staff', {})
        use_discord_perms = bool(staff_config.get('use_discord_permissions', True))

        if use_discord_perms:
            permissions = interaction.channel.permissions_for(interaction.user)
            return getattr(permissions, required_permissions, False)
        else:
            moderate_users = staff_config.get('moderate_users', [])
            return str(interaction.user.id) in [str(uid) for uid in moderate_users]

    staff_group = app_commands.Group(name="staff", description="Commands for moderators")

    @staff_group.command(name="clear", description="Clear a certain amount of messages in the channel")
    @app_commands.describe(amount="The amount of messages you want to delete")
    async def clear(self, interaction: discord.Interaction, amount: int):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['generals'].get('language'))

        if not await self.permissions(interaction, config, "manage_messages"):
            refused_message = await translate(text="⛔️ You do not have permission to use this command.", dest_lng=language)
            return await interaction.response.send_message(refused_message, ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)

        if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
            error_permission_message = await translate(text="❌ I don't have permission to manage messages in this channel.", dest_lng=language)
            return await interaction.followup.send(error_permission_message, ephemeral=True)

        try:
            clear_message = await translate(text="messages have been deleted", dest_lng=language)
            await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"🧹 {amount} {clear_message}", ephemeral=True)
        except discord.Forbidden:
            error_forbidden_message = await translate(text="❌ Failed to delete messages (Forbidden error).", dest_lng=language)
            await interaction.followup.send(error_forbidden_message, ephemeral=True)

    @staff_group.command(name="profile", description="Display the profile of a member")
    @app_commands.describe(member="The member whose profile you want to display")
    async def profile(self, interaction: discord.Interaction, member: discord.Member):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['generals'].get('language'))
        
        if not await self.permissions(interaction, config, "manage_messages"):
            refused_message = await translate(text="⛔️ You do not have permission to use this command.", dest_lng=language)
            return await interaction.response.send_message(refused_message, ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        
        warn_value = await get_user_from_db(data_to_get="warn", user_id=member.id, guild_id=interaction.guild_id)
        timeout_value = await get_user_from_db(data_to_get="timeout_count", user_id=member.id, guild_id=interaction.guild_id)
        note_value = await get_user_from_db(data_to_get="note", user_id=member.id, guild_id=interaction.guild_id)

        info = await translate(text="📝 Informations", dest_lng=language)
        username = await translate(text="User name", dest_lng=language)
        displayname = await translate(text="Display name", dest_lng=language)
        nickname = await translate(text="Nickname on the server", dest_lng=language)
        id = await translate(text="User ID", dest_lng=language)
        joined = await translate(text="Joined the server", dest_lng=language)
        created = await translate(text="Creater his account", dest_lng=language)
        sanctions = await translate(text="📛 Sanctions", dest_lng=language)
        warn = await translate(text="warn(s)", dest_lng=language)
        mute = await translate(text="mute(s)", dest_lng=language)
        notes = await translate(text="Notes from the moderators", dest_lng=language)

        embed = discord.Embed(title="Profile", description=f"__**{info}**__\n\n**{username}** : *{member.global_name}*\n**{displayname}** : *{member.display_name}*\n**{nickname}** : *{member.nick}*\n**{id}** : `{member.id}`\n\n**{joined}** : <t:{int(member.joined_at.timestamp())}:F>\n**{created}** : <t:{int(member.created_at.timestamp())}>\n\n__**{sanctions}**__\n\n**{warn}** : {warn_value}\n**{mute}** : {timeout_value}\n\n__**{notes}**__\n```\n{note_value if note_value is not None else await translate(text="No note has been added about his user for now", dest_lng=language)}\n```", color=discord.Color.blurple())
        embed.set_thumbnail(url=member.display_avatar.url)

        await interaction.followup.send(embed=embed)

    @staff_group.command(name="note", description="Add or edit a note on a member's profile")
    @app_commands.describe(member="The member whose note you want to add or edit", note="The note you want to add or edit")
    async def note(self, interaction: discord.Interaction, member: discord.Member, note: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['generals'].get('language'))

        if not await self.permissions(interaction, config, "manage_messages"):
            refused_message = await translate(text="⛔️ You do not have permission to use this command.", dest_lng=language)
            return await interaction.response.send_message(refused_message, ephemeral=True)

        response_message = await translate(text="✅ Note added for", dest_lng=language)

        await update_db(column="note", value=note, user_id=member.id, guild_id=interaction.guild_id)
        await interaction.response.send_message(f"{response_message} {member.mention}", ephemeral=True)

    @staff_group.command(name="warn", description="Warn a member")
    @app_commands.describe(member="The member you want to warn", reason="The reason why the member is warned")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['generals'].get('language'))

        await interaction.response.defer(ephemeral=True)

        if not await self.permissions(interaction, config, "manage_messages"):
            refused_message = await translate(text="⛔️ You do not have permission to use this command.", dest_lng=language)
            return await interaction.response.send_message(refused_message, ephemeral=True)

        embed_title = await translate(text="📛 Sanction", dest_lng=language)
        embed_message_first_part = await translate(text="You have been warned in the server", dest_lng=language)
        embed_message_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{embed_message_first_part} **{interaction.guild.name}**\n{embed_message_second_part} {reason}", color=discord.Color.orange())

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass
        
        value = await get_user_from_db(data_to_get="warn", user_id=member.id, guild_id=interaction.guild_id)
        await update_db(column="warn", value=value+1, user_id=member.id, guild_id=interaction.guild_id)

        embed_title = await translate(text="📛 Sanction", dest_lng=language)
        embed_message_first_part = await translate(text="has been warned in the server", dest_lng=language)
        embed_message_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{member.mention} {embed_message_first_part}\n{embed_message_second_part} {reason}", color=discord.Color.orange())

        await interaction.followup.send(embed=embed)

    @staff_group.command(name="timeout", description="Temporarily prevents a member from messaging")
    @app_commands.describe(member="The member you want to timeout", duration="How long will the timeout be, in minutes", reason="The reason why the member is timed out from the server")
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['generals'].get('language'))
        
        if not await self.permissions(interaction, config, "manage_messages"):
            refused_message = await translate(text="⛔️ You do not have permission to use this command.", dest_lng=language)
            return await interaction.response.send_message(refused_message, ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        until = discord.utils.utcnow() + await self.parse_duration(duration_str=duration)
        timestamp = discord.utils.format_dt(until, style='R')
        
        embed_title = await translate(text="📛 Sanction", dest_lng=language)
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
        
        embed_title = await translate(text="📛 Sanction", dest_lng=language)
        embed_first_part = await translate(text="has been timed out from the server", dest_lng=language)
        embed_second_part = await translate(text="Reason :", dest_lng=language)
        embed_third_part = await translate(text="End of the sanction :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{member.mention} {embed_first_part}\n{embed_second_part} {reason} **|** {embed_third_part} {timestamp}", color=discord.Color.orange())

        await interaction.followup.send(embed=embed)
    
    @staff_group.command(name="kick", description="Exclude a user from the server")
    @app_commands.describe(member="The member you want to exclude", reason="The reason why the member is excluded from the server")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['generals'].get('language'))
        
        if not await self.permissions(interaction, config, "kick_members"):
            refused_message = await translate(text="⛔️ You do not have permission to use this command.", dest_lng=language)
            return await interaction.response.send_message(refused_message, ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        embed_title = await translate(text="📛 Sanction", dest_lng=language)
        embed_first_part = await translate(text="You have been kicked from the server", dest_lng=language)
        embed_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{embed_first_part} **{interaction.guild.name}**\n{embed_second_part} {reason}", color=discord.Color.orange())

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        await member.kick(reason=reason)
        
        embed_title = await translate(text="📛 Sanction", dest_lng=language)
        embed_first_part = await translate(text="has been kicked from the server", dest_lng=language)
        embed_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{member.mention} {embed_first_part}\n{embed_second_part} {reason}", color=discord.Color.orange())
        
        await interaction.followup.send(embed=embed)
    
    @staff_group.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(member="The member you want to ban", reason="The reason why the member is banned from the server")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['generals'].get('language'))
        
        if not await self.permissions(interaction, config, "ban_members"):
            refused_message = await translate(text="⛔️ You do not have permission to use this command.", dest_lng=language)
            return await interaction.response.send_message(refused_message, ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        embed_title = await translate(text="📛 Sanction", dest_lng=language)
        embed_first_part = await translate(text="You have been banned from the server", dest_lng=language)
        embed_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{embed_first_part} **{interaction.guild.name}**\n{embed_second_part} {reason}", color=discord.Color.orange())

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        await member.ban(reason=reason)

        embed_title = await translate(text="📛 Sanction", dest_lng=language)
        embed_first_part = await translate(text="has been banned from the server", dest_lng=language)
        embed_second_part = await translate(text="Reason :", dest_lng=language)
        embed = discord.Embed(title=embed_title, description=f"{member.mention} {embed_first_part}\n{embed_second_part} {reason}", color=discord.Color.orange())
        
        await interaction.followup.send(embed=embed)

async def setup(client):
    await client.add_cog(Mod(client))