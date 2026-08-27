import os
import asyncio
import random
import discord
from discord.ext import commands
from openai import AsyncOpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GROK_KEY = os.getenv("ZXurbdLhWK5zCH6BHgUfxW6NZt0JhzT0gXjVNOS1R6KwdNQoWfNqmou52X0DNIY3p8MeRuQAb5S5RUYP") or "xai-ZXurbdLhWK5zCH6BHgUfxW6NZt0JhzT0gXjVNOS1R6KwdNQoWfNqmou52X0DNIY3p8MeRuQAb5S5RUYP"

grok_client = AsyncOpenAI(
    api_key=GROK_KEY,
    base_url="https://api.x.ai/v1"
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

import config
import games

mafia_games = {}
chairs_games = {}
roulette_games = {}
bus_games = {}

ARABIC_LETTERS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
BUS_CATEGORIES = ["اسم", "جماد", "حيوان", "نبات", "بلاد"]

async def check_word_with_grok(word: str, category: str, letter: str) -> bool:
    try:
        prompt = (
            f"هل كلمة '{word}' هي اسم {category} صحيح معروف باللغة العربية ويبدأ بحرف '{letter}'؟ "
            f"أجب بكلمة واحدة فقط: نعم أو لا."
        )
        response = await grok_client.chat.completions.create(
            model="grok-beta",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=5
        )
        answer = response.choices[0].message.content.strip()
        return "نعم" in answer
    except Exception as e:
        print(f"AI Verification Error: {e}")
        return False

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Bot online | Synced {len(synced)} commands")
    except Exception as e:
        print(f"Sync error: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    cid = message.channel.id

    if cid in bus_games:
        g_data = bus_games[cid]
        content = message.content.strip()

        if content.startswith(g_data["letter"]) and len(content) == g_data["length"]:
            is_valid = await check_word_with_grok(content, g_data["category"], g_data["letter"])

            if is_valid:
                n_letter = random.choice(ARABIC_LETTERS)
                n_cat = random.choice(BUS_CATEGORIES)
                n_length = random.randint(3, 5)

                bus_games[cid].update({"letter": n_letter, "category": n_cat, "length": n_length})
                
                await message.reply(
                    embed=games.embed(
                        "إجابة صحيحة ✨",
                        f"أحسنت {message.author.mention}! الكلمة (**{content}**) صحيحة.\n\n"
                        f"المطلوب الجديد: **{n_cat}** بحرف **{n_letter}** (طولها **{n_length}** أحرف)",
                        config.COLORS["success"]
                    ),
                    view=BusControlView(cid, g_data["host"])
                )
                return
            else:
                await message.add_reaction("❌")

    await bot.process_commands(message)

GAME_CHOICES = [
    discord.app_commands.Choice(name="Roulette", value="roulette"),
    discord.app_commands.Choice(name="Mafia", value="mafia"),
    discord.app_commands.Choice(name="Guess Country", value="country"),
    discord.app_commands.Choice(name="Hide and Seek", value="hide"),
    discord.app_commands.Choice(name="Musical Chairs", value="chairs"),
    discord.app_commands.Choice(name="Dice Roll", value="dice"),
    discord.app_commands.Choice(name="Replica", value="replica"),
    discord.app_commands.Choice(name="Rock Paper Scissors", value="rps"),
    discord.app_commands.Choice(name="XO", value="xo"),
    discord.app_commands.Choice(name="Hot XO", value="hotxo"),
    discord.app_commands.Choice(name="Bus Complete", value="bus"),
    discord.app_commands.Choice(name="Bank Game", value="bank")
]

@bot.tree.command(name="game", description="Start a new game")
@discord.app_commands.choices(choice=GAME_CHOICES)
async def game_cmd(interaction: discord.Interaction, choice: discord.app_commands.Choice[str]):
    try:
        g, p, cid = choice.value, interaction.user, interaction.channel_id

        # لعبة أتوبيس كومبليت
        if g == "bus":
            if cid in bus_games:
                return await interaction.response.send_message("أتوبيس كومبليت تعمل بالفعل في هذه القناة.", ephemeral=True)
            
            letter = random.choice(ARABIC_LETTERS)
            cat = random.choice(BUS_CATEGORIES)
            length = random.randint(3, 5)

            bus_games[cid] = {"letter": letter, "category": cat, "length": length, "host": p.id}
            
            return await interaction.response.send_message(
                embed=games.embed(
                    "أتوبيس كومبليت",
                    f"المطلوب للجميع: **{cat}** بحرف **{letter}** (تتكون من **{length}** أحرف)\n\n"
                    f"أكتب الإجابة في الشات ليتعرف عليها البوت تلقائياً!"
                ),
                view=BusControlView(cid, p.id)
            )

        # لعبة الروليت
        if g == "roulette":
            if cid in roulette_games:
                return await interaction.response.send_message("توجد لعبة روليت تعمل بالفعل.", ephemeral=True)
            
            roulette_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
            view = games.RouletteLobbyView(cid) if hasattr(games, 'RouletteLobbyView') else None
            
            await interaction.response.send_message(
                embed=games.embed(
                    "لعبة الروليت",
                    f"المنشئ: {p.mention}\nاللاعبون: 1\n\nاضغط للانضمام خلال 20 ثانية!"
                ),
                view=view
            )
            if hasattr(games, 'run_roulette_timer'):
                asyncio.create_task(games.run_roulette_timer(cid, interaction.channel, await interaction.original_response(), view))
            return

        # ربط كافة الألعاب المتبقية بالأزرار والدوال المقابلة لها في ملف games.py
        game_views = {
            "mafia": "MafiaLobbyView",
            "chairs": "ChairsLobbyView",
            "country": "CountryGameView",
            "hide": "HideGameView",
            "dice": "DiceGameView",
            "replica": "ReplicaGameView",
            "rps": "RPSGameView",
            "xo": "XOGameView",
            "hotxo": "HotXOGameView",
            "bank": "BankGameView"
        }

        # تشغيل الدالة المباشرة إن وجدت أو إرفاق زر اللعبة (View)
        game_func = getattr(games, f"start_{g}", None)
        if callable(game_func):
            await game_func(interaction)
        elif g in game_views and hasattr(games, game_views[g]):
            view_cls = getattr(games, game_views[g])
            await interaction.response.send_message(
                embed=games.embed(f"لعبة {choice.name}", f"تم بدء لعبة {choice.name} بواسطة {p.mention}!"),
                view=view_cls(cid)
            )
        else:
            await interaction.response.send_message(f"تم بدء لعبة {choice.name}!", ephemeral=True)

    except Exception as e:
        print(f"Error in game_cmd: {e}")

class BusControlView(discord.ui.View):
    def __init__(self, cid, host_id):
        super().__init__(timeout=None)
        self.cid = cid
        self.host_id = host_id

    @discord.ui.button(label="إيقاف اللعبة", style=discord.ButtonStyle.danger)
    async def stop_bus(self, i: discord.Interaction, b: discord.ui.Button):
        if bus_games.pop(self.cid, None):
            await i.response.edit_message(
                embed=games.embed(
                    "تم إيقاف اللعبة",
                    f"تم الإنهاء بواسطة {i.user.mention}",
                    config.COLORS.get("error", 0xFF0000)
                ),
                view=None
            )
        else:
            await i.response.send_message("اللعبة منتهية بالفعل.", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN") or getattr(config, "TOKEN", ""))
