from utils import load_config
import discord
from discord.ext import commands

class OnMemberUpdate(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
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
                await after.add_roles(parent_role)

            elif not has_any_child and parent_role in after.roles:
                await after.remove_roles(parent_role)

async def setup(client):
    await client.add_cog(OnMemberUpdate(client))