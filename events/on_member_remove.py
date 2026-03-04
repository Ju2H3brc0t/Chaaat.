from utils import remove_user_from_db, load_config, translate
import discord
from discord.ext import commands

class OnMemberRemove(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await remove_user_from_db(user_id=member.id, guild_id=member.guild.id)

        config = await load_config(guild_id=member.guild.id, auto_create=True)
        language = config['features'].get('language', 'en')
        
        goodbye_enabled = bool(config['features']['goodbye'].get('enabled'))
        channel_id = int(config['features']['goodbye'].get('channel_id'))

        if goodbye_enabled is True:
            channel = await self.client.fetch_channel(channel_id)

            embed_title = await translate(text="Goodbye !", dest_lng=language)
            embed_description = await translate(text=f"has left the server")

            embed = discord.Embed(
                title=embed_title,
                description=f'{member.mention} {embed_description}',
                color=discord.Color.dark_red(),
                timestamp=discord.utils.utcnow())
            
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await channel.send(embed=embed)

async def setup(client):
    await client.add_cog(OnMemberRemove(client))