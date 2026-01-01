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

        with open(f'server_configs/{guild_id}/{member.id}.json', 'w') as json_file:
            json.dump(default_json, json_file, indent=4)

        member_enabled = bool(config['features']['member_role'].get('enabled'))
        welcome_enabled = bool(config['features']['welcome'].get('enabled'))
        channel_id = int(config['features']['welcome'].get('channel_id'))

        language = config['features'].get('language', 'en')

        if member_enabled is True:
            for role_id in config['features']['member_role'].get('role_id', []):
                role = member.guild.get_role(int(role_id))
                if role is not None:
                    await member.add_roles(role)

        if welcome_enabled is True:
            channel = self.client.get_channel(channel_id)
            if language == 'fr':
                embed_title = "Bienvenue !"
                embed_description = f"Bonjour {member.mention}, bienvenue sur {member.guild.name} !\nLe serveur compte désormais {member.guild.member_count} membres."
            else:
                embed_title = "Welcome !"
                embed_description = f"Hello {member.mention}, welcome to {member.guild.name} !\nThe server now has {member.guild.member_count} members."
            embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                color=discord.Color.teal(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

async def setup(client):
    await client.add_cog(OnMemberJoin(client))