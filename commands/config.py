from utils import DEFAULT_CONFIG, load_config, translate
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

class Config(commands.Cog):
    def __init__(self, client):
        self.client = client

    config_group = app_commands.Group(name="config", description="Commands to modify the configs of the current server")

    @config_group.command(name="show", description="Show the configs of the current server")
    @app_commands.check.has_permissions(administration=True)
    async def show(self, interaction: discord.Interaction):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        features = config.get("features", {})
        language = str(config['features'].get('language', 'en'))

        embed_title = await translate(text="⚙️ Server configuration", dest_lng=language)
        embed_description = await translate(text="⚠️ This command directly returns the content of the yaml file associated with this server, you can edit it via the `/set_config` command at your own risk.\n\nHere is the bot configuration for this server :", dest_lng=language)

        embed = discord.Embed(
            title=embed_title,
            description=embed_description,
            colour=discord.Color.light_gray()
        )

        embed.set_footer(text="Chaat• Config Viewer", icon_url=self.client.user.display_avatar.url)

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

    @config_group.command(name="edit", description="Edit the configs of the current server")
    @app_commands.describe(path="The path to the key you want to modify")
    @app_commands.check.has_permissions(administrator=True)
    async def edit(self, interaction: discord.Interaction, path: str):
        clean_path = path.replace("\\", "")

        config = await load_config(guild_id=interaction.guild_id, auto_create=False)
        if not config:
            await interaction.response.send_message("⚠️ Config file not found for this server.", ephemeral=True)
            return

        language = str(config['features'].get('language', 'en'))

        keys = clean_path.split(':')
        if len(keys) < 2:
            error_message = await translate(text="⚠️ Format: `key:value` or `key:subkey:value`", dest_lng=language)
            await interaction.response.send_message(error_message)
            return
        
        *dict_path, value_str = keys

        new_value = yaml.safe_load(value_str)

        ref = config['features']
        for key in dict_path[:-1]:
            if key not in ref or not isinstance(ref[key], dict):
                ref[key] = {}
            ref = ref[key]

        final_key = dict_path[-1]
        ref[final_key] = new_value

        config_file_path = f'server_configs/{interaction.guild_id}/config.yaml'
        with open(config_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)

        intro_success_message = await translate(f"✅ Key ")
        outro_success_message = await translate(f" updated successfully !")
        success_message = f'{intro_success_message}{path}{outro_success_message}'

        await interaction.response.send_message(success_message)

    @config_group.command(name="reset", description="Reset default configs for the current server")
    @app_commands.check.has_permissions(administrator=True)
    async def reset(self, interaction: discord.Interaction):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language', 'en'))

        config_file_path = f'server_configs/{interaction.guild_id}/config.yaml'

        with open(config_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(DEFAULT_CONFIG, f, allow_unicode=True)

        confirm_message = await translate(f"✅ Configuration has been reset to default values", dest_lng=language)
        await interaction.response.send_message(confirm_message)

    @config_group.command(name="help", description="get some help with the configs editor")
    @app_commands.check.has_permissions(administrator=True)
    async def help(self, interaction: discord.Interaction):
        config = await load_config(guild_id=interaction.guild_id, auto_create=True)
        language = str(config['features'].get('language', 'en'))

        help_text = (
            "## ⚙️ Configuration Help\n\n"
            "### 📋 Available Commands :\n"
            "* **`/config show`** : Show current config file for the server in YAML format\n"
            "* **`/config edit`** : Allow to modify a specific value\n"
            "* **`/config reset`** : Reset the config file with defaul values. **Warning : cannot be undone !\n\n**"
            "### ✏️ How to use `/config edit` :\n"
            "You have to give the path to the key you want to modify\n"
            "For example: to enable the leveling system you hve to type `/config edit feature:leveling:enabled:True`\n"
            "If you want to disable it you have to type `/config edit leveling:enabled:False` instead\n\n"
            "### 💡 Tips :\n"
            "* **Escape characters** : You can use escape characters like the backslash to avoid Discord replacing one of your value to an emoji, for exemple, if you wanna type `:100:`\n"
            "* **YAML format** : Respect types (True/False for booleans, numbers for ID's)\n"
            "* **Users/Channels ID** : You can get the ID of something by enabling developper mode in Discord settings then doing right click -> Copy ID\n\n"
            "### Useful ressources :\n"
            "* [Learn YAML in 5 minutes](https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started) *"
            "* [online YAML verifyer](https://yamlchecker.com/) *"
        )

        translated_help_text = await translate(text=help_text, dest_lng=language)
        await interaction.response.send_message(translated_help_text)

async def setup(client):
    await client.add_cog(Config(client))