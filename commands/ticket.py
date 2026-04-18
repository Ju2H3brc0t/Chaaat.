import discord
from discord import app_commands
from discord.ext import commands
from utils import load_config, translate

class Ticket(commands.Cog):
    def __init__(self, client):
        self.client = client

    ticket_group = app_commands.Group(name="ticket", description="Commands related to the ticket system")

    @ticket_group.command(name="setup", description="Send the message to open tickets")
    @app_commands.describe(message="The message to send with the \"open ticket\" button")
    async def ticket(self, interaction: discord.Interaction, message: str):
        from ui.tickets import TicketLauncher
        await interaction.response.send_message(message, view=TicketLauncher(), ephemeral=True)

    @ticket_group.command(name="close", description="Close the ticket channel")
    async def close(self, interaction: discord.Interaction):
        if interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("...", ephemeral=True)
            await interaction.channel.delete()
        else:
            ticket_close_message = await translate("This command can only be used in a ticket channel.", dest_lng=str((await load_config(guild_id=interaction.guild.id, auto_create=False))['features'].get('language')))
            await interaction.response.send_message(ticket_close_message, ephemeral=True)