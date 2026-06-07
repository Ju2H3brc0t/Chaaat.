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
        language = config['generals'].get('language', 'en')
        
        goodbye_enabled = bool(config['features']['goodbye'].get('enabled'))
        
        if goodbye_enabled:

            channel_id = int(config['features']['goodbye'].get('announcement_channel_id'))

            channel = self.client.get_channel(channel_id)
            if not channel:
                try:
                    channel = await self.client.fetch_channel(channel_id)
                except discord.HTTPException:
                    return 

            user_object = member
            if not hasattr(member, 'display_avatar') or member.display_avatar is None:
                user_object = self.client.get_user(member.id)
                if not user_object:
                    try:
                        user_object = await self.client.fetch_user(member.id)
                    except discord.HTTPException:
                        user_object = member

            embed_title = await translate(text="Goodbye !", dest_lng=language)
            
            config_text = config['features']['goodbye'].get('text', "{member} has left the server")
            translated_text = await translate(text=config_text, dest_lng=language)

            embed_description = (
                translated_text
                .replace("{member}", user_object.mention)
                .replace("{guild}", member.guild.name)
            )

            embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                color=discord.Color.dark_red(),
                timestamp=discord.utils.utcnow()
            )
            
            if user_object and hasattr(user_object, 'display_avatar') and user_object.display_avatar:
                embed.set_thumbnail(url=user_object.display_avatar.url)
            else:
                embed.set_thumbnail(url=member.default_avatar.url)
            
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass
async def setup(client):
    await client.add_cog(OnMemberRemove(client))