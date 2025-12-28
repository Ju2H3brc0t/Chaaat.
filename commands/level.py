import discord
from discord import app_commands
from discord.ext import commands
import json
import yaml

class Level(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="level", description="Check your current level and experience points")
    async def level(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        config_path = f'server_configs/{guild_id}/config.yaml'
        user_data_path = f'server_configs/{guild_id}/{interaction.user.id}.json'

        try:
            with open(config_path, 'r') as yaml_file:
                config = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            await interaction.response.send_message("⚠️ Config file not found for this server.", ephemeral=True)
            return

        try:
            with open(user_data_path, 'r') as json_file:
                user_data = json.load(json_file)
        except FileNotFoundError:
            print(f"⚠️ User data file not found for user {interaction.author.id} in guild {guild_id}.")
            return

        language = str(config['features'].get('language'))
        current_lvl = int(user_data.get('level'))
        current_xp = int(user_data.get('experience'))
        xp_to_next = 5 * (current_lvl ** 2) + 50 * current_lvl + 100
        xp_required = xp_to_next - current_xp

        if language == 'fr':
            embed_title = "📊 Niveau et Expérience"
            embed_description = f"Vous êtes actuellement au niveau **{current_lvl}** avec **{current_xp}** points d'expérience.\nPour passer au niveau suivant vous avez besoin de **{xp_required}** points d'expérience supplémentaires."
        else:
            embed_title = "📊 Level and Experience"
            embed_description = f"You are currently at level **{current_lvl}** with **{current_xp}** experience points.\nTo advance to the next level, you need **{xp_required}** more experience points."

        embed = discord.Embed(title=embed_title,
                              description=embed_description,
                              color=discord.Color.gold())

        embed.set_footer(text="Chaaat", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Level(client))