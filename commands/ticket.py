import discord
from discord import app_commands
from discord.ext import commands
from utils import load_config, translate

class Ticket(commands.Cog):
    def __init__(self, client):
        self.client = client

    ticket_group = app_commands.Group(name="ticket", description="Commands related to the ticket system")

    @ticket_group.command(name="setup", description="Send the message to open tickets")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket(self, interaction: discord.Interaction):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))

        embed_title = await translate(text="🎫 Create a ticket", dest_lng=language)
        embed_description = await translate(text="You can create a ticket if you need to contact a staff member. Any abuse will be penalized. To create a ticket, click the button below.", dest_lng=language)
        embed = discord.Embed(title=embed_title,
                              description=embed_description,
                              colour=discord.Colour.yellow())

        from ui.tickets import TicketLauncher
        await interaction.channel.send(embed=embed, view=TicketLauncher())
        button_sent_message = await translate(text="✅ The message with the button has been sent", dest_lng=language)
        await interaction.response.send_message(button_sent_message)

    @ticket_group.command(name="close", description="Close the ticket channel")
    async def close(self, interaction: discord.Interaction):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language'))

        if interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("...", ephemeral=True)
            await interaction.channel.delete()
        else:
            ticket_close_message = await translate("⛔ This command can only be used in a ticket channel.", dest_lng=language)
            await interaction.response.send_message(ticket_close_message, ephemeral=True)

async def setup(client):
    await client.add_cog(Ticket(client))