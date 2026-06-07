from utils import load_config
import discord
from discord.ext import commands
import decancer_py as decancer

class OnMemberUpdate(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    async def banned_nicknames(self, before, after):
        config = await load_config(guild_id=after.guild.id, auto_create=True)

        if before.display_name == after.display_name:
            return
        
        banned_nicknames = []

        if not config['generals']['staff'].get('use_discord_permissions'):
            staff_id = set(config['generals']['staff'].get('manage_tickets', [])) | set(config['generals']['staff'].get('moderate_users', []))
        else:
            manage_channels = {m.id for m in after.guild.members if m.guild_permissions.manage_channels}
            moderate_users = {m.id for m in after.guild.members if m.guild_permissions.moderate_users}
            staff_id = manage_channels | moderate_users

        if after.id in staff_id:
            return

        for staff in staff_id:
            member = after.guild.get_member(staff)
            if not member:
                try:
                    member = await after.guild.fetch_member(staff)
                except discord.HTTPException:
                    continue

            if member:
                cleaned_staff_name = str(decancer.parse(member.display_name)).lower().replace(" ", "")
                banned_nicknames.append(cleaned_staff_name)

        for nickname in config['features']['automod'].get('banned_nicknames', []):
            banned_nicknames.append(str(decancer.parse(nickname)).lower().replace(" ", ""))

        cleaned_after_name = str(decancer.parse(after.display_name)).lower().replace(" ", "")
        if cleaned_after_name in banned_nicknames:
            try:
                await after.edit(nick=None)
            except discord.Forbidden:
                pass 

    async def linked_roles(self, before, after):
        config = await load_config(guild_id=after.guild.id, auto_create=True)

        if before.roles == after.roles:
            return
        
        after_ids = {str(r.id) for r in after.roles}
        linked_roles = config['features'].get('linked_roles', {})

        for parent_id, children_id in linked_roles.items():
            children_ids = [str(c) for c in children_id]
            parent_role = after.guild.get_role(int(parent_id))

            if not parent_role:
                continue

            has_any_child = any(cid in after_ids for cid in children_ids)

            if has_any_child and parent_role not in after.roles:
                try:
                    await after.add_roles(parent_role)
                except discord.Forbidden:
                    pass

            elif not has_any_child and parent_role in after.roles:
                try:
                    await after.remove_roles(parent_role)
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        await self.banned_nicknames(before, after)
        await self.linked_roles(before, after)

async def setup(client):
    await client.add_cog(OnMemberUpdate(client))