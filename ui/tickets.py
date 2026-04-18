import discord
from utils import load_config, translate

class TicketLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="📩", custom_id="ticket_button")
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await load_config(guild_id=interaction.guild.id, auto_create=False)
        language = str(config['features'].get('language'))

        category_id = config['features']['tickets'].get('category_id')
        category = discord.utils.get(interaction.guild.categories, id=category_id)

        class TicketModal(discord.ui.Modal, title=translate("Opening a Ticket", dest_lng=language)):
            reason = discord.ui.TextInput(
                label=translate("Reason of the ticket", dest_lng=language),
                placeholder=translate("Explain the reason here...", dest_lng=language),
                style=discord.TextStyle.short,
                max_length=50,
            )

            async def on_submit(self, interaction_modal: discord.Interaction):
                guild = interaction_modal.guild
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    interaction_modal.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, view_channel=True),
                    guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, view_channel=True)
                }

                channel = await guild.create_text_channel(
                    name=f"ticket-{interaction_modal.user.name}",
                    category=category,
                    overwrites=overwrites
                )

                ticket_created_message = translate("Your ticket has been created :", dest_lng=language)
                ticket_message_first_part = translate('Hello !\n A staff member will be with you shortly.', dest_lng=language)
                roles_to_mention = config['features']['tickets'].get('mention_roles', [])
                ticket_message = f'{interaction_modal.user.mention} {ticket_message_first_part}\n'

                for role_id in roles_to_mention:
                    role = guild.get_role(int(role_id))
                    if role:
                        ticket_message += f' {role.mention}'

                await interaction_modal.response.send_message(f"{ticket_created_message} {channel.mention}", ephemeral=True)
                await channel.send(ticket_message)   

        await interaction.response.send_modal(TicketModal())
