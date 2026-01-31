import discord
from discord.ext import commands, tasks
import itertools

class AnimatedStatus(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.statuses = itertools.cycle([
            discord.Activity(type=discord.ActivityType.watching, name="(ᴗ˳ᴗ) z"),
            discord.Activity(type=discord.ActivityType.watching, name="(ᴗ˳ᴗ) zZ"),
            discord.Activity(type=discord.ActivityType.watching, name="(ᴗ˳ᴗ) zZz"),
        ])
        self.change_status.start()

    @tasks.loop(seconds=3)
    async def change_status(self):
        new_status = next(self.statuses)
        await self.client.change_presence(activity=new_status)

    @change_status.before_loop
    async def before_change_status(self):
        await self.client.wait_until_ready()

async def setup(client):
    await client.add_cog(AnimatedStatus(client))