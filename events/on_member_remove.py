import discord
from discord.ext import commands
import yaml
import os

class OnMemberRemove(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):

        guild_id = member.guild.id
        config_path = f'server_configs/{guild_id}/config.yaml'

        try:
            with open(config_path, 'r') as yaml_file:
                config = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            print(f"⚠️ Config file not found for guild {guild_id}.")
            return
        
        goodbye_enabled = bool(config['features']['goodbye'].get('enabled'))
        channel_id = int(config['features']['goodbye'].get('channel_id'))

        language = config['features'].get('language', 'en')

        if goodbye_enabled is True:
            channel = self.client.get_channel(channel_id)
            if language == 'fr':
                embed_title = "Au revoir !"
                embed_description = f"{member.mention} a quitté le serveur."
            else:
                embed_title = "Goodbye !"
                embed_description = f"{member.mention} has left the server."
            embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                color=discord.Color.dark_red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

        if os.path.exists(f'server_configs/{guild_id}/{member.id}.json'):
            os.remove(f'server_configs/{guild_id}/{member.id}.json')

async def setup(client):
    await client.add_cog(OnMemberRemove(client))