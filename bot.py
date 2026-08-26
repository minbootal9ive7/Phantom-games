import asyncio
import random
import discord
from discord.ext import commands
import config
import games

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

mafia_games = {}
chairs_games = {}
roulette_games = {}
bus_games = {}  # لتخزين جلسات أتوبيس كومبليت النشطة لكل شات

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Bot is online: {bot.user} | Synced {len(synced)} commands")
    except Exception as e:
        print(f"Sync error: {e}")

# =========================================================
# 🎮 نظام تفاعل أتوبيس كومبليت (Listener)
# =========================================================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    cid = message.channel.id
    if cid in bus_games:
        game_data = bus_games[cid]
        target_letter = game_data["letter"].lower()
        content = message.content.strip().lower()

        # التحقق إذا كانت الكلمة تبدأ بالحرف المطلوب
        if content.startswith(target_letter) and len(content) > 1:
            # إيقاف الجلسة الحالية مؤقتاً لتجنب التكرار
            bus_games.pop(cid, None)
            
            # اختيار حرف جديد للسؤال التالي
            new_letter = random.choice("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
            bus_games[cid] = {"letter": new_letter}

            embed_res = games.embed("🎯 إجابة صحيحة!", f"كفو يا {message.author.mention}! الكلمة (`{message.content}`) صحيحة.\n\nالانتقال للسؤال التالي...\nالحرف الجديد: **{new_letter}**", config.COLORS["success"])
            await message.reply(embed=embed_res)
            return

    await bot.process_commands(message)


@bot.tree.command(name="games", description="عرض جميع الألعاب المتاحة")
async def games_cmd(interaction: discord.Interaction):
    text = "\n".join(f"🔹 **{name}**" for name in games.GAMES.values())
    await interaction.response.send_message(embed=games.embed("🎮 ألعاب نايت فول", f"قائمة الألعاب المتاحة:\n\n{text}\n\nاستخدم `/game` لبدء أي لعبة!"))

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

@bot.tree.command(name="game", description="بدء لعبة جديدة")
@discord.app_commands.choices(choice=GAME_CHOICES)
async def game_cmd(interaction: discord.Interaction, choice: discord.app_commands.Choice[str]):
    g, p = choice.value, interaction.user
    
    if g == "roulette":
        cid = interaction.channel_id
        if cid in roulette_games:
            return await interaction.response.send_message("⚠️ هناك لعبة روليت تعمل بالفعل في هذه القناة.", ephemeral=True)
        roulette_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
        return await interaction.response.send_message(embed=games.embed("🎰 لوبي الروليت", f"المنشئ: {p.mention}\nالمشتركين: 1\n\nاضغط Join للانضمام (خلال 10 ثوانٍ)"), view=RouletteLobbyView(cid))

    if g == "dice":
        res, wins = games.roll_dice([p.display_name, "Bot"])
        txt = "\n".join(f"🔸 **{k}**: `{v}`" for k, v in res.items())
        return await interaction.response.send_message(embed=games.embed("🎲 رمي النرد", f"{txt}\n\n🏆 **الفائز:** {', '.join(wins)}", config.COLORS["success"]))

    if g == "mafia":
        cid = interaction.channel_id
        if cid in mafia_games:
            return await interaction.response.send_message("⚠️ لعبة مافيا جارية بالفعل هنا.", ephemeral=True)
        mafia_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
        return await interaction.response.send_message(embed=games.embed("🕵️ لوبي المافيا", f"المنشئ: {p.mention}\nاللاعبين: 1\n\nالحد الأدنى: 4 لاعبين"), view=MafiaView(cid))

    if g == "country":
        c = games.random_country()
        return await interaction.response.send_message(embed=games.embed("🌍 تخمين الدولة", f"ما هي هذه الدولة من خلال العلم؟\n\n# {c['flag']}"), view=CountryView(c))

    if g == "hide":
        seeker, hidden = games.hide_and_seek([p.display_name, "لاعب 2", "لاعب 3", "لاعب 4"])
        return await interaction.response.send_message(embed=games.embed("🙈 الغميضة", f"👁️ **الباحث:** {seeker}\n👥 **المختبئون:**\n" + "".join(f"- {x}\n" for x in hidden)))

    if g == "chairs":
        cid = interaction.channel_id
        if cid in chairs_games:
            return await interaction.response.send_message("⚠️ الكراسي الموسيقية تعمل بالفعل هنا.", ephemeral=True)
        chairs_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False, "round": 0}
        return await interaction.response.send_message(embed=games.embed("🪑 الكراسي الموسيقية", f"المنشئ: {p.mention}\nاللاعبين: 1"), view=ChairsLobbyView(cid))

    if g == "replica":
        return await interaction.response.send_message(embed=games.embed("🎭 ريبليكا", f"الشخصية المختارة:\n# {games.replica([p.display_name, 'لاعب 2', 'لاعب 3'])}"))

    if g == "rps":
        return await interaction.response.send_message(embed=games.embed("✂️ حجر ورقة مقص", "اختر ضربتك:"), view=RPSView())

    if g in ("xo", "hotxo"):
        return await interaction.response.send_message(embed=games.embed("❌ إكس أو", "الدور لـ: X"), view=XoView())

    if g == "bus":
        cid = interaction.channel_id
        letter = random.choice("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
        bus_games[cid] = {"letter": letter}
        return await interaction.response.send_message(embed=games.embed("🚌 أتوبيس كومبليت", f"الحرف المطلـوب: **{letter}**\n\nاكتب كلمة تبدأ بهذا الحرف في الشات بأسرع ما يمكن!"))


# ================= VIEWS =================
class RouletteLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=10)
        self.cid = cid

    @discord.ui.button(label="Join 🎮", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = roulette_games.get(self.cid)
        if not game or game["started"] or interaction.user.id in game["players"]:
            return await interaction.response.send_message("لا يمكنك الانضمام.", ephemeral=True)
        game["players"][interaction.user.id] = interaction.user
        await interaction.response.send_message("✅ تم انضمامك بنجاح!", ephemeral=True)

    async def on_timeout(self):
        game = roulette_games.pop(self.cid, None)
        if not game or len(game["players"]) == 0:
            return
        players_list = list(game["players"].values())
        display_names = [usr.display_name for usr in players_list]
        winner = games.roulette_winner(display_names)
        
        channel = bot.get_channel(self.cid)
        if not channel:
            return

        msg = await channel.send(embed=games.embed("🎰 عجلة الحظ", "جاري التدوير لمدة 10 ثوانٍ..."))
        gif = games.create_roulette_gif(display_names, winner)
        file = discord.File(gif, filename="roulette.gif")
        
        await msg.edit(content="", attachments=[file])
        await asyncio.sleep(10)
        await channel.send(embed=games.embed("🎉 الفائز في الروليت", f"مبروك الفائز:\n# {winner}", config.COLORS["success"]))

class MafiaView(discord.ui.View):
    def __init__(, cid):
        super().__init__(timeout=300)
        self.cid = cid

    @discord.ui.button(label="Join 👥", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = mafia_games.get(self.cid)
        if not game or game["started"] or i.user.id in game["players"]:
            return await i.response.send_message("خطأ في الانضمام.", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("🕵️ لوبي المافيا", f"اللاعبين: {len(game['players'])}"))

    @discord.ui.button(label="Start 🚀", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        game = mafia_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 4:
            return await i.response.send_message("تحتاج إلى 4 لاعبين كحد أدنى.", ephemeral=True)
        game["started"] = True
        roles = games.create_mafia_roles(list(game["players"].keys()))
        for uid, usr in game["players"].items():
            try:
                await usr.send(embed=games.embed("🕵️ دورك في المافيا", f"دورك هو: **{roles.get(uid, 'Citizen')}**"))
            except:
                pass
        mafia_games.pop(self.cid, None)
        await i.response.edit_message(embed=games.embed("🕵️ بدأت المافيا", "تم إرسال الأدوار بالخاص."), view=None)

class ChairsLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=300)
        self.cid = cid

    @discord.ui.button(label="Join 🪑", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = chairs_games.get(self.cid)
        if not game or i.user.id in game["players"]:
            return await i.response.send_message("خطأ", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("🪑 الكراسي الموسيقية", f"اللاعبين: {len(game['players'])}"))

    @discord.ui.button(label="Start 🎶", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        game = chairs_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 2:
            return await i.response.send_message("تحتاج لاعبين اثنين على الأقل.", ephemeral=True)
        game["started"] = True
        await i.response.edit_message(embed=games.embed("🪑 الكراسي", "بدأت الموسيقى!"), view=None)
        asyncio.create_task(run_chairs(self.cid))

async def run_chairs(cid):
    game = chairs_games.get(cid)
    if not game:
        return
    players = list(game["players"].values())
    if len(players) == 1:
        chairs_games.pop(cid, None)
        ch = bot.get_channel(cid)
        if ch:
            return await ch.send(embed=games.embed("🏆 الفائز بالكراسي", f"# {players[0].display_name}", config.COLORS["success"]))
        return
    
    game["round"] += 1
    view = ChairView(cid, len(players) - 1)
    ch = bot.get_channel(cid)
    if ch:
        await ch.send(embed=games.embed(f"الجولة {game['round']}", "الكراسي أقل من اللاعبين - اضغط بسرعة!"), view=view)
    await asyncio.sleep(4)
    view.stop()
    
    loser = next((p for p in players if p.id not in view.taken), None)
    if loser and loser.id in game["players"]:
        del game["players"][loser.id]
        if ch:
            await ch.send(embed=games.embed("❌ خروج", f"خرج اللاعب: {loser.display_name}"))
    await asyncio.sleep(2)
    asyncio.create_task(run_chairs(cid))

class ChairView(discord.ui.View):
    def __init__(self, cid, count):
        super().__init__(timeout=4)
        self.taken = set()
        for i in range(count):
            btn = discord.ui.Button(label=f"كرسي {i+1}", style=discord.ButtonStyle.primary)
            async def cb(interaction: discord.Interaction, b=btn):
                game = chairs_games.get(cid)
                if not game or interaction.user.id not in game["players"] or interaction.user.id in self.taken:
                    return await interaction.response.send_message("ممنوع", ephemeral=True)
                self.taken.add(interaction.user.id)
                b.disabled = True
                await interaction.response.send_message("🪑 جلست!", ephemeral=True)
                try:
                    await interaction.message.edit(view=self)
                except:
                    pass
            btn.callback = cb
            self.add_item(btn)

class XoButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="-", row=x)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        if self.label != "-":
            return await interaction.response.send_message("مأخوذ!", ephemeral=True)
        self.label = "X"
        self.style = discord.ButtonStyle.danger
        await interaction.response.edit_message(view=self.view)

class XoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for x in range(3):
            for y in range(3):
                self.add_item(XoButton(x, y))

class CountryView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=30)
        for choice in data["choices"]:
            btn = discord.ui.Button(label=choice, style=discord.ButtonStyle.secondary)
            async def cb(i: discord.Interaction, ch=choice):
                res = "✅ إجابة صحيحة!" if ch == data["answer"] else "❌ إجابة خاطئة!"
                await i.response.edit_message(embed=games.embed(res, f"الإجابة هي: {data['answer']}"), view=None)
            btn.callback = cb
            self.add_item(btn)

class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        for c in ["حجر", "ورقة", "مقص"]:
            btn = discord.ui.Button(label=c, style=discord.ButtonStyle.primary)
            async def cb(i: discord.Interaction, choice=c):
                bot_c = random.choice(["حجر", "ورقة", "مقص"])
                wins = {"حجر": "مقص", "مقص": "ورقة", "ورقة": "حجر"}
                res = "تعادل 🤝" if choice == bot_c else ("فزت 🎉" if wins[choice] == bot_c else "فاز البوت 🤖")
                await i.response.edit_message(embed=games.embed("✂️ حجر ورقة مقص", f"أنت: {choice}\nالبوت: {bot_c}\n\n**{res}**"), view=None)
            btn.callback = cb
            self.add_item(btn)

bot.run(config.TOKEN)
    
