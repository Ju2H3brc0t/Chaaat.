import discord
from utils import load_config, translate

class TicketModal(discord.ui.Modal):
    def __init__(self, title, label, placeholder, language, config, category):
        super().__init__(title=title)
        self.language = language
        self.config = config
        self.category = category
        self.reason.label = label
        self.reason.placeholder = placeholder

    reason = discord.ui.TextInput(
            label="...", 
            placeholder="...",
            style=discord.TextStyle.short,
            max_length=50,
        )

    async def on_submit(self, interaction_modal: discord.Interaction):
        guild = interaction_modal.guild
        user = interaction_modal.user
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=self.category,
            overwrites=overwrites,
            topic=f"{self.reason.value}"
        )
        
        roles_to_mention = self.config['features']['tickets'].get('mention_roles', [])
        mentions = " ".join([f"<@&{rid}>" for rid in roles_to_mention if rid])
        
        embed_title = await translate(text="🎫 Ticket", dest_lng=self.language)
        embed_description_first_part = await translate(text="hello !\nThank you for creating a ticket, a staff member will answer shortly\n\n**Reason of the ticket** :", dest_lng=self.language)

        embed = discord.Embed(title=embed_title,
                              description=f'{user.mention} {embed_description_first_part} {self.reason.value}',
                              colour=discord.Color.yellow())

        await channel.send(mentions, embed=embed)

        modal_response_first_part = await translate(text="✅ Your ticket has been created :", dest_lng=self.language)

        await interaction_modal.response.send_message(f"{modal_response_first_part} {channel.mention}", ephemeral=True)

class TicketLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="📩", custom_id="ticket_button")
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await load_config(guild_id=interaction.guild.id, auto_create=False)
        language = str(config['features'].get('language'))
        
        category_id = config['features']['tickets'].get('category_id')
        category = interaction.guild.get_channel(int(category_id)) if category_id else None

        m_title = await translate(text="Opening a ticket", dest_lng=language)
        m_label = await translate(text="Reason of the ticket", dest_lng=language)
        m_placeholder = await translate(text="Explain your problem here...", dest_lng=language)

        modal = TicketModal(title=m_title, label=m_label, placeholder=m_placeholder, language=language, config=config, category=category)
        
        await interaction.response.send_modal(modal)
