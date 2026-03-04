from utils import add_users_to_db, load_config, translate
import discord
from discord.ext import commands

class OnMemberJoin(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_member_join(self, member):

        config = await load_config(guild_id=member.guild.id, auto_create=True)
        language = config['features'].get('language', 'en')

        await add_users_to_db(member.id, member.guild.id)

        member_enabled = bool(config['features']['member_role'].get('enabled'))
        welcome_enabled = bool(config['features']['welcome'].get('enabled'))
        channel_id = int(config['features']['welcome'].get('channel_id'))

        if member_enabled is True:
            for role_id in config['features']['member_role'].get('role_id', []):
                role = member.guild.get_role(int(role_id))
                if role is not None:
                    await member.add_roles(role)

        if welcome_enabled is True:
            channel = self.client.get_channel(channel_id)

            embed_title = await translate(text="Welcome !", dest_lng=language)
            embed_description_first_part = await translate(f"Hello")
            embed_description_second_part = await translate(f", welcome to <span class=notranslate>{member.guild.name}</span> !\nThe server now have {member.guild.member_count} members")

            embed = discord.Embed(
                title=embed_title,
                description=f'{embed_description_first_part} {member.mention}{embed_description_second_part}',
                color=discord.Color.teal(),
                timestamp=discord.utils.utcnow())
            
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await channel.send(embed=embed)

async def setup(client):
    await client.add_cog(OnMemberJoin(client))