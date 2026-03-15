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
    @mod_group.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration=duration, reason=reason)
        
        timeout_message_first_part = await translate(text="has been timed out for", dest_lng=language)
        timeout_message_second_part = await translate(text="minutes. Reason :", dest_lng=language)
        
        await interaction.response.send_message(f"✅ {member.mention} {timeout_message_first_part} {minutes} {timeout_message_second_part} {reason}")
    
    @mod_group.command(name="kick", description="Exclude a user from the server")
    @mod_group.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        
        await member.kick(reason=reason)
        
        kick_message = await translate(text="has been excluded. Reason :", dest_lng=language)
        
        await interaction.response.send_message(f"👢 {member.mention} {kick_message} {reason}")
    
    @mod_group.command(name="ban", description="Ban a user from the server")
    @mod_group.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))
        
        await member.ban(reason=reason)
        ban_message = await translate(text="has been defently banned. Reason :", dest_lng=language)
        await interaction.response.send_message(f"🔨 {member.mention} {ban_message} {reason}")

async def setup(client):
    await client.add_cog(Mod(client))