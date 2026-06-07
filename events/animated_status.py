import discord
from discord.ext import commands, tasks
import itertools
import datetime

class AnimatedStatus(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.animation_step = 0
        self.change_status.start()

    @tasks.loop(seconds=15)
    async def change_status(self):
        now = datetime.datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        weekday = now.weekday()

        status_name = "(•_•)"

        if current_hour >= 22 or current_hour < 7:
            status_name = "(ᴗ˳ᴗ) zZ"
        
        elif current_hour == 21:
            status_name = "(─_─)💤"
        
        elif current_hour == 7 and current_minute < 15:
            status_name = "(˙𐃷˙)"

        else:
            if weekday == 0:
                status_name = "(ಥ﹏ಥ)"

            elif weekday == 1:
                status_name = "(￣_￣)"
            
            elif weekday == 2:
                status_name = "(•_•)"
            
            elif weekday == 3:
                status_name = "(ᵔ◡ᵔ)"
            
            elif weekday == 4:
                status_name = "(📣^▽^)"
            
            elif weekday in [5, 6]:
                dance_moves = ["~(˘▽˘~)", "(~˘▽˘)~", "ヘ(^_^ヘ)", "(ノ^_^)ノ"]
                status_name = dance_moves[self.animation_step % len(dance_moves)]
                self.animation_step += 1
        
        try:
            await self.client.change_presence(activity=discord.CustomActivity(name=status_name))
        except discord.HTTPException:
            pass

    @change_status.before_loop
    async def before_change_status(self):
        await self.client.wait_until_ready()

async def setup(client):
    await client.add_cog(AnimatedStatus(client))