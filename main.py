"""
Nightfall Games - Discord Bot (نسخة 3 ملفات)
main.py + database.py + games.py
بوت ألعاب جماعية بالعربي - بدون AI - أوامر سلاش + أزرار + JSON محلي
"""
import discord
from discord.ext import commands
import asyncio
import os
import logging

from games import setup_games

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("nightfall")

TOKEN = os.getenv("DISCORD_TOKEN", "MTU0MjIwMTAzMTYyMTA4NzI3NA.GNTc3b.xuO3RXnSyagGdBH1XO8Ydd8WLhQ_C01h28VnFg")
GUILD_ID = os.getenv("1527415229279895744")  # ضع ID السيرفر عشان الأوامر تظهر فوراً بدل الانتظار ساعة

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class NightfallBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        await setup_games(self)
        log.info("✅ تم تحميل كل الألعاب: مافيا، كراسي، عجلة الحظ، أتوبيس كومبليت، البنك")

        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info(f"🔄 تمت مزامنة {len(synced)} أمر في السيرفر {GUILD_ID}")
        else:
            synced = await self.tree.sync()
            log.info(f"🔄 تمت مزامنة {len(synced)} أمر عالمياً (قد يستغرق حتى ساعة للظهور)")

    async def on_ready(self):
        log.info(f"🌙 {self.user} جاهز ويعمل الآن!")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name="🎮 Nightfall Games")
        )


bot = NightfallBot()


async def main():
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
