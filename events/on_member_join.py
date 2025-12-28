import discord
from discord.ext import commands
import yaml
import json

class OnMemberJoin(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_member_join(self, member):

        guild_id = member.guild.id
        config_path = f'server_configs/{guild_id}/config.yaml'

        default_json = {
            'level': 1,
            'experience': 0
        }

        try:
            with open(config_path, 'r') as yaml_file:
                config = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            print(f"⚠️ Config file not found for guild {guild_id}.")
            return

        member_enabled = bool(config['features']['member_role'].get('enabled'))
        level_enabled = bool(config['features']['leveling'].get('enabled'))

        if member_enabled is True:
            for role in config['features']['member_role'].get('role_id'):
                member_role = member.guild.get_role(int(role))
                if member_role is not None:
                    await member.add_roles(member_role)
        
        if level_enabled is True:
            default_level_role_id = int(config['features']['leveling'].get('default_level'))
            default_level_role = member.guild.get_role(default_level_role_id)
            if default_level_role is not None:
                await member.add_roles(default_level_role)

        with open(f'server_configs/{guild_id}/{member.id}.json', 'w') as json_file:
            json.dump(default_json, json_file, indent=4)

async def setup(client):
    await client.add_cog(OnMemberJoin(client))