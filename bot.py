import os
import asyncio
import random
import discord
from discord.ext import commands
import config
import games
from io import BytesIO
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

mafia_games, chairs_games, roulette_games, bus_games = {}, {}, {}, {}

ARABIC_LETTERS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
BUS_CATEGORIES = ["اسم", "جماد", "حيوان", "نبات", "بلاد"]
VALID_BUS_WORDS = {
    "اسم": ["أحمد", "محمد", "علي", "فاطمة", "سارة", "خالد", "عمر", "يوسف", "ابراهيم", "زينب", "مريم", "منى", "ريم", "سعيد", "سالم", "حسن", "حسين", "بلال", "تميم", "حمزة", "أنس", "زياد", "بدر", "تركي", "جابر", "حاتم", "داني", "راجح", "سامي", "طارق", "ظافر", "عادل", "غالب", "فهد", "قاسم", "كريم", "ماجد", "ناصر", "هادي", "وليد", "ياسر"],
    "جماد": ["قلم", "باب", "كتاب", "كرسي", "طاولة", "سيارة", "بيت", "شباك", "ساعة", "جوال", "حاسوب", "مكتب", "سرير", "شاشة", "ثلاجة", "فرن", "وسادة", "غطاء", "حقيبة", "مفتاح", "حائط", "سجادة", "ستارة", "لوحة", "مصباح", "سفينة", "طائرة", "قطار", "صندوق", "عصا"],
    "حيوان": ["أسد", "فهد", "نمر", "ذئب", "ثعلب", "قرد", "فيل", "زرافة", "حصان", "جمل", "بقر", "غنم", "ماعز", "كلب", "قطة", "أرنب", "دب", "تمساح", "ثعبان", "نسر", "صقر", "بومة", "حمامة", "دجاجة", "بطة", "سمكة", "حوت", "قرش", "دولفين", "أطوم"],
    "نبات": ["تفاح", "موز", "برتقال", "عنب", "توت", "رمان", "خوخ", "مشمش", "بطيخ", "شجر", "ورد", "نخل", "قمح", "أرز", "ذرة", "عدس", "فول", "حمص", "نعناع", "بقدونس", "خس", "جزر", "بصل", "ثوم", "بطاطس", "طماطم", "خيار", "ليمون", "تين", "زيتون"],
    "بلاد": ["مصر", "سوريا", "العراق", "اليمن", "ليبيا", "تونس", "المغرب", "الجزائر", "السودان", "قطر", "عمان", "الكويت", "الأردن", "لبنان", "فلسطين", "تركيا", "إيران", "فرنسا", "ألمانيا", "إيطاليا", "إسبانيا", "الصين", "اليابان", "الهند", "روسيا", "البرازيل", "كندا", "أمريكا", "بريطانيا"]
}

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

# دالة التحقق الذكي (تتحقق أولاً من القائمة المحلية المضمنة، وإن لم تكن موجودة تفحص عبر Grok AI)
async def check_word_with_ai(word: str, category: str, letter: str) -> bool:
    clean_word = normalize_arabic(word)
    # التحقق المحلي أولاً من القائمة الكلاسيكية لتوفير السرعة
    if category in VALID_BUS_WORDS:
        for item in VALID_BUS_WORDS[category]:
            if normalize_arabic(item) == clean_word:
                return normalize_arabic(item).startswith(normalize_arabic(letter))

    # إذا لم تكن في القائمة المحلية، يتم الفحص عبر Grok AI
    try:
        prompt = (
            f"تدقيق دقيق جداً للعبة أتوبيس كومبليت:\n"
            f"الكلمة المقدمة: '{word}'\n"
            f"الفئة المطلوبة: '{category}'\n"
            f"الحرف المطلوب: '{letter}'\n\n"
            f"الشروط:\n"
            f"1. يجب أن تبدأ الكلمة بالحرف '{letter}' (تجاهل التشكيل والهمزات والتاء المربوطة والهاء).\n"
            f"2. يجب أن تكون الكلمة بالتأكيد تنتمي لفئة ({category}) فقط بشكل صحيح ومنطقي.\n"
            f"أجب بكلمة واحدة فقط: نعم أم لا."
        )
        response = await grok_client.chat.completions.create(
            model="grok-2-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=5
        )
        answer = response.choices[0].message.content.strip()
        return "نعم" in answer
    except Exception as e:
        print(f"AI Verification Error: {e}")
        return clean_word.startswith(normalize_arabic(letter))

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
        # التحقق من أن اللعبة بدأت وأن الشخص مرسل الرسالة من ضمن اللاعبين المنضمين حصراً
        if g_data.get("started", False) and message.author.id in g_data["players"]:
            content = message.content.strip()
            if not content:
                return
            
            req_letter = normalize_arabic(g_data["letter"])
            user_first_letter = normalize_arabic(content[0])

            if user_first_letter == req_letter:
                is_valid = await check_word_with_ai(content, g_data["category"], g_data["letter"])

                if is_valid:
                    n_letter, n_cat = random.choice(ARABIC_LETTERS), random.choice(BUS_CATEGORIES)
                    bus_games[cid].update({"letter": n_letter, "category": n_cat})
                    await message.reply(
                        embed=games.embed("إجابة صحيحة ✨", f"أحسنت {message.author.mention}! الكلمة (**{message.content}**) صحيحة.\n\nالمطلوب الجديد: **{n_cat}** بحرف **{n_letter}**", config.COLORS["success"]),
                        view=BusControlView(cid, g_data["host"])
                    )
                    return
                else:
                    await message.add_reaction("❌")
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
        if g == "roulette":
            if cid in roulette_games: return await interaction.response.send_message("توجد لعبة روليت تعمل بالفعل.", ephemeral=True)
            roulette_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
            view = RouletteLobbyView(cid)
            await interaction.response.send_message(embed=games.embed("لعبة الروليت", f"المنشئ: {p.mention}\nاللاعبون: 1\n\nيجب أن يكون هناك لاعبان على الأقل لتبدأ العجلة! اضغط للانضمام خلال 20 ثانية"), view=view)
            asyncio.create_task(run_roulette_timer(cid, interaction.channel, await interaction.original_response(), view))
            return
        if g == "dice":
            res, wins = games.roll_dice([p.display_name, "البوت"])
            return await interaction.response.send_message(embed=games.embed("رمي النرد", f"\n".join(f"**{k}**: `{v}`" for k, v in res.items()) + f"\n\nالفائز: {', '.join(wins)}", config.COLORS["success"]))
        if g == "mafia":
            if cid in mafia_games: return await interaction.response.send_message("توجد لعبة مافيا تعمل بالفعل.", ephemeral=True)
            mafia_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
            return await interaction.response.send_message(embed=games.embed("لعبة المافيا", f"المنشئ: {p.mention}\nالحد الأدنى: 4 لاعبين"), view=MafiaView(cid))
        if g == "country":
            c = games.random_country()
            return await interaction.response.send_message(embed=games.embed("احزر الدولة", f"ما هي الدولة التي يتبعها هذا العلم؟\n\n{c['flag']}"), view=CountryView(c))
        if g == "hide":
            seeker, hidden = games.hide_and_seek([p.display_name, "اللاعب 2", "اللاعب 3", "اللاعب 4"])
            return await interaction.response.send_message(embed=games.embed("لعبة الاختباء", f"الباحث: {seeker}\nالمختبئون:\n" + "".join(f"- {x}\n" for x in hidden)))
        if g == "chairs":
            if cid in chairs_games: return await interaction.response.send_message("لعبة الكراسي تعمل بالفعل.", ephemeral=True)
            chairs_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False, "round": 0}
            return await interaction.response.send_message(embed=games.embed("الكراسي", f"المنشئ: {p.mention}"), view=ChairsLobbyView(cid))
        if g == "replica":
            return await interaction.response.send_message(embed=games.embed("لعبة النسخة", f"الشخصية المختارة:\n{games.replica([p.display_name, 'اللاعب 2', 'اللاعب 3'])}"))
        if g == "rps":
            return await interaction.response.send_message(embed=games.embed("حجر ورقة مقص", "اختر حركتك:"), view=RPSView())
        if g in ("xo", "hotxo"):
            return await interaction.response.send_message(embed=games.embed("لعبة إكس أو", "الدور على: X"), view=XoView())
        if g == "bus":
            if cid in bus_games: return await interaction.response.send_message("أتوبيس كومبليت يعمل بالفعل.", ephemeral=True)
            letter, cat = random.choice(ARABIC_LETTERS), random.choice(BUS_CATEGORIES)
            bus_games[cid] = {
                "letter": letter, 
                "category": cat, 
                "host": p.id, 
                "players": [p.id], 
                "started": False
            }
            return await interaction.response.send_message(
                embed=games.embed("تجهيز أتوبيس كومبليت 🚌", f"أنشأ {p.mention} لعبة جديدة!\n\nاضغط على زر **انضمام 🎯** للمشاركة، وعند الانتهاء اضغط **بدء اللعبة ▶️**"), 
                view=BusLobbyView(cid, p.id)
            )
        
        await interaction.response.send_message(embed=games.embed("تنبيه", "هذه اللعبة غير متوفرة حالياً."), ephemeral=True)
    except Exception as e:
        print(f"Error in game_cmd: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("حدث خطأ أثناء تشغيل اللعبة.", ephemeral=True)

# واجهة لوبي أتوبيس كومبليت بالزرار
class BusLobbyView(discord.ui.View):
    def __init__(self, cid, host_id):
        super().__init__(timeout=120)
        self.cid, self.host_id = cid, host_id

    @discord.ui.button(label="انضمام 🎯", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = bus_games.get(self.cid)
        if not game or game["started"]:
            return await i.response.send_message("انتهت اللعبة أو بدأت بالفعل.", ephemeral=True)
        if i.user.id in game["players"]:
            return await i.response.send_message("أنت منضم بالفعل!", ephemeral=True)
        
        game["players"].append(i.user.id)
        await i.response.send_message(f"🎯 انضم {i.user.mention} إلى أتوبيس كومبليت!", ephemeral=False)

    @discord.ui.button(label="بدء اللعبة ▶️", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        if i.user.id != self.host_id:
            return await i.response.send_message("فقط منشئ اللعبة يستطيع البدء!", ephemeral=True)
        game = bus_games.get(self.cid)
        if not game:
            return await i.response.send_message("اللعبة غير موجودة.", ephemeral=True)
        
        game["started"] = True
        await i.response.edit_message(
            embed=games.embed(
                "أتوبيس كومبليت 🚌",
                f"اللاعبون المشاركون: {len(game['players'])}\n\nالمطلوب للجميع: **{game['category']}** بحرف **{game['letter']}**\n\nأكتب الإجابة في الشات ليتعرف عليها البوت تلقائياً (للاعبين المنضمين فقط)!"
            ),
            view=BusControlView(self.cid, self.host_id)
        )

class BusControlView(discord.ui.View):
    def __init__(self, cid, host_id):
        super().__init__(timeout=None)
        self.cid, self.host_id = cid, host_id
    @discord.ui.button(label="إيقاف اللعبة", style=discord.ButtonStyle.danger)
    async def stop_bus(self, i: discord.Interaction, b: discord.ui.Button):
        if bus_games.pop(self.cid, None):
            await i.response.edit_message(embed=games.embed("تم إيقاف اللعبة", f"تم الإنهاء بواسطة {i.user.mention}", config.COLORS.get("error", 0xFF0000)), view=None)
        else:
            await i.response.send_message("اللعبة منتهية بالفعل.", ephemeral=True)

async def run_roulette_timer(cid, channel, msg, view):
    await asyncio.sleep(20)
    view.stop()
    game = roulette_games.pop(cid, None)
    if not game or not game["players"]: return
    
    players_list = list(game["players"].values())
    
    try: await msg.delete()
    except: pass

    if len(players_list) < 2:
        await channel.send(embed=games.embed("إلغاء الروليت", "تم إلغاء اللعبة لعدم اكتمال الحد الأدنى من اللاعبين (مطلوب لاعبان على الأقل)."))
        return

    players_data = []
    for usr in players_list:
        try: img = await games.download_avatar(usr.display_avatar.url)
        except: img = None
        players_data.append({"name": usr.display_name, "user": usr, "avatar": img})
    
    winner_name = games.roulette_winner([p["name"] for p in players_data])
    winner_user = next((p["user"] for p in players_data if p["name"] == winner_name), players_list[0])

    try:
        spin_msg = await channel.send(embed=games.embed("عجلة الروليت", "جارٍ التدوير..."), file=discord.File(games.create_roulette_gif(players_data, winner_name), filename="roulette.gif"))
    except:
        spin_msg = await channel.send(embed=games.embed("عجلة الروليت", f"الفائز: **{winner_name}**"))
    
    await asyncio.sleep(7)
    
    try: await spin_msg.delete()
    except: pass

    await channel.send(
        embed=games.embed("فائز الروليت", f"مبروك للفائز:\n{winner_user.mention}\n\nهل تريدون إعادة اللعبة؟", config.COLORS["success"]),
        view=RouletteRestartView()
    )

class RouletteRestartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="إعادة اللعبة 🔄", style=discord.ButtonStyle.success)
    async def restart(self, i: discord.Interaction, b: discord.ui.Button):
        cid = i.channel_id
        if cid in roulette_games:
            return await i.response.send_message("توجد لعبة روليت تعمل بالفعل.", ephemeral=True)
        
        roulette_games[cid] = {"host": i.user.id, "players": {i.user.id: i.user}, "started": False}
        view = RouletteLobbyView(cid)
        
        await i.response.edit_message(embed=games.embed("لعبة الروليت", f"تم إعادة فتح اللعبة بواسطة {i.user.mention}\nاللاعبون: 1\n\nيجب أن يكون هناك لاعبان على الأقل لتبدأ العجلة! اضغط للانضمام خلال 20 ثانية"), view=view)
        asyncio.create_task(run_roulette_timer(cid, i.channel, await i.original_response(), view))

    @discord.ui.button(label="إنهاء ❌", style=discord.ButtonStyle.danger)
    async def stop_game(self, i: discord.Interaction, b: discord.ui.Button):
        await i.response.edit_message(embed=games.embed("انتهت اللعبة", "شكراً لكم على اللعب!"), view=None)

class RouletteLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=20)
        self.cid = cid
    @discord.ui.button(label="انضمام", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = roulette_games.get(self.cid)
        if not game or game["started"] or i.user.id in game["players"]: return await i.response.send_message("لا يمكنك الانضمام.", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("لعبة الروليت", f"المنشئ: <@{game['host']}>\nاللاعبون: {len(game['players'])}\n\n(مطلوب لاعبان على الأقل لبدء الدوران)"))
        await i.followup.send("تم الانضمام!", ephemeral=True)

class MafiaView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=300)
        self.cid = cid
    @discord.ui.button(label="انضمام", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = mafia_games.get(self.cid)
        if not game or game["started"] or i.user.id in game["players"]: return await i.response.send_message("خطأ", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("لعبة المافيا", f"اللاعبون: {len(game['players'])}"))
    @discord.ui.button(label="بدء", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        game = mafia_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 4: return await i.response.send_message("مطلوب 4 لاعبين كحد أدنى.", ephemeral=True)
        game["started"] = True
        roles = games.create_mafia_roles(list(game["players"].keys()))
        for uid, usr in game["players"].items():
            try: await usr.send(embed=games.embed("دورك في المافيا", f"دورك: **{roles.get(uid, 'مواطن')}**"))
            except: pass
        mafia_games.pop(self.cid, None)
        await i.response.edit_message(embed=games.embed("بدء المافيا", "تم إرسال الأدوار بالخاص."), view=None)

class ChairsLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=300)
        self.cid = cid
    @discord.ui.button(label="انضمام", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = chairs_games.get(self.cid)
        if not game or i.user.id in game["players"]: return await i.response.send_message("خطأ", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("الكراسي", f"اللاعبون: {len(game['players'])}"))
    @discord.ui.button(label="بدء", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        game = chairs_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 2: return await i.response.send_message("مطلوب لاعبين اثنين على الأقل.", ephemeral=True)
        game["started"] = True
        await i.response.edit_message(embed=games.embed("الكراسي", "بدأت الموسيقى!"), view=None)
        asyncio.create_task(run_chairs(self.cid))

async def run_chairs(cid):
    game = chairs_games.get(cid)
    if not game: return
    players = list(game["players"].values())
    if len(players) == 1:
        chairs_games.pop(cid, None)
        ch = bot.get_channel(cid)
        if ch: await ch.send(embed=games.embed("فائز الكراسي", f"{players[0].display_name}", config.COLORS["success"]))
        return
    game["round"] += 1
    view = ChairView(cid, len(players) - 1)
    ch = bot.get_channel(cid)
    if ch: await ch.send(embed=games.embed(f"الجولة {game['round']}", "اضغط بسرعة على الكرسي!"), view=view)
    await asyncio.sleep(4)
    view.stop()
    loser = next((p for p in players if p.id not in view.taken), None)
    if loser and loser.id in game["players"]:
        del game["players"][loser.id]
        if ch: await ch.send(embed=games.embed("استبعاد", f"تم استبعاد: {loser.display_name}"))
    await asyncio.sleep(2)
    asyncio.create_task(run_chairs(cid))

class ChairView(discord.ui.View):
    def __init__(self, cid, count):
        super().__init__(timeout=4)
        self.taken = set()
        for idx in range(count):
            btn = discord.ui.Button(label=f"كرسي {idx+1}", style=discord.ButtonStyle.primary)
            async def cb(i: discord.Interaction, b=btn):
                game = chairs_games.get(cid)
                if not game or i.user.id not in game["players"] or i.user.id in self.taken: return await i.response.send_message("غير مسموح", ephemeral=True)
                self.taken.add(i.user.id)
                b.disabled = True
                await i.response.send_message("جلست على كرسي!", ephemeral=True)
                try: await i.message.edit(view=self)
                except: pass
            btn.callback = cb
            self.add_item(btn)

class XoButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="-", row=x)
    async def callback(self, i: discord.Interaction):
        if self.label != "-": return await i.response.send_message("مأخوذة!", ephemeral=True)
        self.label, self.style = "X", discord.ButtonStyle.danger
        await i.response.edit_message(view=self.view)

class XoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for x in range(3):
            for y in range(3): self.add_item(XoButton(x, y))

class CountryView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=30)
        for choice in data["choices"]:
            btn = discord.ui.Button(label=choice, style=discord.ButtonStyle.secondary)
            async def cb(i: discord.Interaction, ch=choice):
                res = "إجابة صحيحة" if ch == data["answer"] else "إجابة خاطئة"
                await i.response.edit_message(embed=games.embed(res, f"الإجابة الصحيحة: {data['answer']}"), view=None)
            btn.callback = cb
            self.add_item(btn)

class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        for c in [("حجر", "Rock"), ("ورقة", "Paper"), ("مقص", "Scissors")]:
            btn = discord.ui.Button(label=c[0], style=discord.ButtonStyle.primary)
            async def cb(i: discord.Interaction, choice=c[1]):
                bot_c = random.choice(["Rock", "Paper", "Scissors"])
                wins = {"Rock": "Scissors", "Scissors": "Paper", "Paper": "Rock"}
                trans = {"Rock": "حجر", "Paper": "ورقة", "Scissors": "مقص"}
                res = "تعادل" if choice == bot_c else ("لقد فزت" if wins[choice] == bot_c else "فاز البوت")
                await i.response.edit_message(embed=games.embed("حجر ورقة مقص", f"أنت: {trans[choice]}\nالبوت: {trans[bot_c]}\n\n**{res}**"), view=None)
            btn.callback = cb
            self.add_item(btn)

bot.run(config.TOKEN)
