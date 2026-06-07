import discord
from discord import app_commands
from discord.ext import commands
from utils import load_config, translate
from ui.tickets import TicketLauncher

class Ticket(commands.Cog):
    def __init__(self, client):
        self.client = client

    ticket_group = app_commands.Group(name="ticket", description="Commands related to the ticket system")

    async def permissions(self, interaction: discord.Interaction, config: dict, required_permissions: str) -> bool:
        staff_config = config.get('generals', {}).get('staff', {})
        use_discord_perms = bool(staff_config.get('use_discord_permissions', True))

        if use_discord_perms:
            permissions = interaction.channel.permissions_for(interaction.user)
            return getattr(permissions, required_permissions, False)
        else:
            manage_tickets = staff_config.get('manage_tickets', [])
            return str(interaction.user.id) in [str(uid) for uid in manage_tickets]

    @ticket_group.command(name="setup", description="Send the message to open tickets")
    async def ticket(self, interaction: discord.Interaction):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['generals'].get('language'))

        if not await self.permissions(interaction, config, "manage_channels"):
            refused_message = await translate(text="⛔️ You do not have permission to use this command.", dest_lng=language)
            return await interaction.response.send_message(refused_message, ephemeral=True)

        embed_title = await translate(text="🎫 Create a ticket", dest_lng=language)
        embed_description = await translate(text="You can create a ticket if you need to contact a staff member. Any abuse will be penalized. To create a ticket, click the button below.", dest_lng=language)
        embed = discord.Embed(title=embed_title,
                              description=embed_description,
                              colour=discord.Colour.yellow())

        button_sent_message = await translate(text="✅ The message with the button has been sent", dest_lng=language)
        await interaction.response.send_message(button_sent_message)
        await interaction.channel.send(embed=embed, view=TicketLauncher())


async def setup(client):
    await client.add_cog(Ticket(client))