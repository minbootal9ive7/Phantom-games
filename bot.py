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

GROK_KEY = os.getenv("GROK_API_KEY") or "xai-ZXurbdLhWK5zCH6BHgUfxW6NZt0JhzT0gXjVNOS1R6KwdNQoWfNqmou52X0DNIY3p8MeRuQAb5S5RUYP"

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

# دالة لتنظيف وتوحيد الأحرف العربية للحرف الأول
def normalize_arabic(text):
    text = text.strip()
    replacements = {
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
        'ى': 'ي', 'ة': 'ه'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# دالة التحقق الذكي والدقيق عبر Grok (تتحقق من النوع والحرف بدون النظر لعدد الحروف)
async def check_word_with_grok(word: str, category: str, letter: str) -> bool:
    try:
        prompt = (
            f"تدقيق دقيق جداً للعبة أتوبيس كومبليت:\n"
            f"الكلمة المقدمة: '{word}'\n"
            f"الفئة المطلوبة: '{category}'\n"
            f"الحرف المطلوب: '{letter}'\n\n"
            f"الشروط:\n"
            f"1. يجب أن تبدأ الكلمة بالحرف '{letter}' (تجاهل التشكيل والهمزات).\n"
            f"2. يجب أن تكون الكلمة بالتأكيد تنتمي لفئة ({category}) فقط.\n"
            f"أمثلة للتدقيق الصارم:\n"
            f"- 'تامر' هو اسم شخص، لذلك إذا كانت الفئة (حيوان) الإجابة 'لا'.\n"
            f"- 'تفاح' هو نبات/فاكهة، إذا كانت الفئة (حيوان) الإجابة 'لا'.\n"
            f"- 'تمساح' هو حيوان ويبدأ بحرف ت، فالإجابة 'نعم'.\n\n"
            f"هل الكلمة '{word}' تلتزم بالشرطين بشكل صحيح 100%؟\n"
            f"أجب بكلمة واحدة فقط: نعم أم لا."
        )
        response = await grok_client.chat.completions.create(
            model="grok-2-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=5
        )
        answer = response.choices[0].message.content.strip()
        print(f"[Grok Check] Word: '{word}' | Cat: '{category}' | Letter: '{letter}' | AI Answer: '{answer}'")
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

        if not content:
            return

        # تحقق أولي محلي: هل يبدأ الحرف بـ الحرف المطلوب (مع توحيد الهمزات)؟
        req_letter = normalize_arabic(g_data["letter"])
        user_first_letter = normalize_arabic(content[0])

        if user_first_letter == req_letter:
            # التحقق الدقيق من الذكاء الاصطناعي على الفئة والنوع
            is_valid = await check_word_with_grok(content, g_data["category"], g_data["letter"])

            if is_valid:
                n_letter = random.choice(ARABIC_LETTERS)
                n_cat = random.choice(BUS_CATEGORIES)

                bus_games[cid].update({"letter": n_letter, "category": n_cat})
                
                await message.reply(
                    embed=games.embed(
                        "إجابة صحيحة ✨",
                        f"أحسنت {message.author.mention}! الكلمة (**{content}**) صحيحة 🎉\n\n"
                        f"المطلوب الجديد: **{n_cat}** بحرف **{n_letter}**",
                        config.COLORS["success"]
                    ),
                    view=BusControlView(cid, g_data["host"])
                )
                return
            else:
                # الكلمة لا تطابق النوع المطلوب (مثلاً اسم بدلاً من حيوان)
                await message.add_reaction("❌")
        else:
            # الحرف الأول غير مطابقة
            await message.add_reaction("❌")

    await bot.process_commands(message)

# أزرار لعبة الروليت
class RouletteLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=20)
        self.cid = cid

    @discord.ui.button(label="انضمام 🎯", style=discord.ButtonStyle.success)
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.cid in roulette_games:
            game = roulette_games[self.cid]
            user = interaction.user
            if user.id not in game["players"]:
                game["players"][user.id] = user
                await interaction.response.send_message(f"🎯 انضم {user.mention} إلى الروليت!", ephemeral=False)
            else:
                await interaction.response.send_message("أنت مضاف في اللعبة بالفعل!", ephemeral=True)
        else:
            await interaction.response.send_message("اللعبة منتهية أو غير موجودة.", ephemeral=True)

    @discord.ui.button(label="إنسحاب ❌", style=discord.ButtonStyle.danger)
    async def leave_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.cid in roulette_games:
            game = roulette_games[self.cid]
            user = interaction.user
            if user.id in game["players"]:
                del game["players"][user.id]
                await interaction.response.send_message(f"❌ انسحب {user.mention} من اللعبة.", ephemeral=False)
            else:
                await interaction.response.send_message("أنت لست مشاركاً في اللعبة.", ephemeral=True)

async def run_roulette_game(cid, channel):
    await asyncio.sleep(20)
    if cid not in roulette_games:
        return
    
    game = roulette_games.pop(cid)
    players = list(game["players"].values())

    if len(players) < 2:
        await channel.send("تم إلغاء لعبة الروليت لعدم اكتمال عدد اللاعبين (مطلوب لاعبين على الأقل).")
        return

    loser = random.choice(players)
    await channel.send(f"💥 **دارت عجلة الروليت...** والخاسر هو: {loser.mention} 💀")

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

        if g == "bus":
            if cid in bus_games:
                return await interaction.response.send_message("أتوبيس كومبليت تعمل بالفعل في هذه القناة.", ephemeral=True)
            
            letter = random.choice(ARABIC_LETTERS)
            cat = random.choice(BUS_CATEGORIES)

            bus_games[cid] = {"letter": letter, "category": cat, "host": p.id}
            
            return await interaction.response.send_message(
                embed=games.embed(
                    "أتوبيس كومبليت 🚌",
                    f"المطلوب للجميع: **{cat}** بحرف **{letter}**\n\n"
                    f"أكتب الكلمة في الشات مباشرة وسيتم التحقق من نوعها وصحتها تلقائياً!"
                ),
                view=BusControlView(cid, p.id)
            )

        if g == "roulette":
            if cid in roulette_games:
                return await interaction.response.send_message("توجد لعبة روليت تعمل بالفعل.", ephemeral=True)
            
            roulette_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
            view = RouletteLobbyView(cid)
            
            await interaction.response.send_message(
                embed=games.embed(
                    "لعبة الروليت 🎰",
                    f"المنشئ: {p.mention}\n\nاضغط على الأزرار بالأسفل للانضمام أو الانسحاب قبل انتهاء الـ 20 ثانية!"
                ),
                view=view
            )
            asyncio.create_task(run_roulette_game(cid, interaction.channel))
            return

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
                
