import discord
import asyncio
from utils import load_config, translate

class TicketModal(discord.ui.Modal):
    def __init__(self, title, label, placeholder, language, config):
        super().__init__(title=title)
        self.language = language
        self.config = config
        self.reason = discord.ui.TextInput(
            label=label,
            placeholder=placeholder,
            style=discord.TextStyle.short,
            max_length=50,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction_modal: discord.Interaction):
        await interaction_modal.response.defer(ephemeral=True)
        try:
            guild = interaction_modal.guild
            user = interaction_modal.user
            parent_channel = interaction_modal.channel

            thread = await parent_channel.create_thread(
                name=f"ticket-{user.name}",
                type=discord.ChannelType.private_thread,
                invitable=False
            )

            roles = self.config['features']['tickets'].get('roles', [])
            for rid in roles:
                role = guild.get_role(int(rid))
                if role:
                    for member in role.members:
                        await thread.add_user(member)

            embed_title = await translate(text="🎫 Ticket", dest_lng=self.language)
            embed_description_first_part = await translate(text="hello !\nThank you for creating a ticket, a staff member will answer shortly\n\n**Reason of the ticket** :", dest_lng=self.language)

            embed = discord.Embed(
                title=embed_title,
                description=f'{user.mention} {embed_description_first_part} {self.reason.value}',
                colour=discord.Color.yellow()
            )
            await thread.send(embed=embed)

            modal_response_first_part = await translate(text="✅ Your ticket has been created :", dest_lng=self.language)
            await interaction_modal.followup.send(f"{modal_response_first_part} {thread.mention}", ephemeral=True)

        except Exception as e:
            print(e)
            await interaction_modal.followup.send("❌ An error occurred while creating the ticket.", ephemeral=True)

class TicketLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="📩", custom_id="ticket_button")
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await load_config(guild_id=interaction.guild.id, auto_create=False)
        language = str(config['features'].get('language', 'en'))

        m_title, m_label, m_placeholder = await asyncio.gather(
            translate(text="Opening a ticket", dest_lng=language),
            translate(text="Reason of the ticket", dest_lng=language),
            translate(text="Explain your problem here...", dest_lng=language),
        )
        modal = TicketModal(title=m_title, label=m_label, placeholder=m_placeholder, language=language, config=config)

        await interaction.response.send_modal(modal)
