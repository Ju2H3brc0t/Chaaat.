import discord
from discord.ext import commands
import yaml

class OnMemberJoin(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_member_join(self, member):

        guild_id = member.guild.id
        config_path = f'server_configs/{guild_id}/config.yaml'

        try:
            with open(config_path, 'r') as yaml_file:
                config = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            print(f"⚠️ Config file not found for guild {guild_id}.")
            return
        
        member_enabled = bool(config['features']['member_role'].get('enabled'))

        if member_enabled is True:
            member_role_id = int(config['features']['member_role'].get('role_id'))
            member_role = member.guild.get_role(member_role_id)

            await member.add_roles(member_role)

async def setup(client):
    await client.add_cog(OnMemberJoin(client))