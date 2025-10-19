import discord
from discord import app_commands
from discord.ext import commands
import yaml

class config(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="view_config", description="Display the current server configuration")
    async def config(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        config_path = f'server_configs/{guild_id}/config.yaml'

        try:
            with open(config_path, 'r') as yaml_file:
                config = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            await interaction.response.send_message("⚠️ Config file not found for this server.", ephemeral=True)
            return

        features = config.get('features', {})
        language = str(config['features']['language'].get('default'))

        embed_title = "⚙️ Configuration du serveur" if language == "fr" else "⚙️ Configuration of the server"
        embed_description = "Voici la configuration du bot pour ce serveur :" if language == "fr" else "Here's the configuration of the bot for this server:"

        embed = discord.Embed(
            title=embed_title,
            description=embed_description,
            colour=discord.Color.blurple() 
        )
        embed.set_footer(text="Chaaat • Config Viewer", icon_url=self.client.user.display_avatar.url)

        for feature_name, settings in features.items():
            if not isinstance(settings, dict):
                settings = { "Valeur": settings }

            value_str = "\n".join([f"- **{key}** : `{value}`" for key, value in settings.items()])
            embed.add_field(
                name=f"{feature_name}",
                value=value_str,
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(config(client))
