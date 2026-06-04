import discord
from discord import app_commands
from discord.ext import commands
from ui.partnership import PartnershipModal
from utils import load_config, translate

class Partnership(commands.Cog):
    def __init__(self, client):
        self.client = client
    

    @app_commands.command(name="partnership", description="A command to send formated partnership messages")
    @app_commands.describe(mention="A role to mention into the partnership message", representative="The person who represent the other server", channel="The channel where to send the partnerhsip message")
    @app_commands.checks.has_permissions(administrator=True)
    async def command(self, interaction: discord.Interaction, representative: discord.User, channel: discord.TextChannel, mention: discord.Role = None):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language')) # This will need to be changed once feature/automod is merged into dev

        modal_title = await translate(text="Sending a partnership message", dest_lng=language)
        field_label = await translate(text="Partnership message here", dest_lng=language)
        field_placeholder = await translate(text="Enter the ad of the other server here...", dest_lng=language)

        modal = PartnershipModal(
            title = modal_title,
            label = field_label,
            placeholder = field_placeholder,
            channel = channel,
            representative = representative,
            responsible  = interaction.user,
            mention = mention,
            language = language,
            config = config
        )

        await interaction.response.send_modal(modal)

async def setup(client):
    await client.add_cog(Partnership(client))

        