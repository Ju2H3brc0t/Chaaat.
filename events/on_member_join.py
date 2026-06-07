from utils import add_users_to_db, load_config, translate
import discord
from discord.ext import commands

class OnMemberJoin(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = await load_config(guild_id=member.guild.id, auto_create=True)
        language = config['generals'].get('language', 'en')

        await add_users_to_db(member.id, member.guild.id)

        member_enabled = bool(config['features']['member_roles'].get('enabled'))
        welcome_enabled = bool(config['features']['welcome'].get('enabled'))

        if member_enabled:
            for role_id in config['features']['member_roles'].get('roles_ids', []):
                role = member.guild.get_role(int(role_id))
                if role is not None:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        pass

        if welcome_enabled:
            channel_id = int(config['features']['welcome'].get('announcement_channel_id'))
            
            channel = self.client.get_channel(channel_id)
            if not channel:
                try:
                    channel = await self.client.fetch_channel(channel_id)
                except discord.HTTPException:
                    return

            embed_title = await translate(text="Welcome !", dest_lng=language)
            
            config_text = config['features']['welcome'].get('text')
            translated_text = await translate(text=config_text, dest_lng=language)
            
            embed_description = (
                translated_text
                .replace("{member}", member.mention)
                .replace("{guild}", member.guild.name)
                .replace("{count}", str(member.guild.member_count))
            )

            embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                color=discord.Color.teal(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

async def setup(client):
    await client.add_cog(OnMemberJoin(client))