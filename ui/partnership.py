import discord
from utils import load_config, translate

class PartnershipModal(discord.ui.Modal):
    def __init__(self, title, label, placeholder, channel: discord.TextChannel, representative: discord.User, responsible: discord.User, mention: discord.Role, language, config):
        super().__init__(title=title)
        self.language = language
        self.config = config
        
        self.target_channel = channel
        self.representative = representative
        self.responsible = responsible
        self.mention = mention
        
        self.message = discord.ui.TextInput(
            label = label,
            placeholder = placeholder,
            style = discord.TextStyle.paragraph,
            max_length = 2000,
            required = True
        )
        self.add_item(self.message)

    async def on_submit(self, interaction_modal: discord.Interaction):
        await interaction_modal.response.defer(ephemeral=True)

        embed = discord.Embed(colour=0xa6d459)

        representative_field_name = await translate(text="Representative", dest_lng=self.language)
        responsible_field_name = await translate(text="Responsible", dest_lng=self.language)

        embed.add_field(name = representative_field_name,
                        value = self.representative.mention,
                        inline = False)
        embed.add_field(name = responsible_field_name,
                        value = self.responsible.mention,
                        inline = False)
        
        if self.mention is not None:
            await self.target_channel.send(f"{self.mention.mention} | \n\n{self.message.value}", embed=embed)
        else:
            await self.target_channel.send(self.message.value, embed=embed)
        
        response_message = await translate(text="✅ Partnership message sent", dest_lng=self.language)
        
        await interaction_modal.followup.send(response_message, ephemeral=True)