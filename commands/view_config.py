import discord
from discord import app_commands
from discord.ext import commands
import yaml

def format_dict(d, indent=0):
    lines = []
    for key, value in d.items():
        prefix = "  " * indent + "- **" + str(key) + "** : "

        if isinstance(value, dict):
            lines.append(prefix)
            lines.extend(format_dict(value, indent + 1))
        else:
            lines.append(prefix + f"`{value}`")
    return lines

class ViewConfig(commands.Cog):
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

        features = config.get("features", {})
        language = features.get("language", "en")

        if language == "fr":
            embed_title = "⚙️ Configuration du serveur"
            embed_description = "⚠️ Cette commande renvoi directement le contenu du fichier yaml associé a ce serveur, vous pouvez l'éditer via la commande `/set_config` a vos risques et périls.\n\nVoici la configuration du bot pour ce serveur :"
        else:
            embed_title = "⚙️ Server configuration"
            embed_description = "⚠️ This command directly returns the content of the yaml file associated with this server, you can edit it via the `/set_config` command at your own risk.\n\nHere is the bot configuration for this server :"

        embed = discord.Embed(
            title=embed_title,
            description=embed_description,
            colour=discord.Color.light_gray()
        )

        embed.set_footer(text="Chaaat • Config Viewer", icon_url=self.client.user.display_avatar.url)

        for feature_name, settings in features.items():
            if isinstance(settings, dict):
                text = "\n".join(format_dict(settings))
            else:
                text = f"`{settings}`"

            embed.add_field(
                name=feature_name,
                value=text,
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(ViewConfig(client))