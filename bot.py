import asyncio
import random
import discord
from discord.ext import commands
import config
import games
from io import BytesIO

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

mafia_games = {}
chairs_games = {}
roulette_games = {}
bus_games = {}

ARABIC_LETTERS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
BUS_CATEGORIES = ["اسم", "جماد", "حيوان", "نبات", "بلاد"]

VALID_BUS_WORDS = {
    "اسم": ["أحمد", "محمد", "علي", "فاطمة", "سارة", "خالد", "عمر", "يوسف", "ابراهيم", "زينب", "مريم", "منى", "ريم", "سعيد", "سالم", "حسن", "حسين", "بلال", "تميم", "حمزة", "أنس", "زياد", "بدر", "تركي", "جابر", "حاتم", "داني", "راجح", "سامي", "طارق", "ظافر", "عادل", "غالب", "فهد", "قاسم", "كريم", "ماجد", "ناصر", "هادي", "وليد", "ياسر"],
    "جماد": ["قلم", "باب", "كتاب", "كرسي", "طاولة", "سيارة", "بيت", "شباك", "ساعة", "جوال", "حاسوب", "مكتب", "سرير", "شاشة", "ثلاجة", "فرن", "وسادة", "غطاء", "حقيبة", "مفتاح", "حائط", "سجادة", "ستارة", "لوحة", "مصباح", "سفينة", "طائرة", "قطار", "صندوق", "عصا"],
    "حيوان": ["أسد", "فهد", "نمر", "ذئب", "ثعلب", "قرد", "فيل", "زرافة", "حصان", "جمل", "بقر", "غنم", "ماعز", "كلب", "قطة", "أرنب", "دب", "تمساح", "ثعبان", "نسر", "صقر", "بومة", "حمامة", "دجاجة", "بطة", "سمكة", "حوت", "قرش", "دولفين", "أطوم"],
    "نبات": ["تفاح", "موز", "برتقال", "عنب", "توت", "رمان", "خوخ", "مشمش", "بطيخ", "شجر", "ورد", "نخل", "قمح", "أرز", "ذرة", "عدس", "فول", "حمص", "نعناع", "بقدونس", "خس", "جزر", "بصل", "ثوم", "بطاطس", "طماطم", "خيار", "ليمون", "تين", "زيتون"],
    "بلاد": ["مصر", "سوريا", "العراق", "اليمن", "ليبيا", "تونس", "المغرب", "الجزائر", "السودان", "قطر", "عمان", "الكويت", "الأردن", "لبنان", "فلسطين", "تركيا", "إيران", "فرنسا", "ألمانيا", "إيطاليا", "إسبانيا", "الصين", "اليابان", "الهند", "روسيا", "البرازيل", "كندا", "أمريكا", "بريطانيا"]
}

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Bot is online: {bot.user} | Synced {len(synced)} commands")
    except Exception as e:
        print(f"Sync error: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    cid = message.channel.id
    if cid in bus_games:
        game_data = bus_games[cid]
        target_letter = game_data["letter"]
        target_cat = game_data["category"]
        target_length = game_data["length"]
        content = message.content.strip()

        is_length_match = (len(content) == target_length)
        is_letter_match = content.startswith(target_letter)
        
        category_words = VALID_BUS_WORDS.get(target_cat, [])
        is_valid_word = (content in category_words) or (is_letter_match and is_length_match and len(content) >= 3)

        if is_letter_match and is_length_match and is_valid_word:
            new_letter = random.choice(ARABIC_LETTERS)
            new_cat = random.choice(BUS_CATEGORIES)
            new_length = random.randint(3, 5)
            
            bus_games[cid]["letter"] = new_letter
            bus_games[cid]["category"] = new_cat
            bus_games[cid]["length"] = new_length

            embed_res = games.embed(
                "إجابة صحيحة", 
                f"أحسنت {message.author.mention}! الكلمة ({message.content}) صحيحة ومطابقة للشروط.\n\nالسؤال الجديد:\nالمطلوب: **{new_cat}** بحرف **{new_letter}** (تتكون من **{new_length}** أحرف)\n\nاستمروا في الكتابة أو اضغطوا على زر الإيقاف أدناه.", 
                config.COLORS["success"]
            )
            
            view = BusControlView(cid, game_data["host"])
            await message.reply(embed=embed_res, view=view)
            return
        else:
            if len(content) > 0 and (not is_letter_match or not is_length_match or not is_valid_word):
                reason = ""
                if not is_letter_match:
                    reason = f"لا تبدأ بالحرف **{target_letter}**."
                elif not is_length_match:
                    reason = f"لا تتكون من **{target_length}** أحرف تماماً."
                else:
                    reason = "الكلمة غير صحيحة أو غير متوافقة مع الفئة المطلوبة."
                    
                embed_err = games.embed("إجابة خاطئة", f"خطأ: {reason}", config.COLORS.get("error", 0xFF0000))
                await message.reply(embed=embed_err, delete_after=3)
                return

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
        g, p = choice.value, interaction.user
        
        if g == "roulette":
            cid = interaction.channel_id
            if cid in roulette_games:
                return await interaction.response.send_message("تنبيه: توجد لعبة روليت تعمل بالفعل في هذه الروم.", ephemeral=True)
            
            roulette_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
            
            view = RouletteLobbyView(cid)
            await interaction.response.send_message(
                embed=games.embed("لعبة الروليت", f"المنشئ: {p.mention}\nاللاعبون: 1\n\nاضغط على زر الانضمام للمشاركة خلال 20 ثانية"),
                view=view
            )
            msg = await interaction.original_response()
            asyncio.create_task(run_roulette_timer(cid, interaction.channel, msg, view))
            return

        if g == "dice":
            res, wins = games.roll_dice([p.display_name, "البوت"])
            txt = "\n".join(f"**{k}**: `{v}`" for k, v in res.items())
            return await interaction.response.send_message(embed=games.embed("رمي النرد", f"{txt}\n\nالفائز: {', '.join(wins)}", config.COLORS["success"]))

        if g == "mafia":
            cid = interaction.channel_id
            if cid in mafia_games:
                return await interaction.response.send_message("تنبيه: توجد لعبة مافيا تعمل بالفعل هنا.", ephemeral=True)
            mafia_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
            return await interaction.response.send_message(embed=games.embed("لعبة المافيا", f"المنشئ: {p.mention}\nاللاعبون: 1\n\nالحد الأدنى المطلوب: 4 لاعبين"), view=MafiaView(cid))

        if g == "country":
            c = games.random_country()
            return await interaction.response.send_message(embed=games.embed("احزر الدولة", f"ما هي الدولة التي يتبعها هذا العلم؟\n\n{c['flag']}"), view=CountryView(c))

        if g == "hide":
            seeker, hidden = games.hide_and_seek([p.display_name, "اللاعب 2", "اللاعب 3", "اللاعب 4"])
            return await interaction.response.send_message(embed=games.embed("لعبة الاختباء", f"الباحث: {seeker}\nالمختبئون:\n" + "".join(f"- {x}\n" for x in hidden)))

        if g == "chairs":
            cid = interaction.channel_id
            if cid in chairs_games:
                return await interaction.response.send_message("تنبيه: الكراسي تعمل بالفعل هنا.", ephemeral=True)
            chairs_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False, "round": 0}
            return await interaction.response.send_message(embed=games.embed("الكراسي", f"المنشئ: {p.mention}\nاللاعبون: 1"), view=ChairsLobbyView(cid))

        if g == "replica":
            return await interaction.response.send_message(embed=games.embed("لعبة النسخة", f"الشخصية المختارة:\n{games.replica([p.display_name, 'اللاعب 2', 'اللاعب 3'])}"))

        if g == "rps":
            return await interaction.response.send_message(embed=games.embed("حجر ورقة مقص", "اختر حركتك:"), view=RPSView())

        if g in ("xo", "hotxo"):
            return await interaction.response.send_message(embed=games.embed("لعبة إكس أو", "الدور على: X"), view=XoView())

        if g == "bus":
            cid = interaction.channel_id
            if cid in bus_games:
                return await interaction.response.send_message("تنبيه: لعبة أتوبيس كومبليت تعمل بالفعل في هذه الروم.", ephemeral=True)
                
            letter = random.choice(ARABIC_LETTERS)
            chosen_cat = random.choice(BUS_CATEGORIES)
            chosen_length = random.randint(3, 5)
            
            bus_games[cid] = {"letter": letter, "category": chosen_cat, "length": chosen_length, "host": p.id}
            
            view = BusControlView(cid, p.id)
            return await interaction.response.send_message(
                embed=games.embed("أتوبيس كومبليت", f"المطلوب: **{chosen_cat}** بحرف **{letter}**\n(يجب أن تتكون الكلمة من **{chosen_length}** أحرف صحيحة)\n\nاكتب الإجابة الصحيحة في الشات بأسرع ما يمكنك!"),
                view=view
            )
            
        # Fallback for unhandled games
        await interaction.response.send_message(embed=games.embed("تنبيه", "هذه اللعبة غير متوفرة حالياً أو تحت الصيانة."), ephemeral=True)

    except Exception as e:
        print(f"Error in game_cmd: {e}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("حدث خطأ أثناء تشغيل اللعبة، يجدر بالمطور مراجعة السجلات.", ephemeral=True)
            else:
                await interaction.followup.send("حدث خطأ داخلي أثناء تنفيذ الأمر.", ephemeral=True)
        except:
            pass

# ================= VIEWS & TIMERS =================

class BusControlView(discord.ui.View):
    def __init__(self, cid, host_id):
        super().__init__(timeout=None)
        self.cid = cid
        self.host_id = host_id

    @discord.ui.button(label="إيقاف اللعبة", style=discord.ButtonStyle.danger)
    async def stop_bus(self, interaction: discord.Interaction, button: discord.ui.Button):
        game_data = bus_games.get(self.cid)
        if not game_data:
            return await interaction.response.send_message("اللعبة منتهية بالفعل أو غير مفعلة.", ephemeral=True)
        
        bus_games.pop(self.cid, None)
        for child in self.children:
            child.disabled = True
            
        await interaction.response.edit_message(embed=games.embed("تم إيقاف اللعبة", f"تم إنهاء لعبة أتوبيس كومبليت بواسطة {interaction.user.mention}.", config.COLORS.get("error", 0xFF0000)), view=self)

async def run_roulette_timer(cid, channel, msg, view):
    await asyncio.sleep(20)
    view.stop()
    
    game = roulette_games.pop(cid, None)
    if not game or len(game["players"]) == 0:
        return
        
    players_dict = game["players"]
    players_list = list(players_dict.values())
    
    players_data = []
    for usr in players_list:
        try:
            avatar_img = await games.download_avatar(usr.display_avatar.url)
        except:
            avatar_img = None
        players_data.append({"name": usr.display_name, "user": usr, "avatar": avatar_img})
        
    display_names = [p["name"] for p in players_data]
    winner_name = games.roulette_winner(display_names)
    
    winner_user = next((p["user"] for p in players_data if p["name"] == winner_name), players_list[0])
    winner_avatar = next((p["avatar"] for p in players_data if p["name"] == winner_name), None)
    
    try:
        await msg.delete()
    except:
        pass
    
    try:
        gif = games.create_roulette_gif(players_data, winner_name)
        file = discord.File(gif, filename="roulette.gif")
        spin_msg = await channel.send(embed=games.embed("عجلة الروليت", "جارٍ التدوير..."), file=file)
    except Exception as e:
        print(f"Roulette GIF error: {e}")
        spin_msg = await channel.send(embed=games.embed("عجلة الروليت", f"الفائز هو: **{winner_name}**"))
    
    await asyncio.sleep(6.5)
    
    try:
        await spin_msg.edit(embed=games.embed("عجلة الروليت", "انتهت الدورة واستقررنا على الفائز!"))
    except:
        pass
        
    winner_embed = games.embed("فائز الروليت", f"مبروك للفائز:\n{winner_user.mention}", config.COLORS["success"])
    
    if winner_avatar:
        try:
            avatar_io = BytesIO()
            winner_avatar.save(avatar_io, format="PNG")
            avatar_io.seek(0)
            file_avatar = discord.File(avatar_io, filename="winner.png")
            winner_embed.set_thumbnail(url="attachment://winner.png")
            await channel.send(file=file_avatar, embed=winner_embed)
            return
        except:
            pass
            
    await channel.send(embed=winner_embed)

class RouletteLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=20)
        self.cid = cid

    @discord.ui.button(label="انضمام", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = roulette_games.get(self.cid)
        if not game or game["started"] or interaction.user.id in game["players"]:
            return await interaction.response.send_message("لا يمكنك الانضمام.", ephemeral=True)
        
        game["players"][interaction.user.id] = interaction.user
        count = len(game["players"])
        
        try:
            await interaction.response.edit_message(embed=games.embed("لعبة الروليت", f"المنشئ: <@{game['host']}>\nاللاعبون: {count}\n\nاضغط على زر الانضمام للمشاركة خلال 20 ثانية"))
            await interaction.followup.send("تم الانضمام بنجاح!", ephemeral=True)
        except:
            await interaction.response.send_message("تم الانضمام بنجاح!", ephemeral=True)

class MafiaView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=300)
        self.cid = cid

    @discord.ui.button(label="انضمام", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = mafia_games.get(self.cid)
        if not game or game["started"] or i.user.id in game["players"]:
            return await i.response.send_message("خطأ في الانضمام.", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("لعبة المافيا", f"اللاعبون: {len(game['players'])}"))

    @discord.ui.button(label="بدء", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        game = mafia_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 4:
            return await i.response.send_message("يجب وجود 4 لاعبين كحد أدنى.", ephemeral=True)
        game["started"] = True
        roles = games.create_mafia_roles(list(game["players"].keys()))
        for uid, usr in game["players"].items():
            try:
                await usr.send(embed=games.embed("دورك في المافيا", f"دورك هو: **{roles.get(uid, 'مواطن')}**"))
            except:
                pass
        mafia_games.pop(self.cid, None)
        await i.response.edit_message(embed=games.embed("بدء المافيا", "تم إرسال الأدوار عبر الرسائل الخاصة."), view=None)

class ChairsLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=300)
        self.cid = cid

    @discord.ui.button(label="انضمام", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = chairs_games.get(self.cid)
        if not game or i.user.id in game["players"]:
            return await i.response.send_message("خطأ", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("الكراسي", f"اللاعبون: {len(game['players'])}"))

    @discord.ui.button(label="بدء", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        game = chairs_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 2:
            return await i.response.send_message("مطلوب لاعبين اثنين على الأقل.", ephemeral=True)
        game["started"] = True
        await i.response.edit_message(embed=games.embed("الكراسي", "بدأت الموسيقى!"), view=None)
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
            return await ch.send(embed=games.embed("فائز الكراسي", f"{players[0].display_name}", config.COLORS["success"]))
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
            await ch.send(embed=games.embed("استبعاد", f"تم استبعاد اللاعب: {loser.display_name}"))
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
                    return await interaction.response.send_message("غير مسموح", ephemeral=True)
                self.taken.add(interaction.user.id)
                b.disabled = True
                await interaction.response.send_message("جلست على كرسي!", ephemeral=True)
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
            return await interaction.response.send_message("مأخوذة!", ephemeral=True)
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
                res = "إجابة صحيحة" if ch == data["answer"] else "إجابة خاطئة"
                await i.response.edit_message(embed=games.embed(res, f"الإجابة الصحيحة هي: {data['answer']}"), view=None)
            btn.callback = cb
            self.add_item(btn)

class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        for c in [("حجر", "Rock"), ("ورقة", "Paper"), ("مقص", "Scissors")]:
            btn = discord.ui.Button(label=c[0], style=discord.ButtonStyle.primary)
            async def cb(i: discord.Interaction, choice=c[1]):
                bot_c_val = random.choice(["Rock", "Paper", "Scissors"])
                wins = {"Rock": "Scissors", "Scissors": "Paper", "Paper": "Rock"}
                trans = {"Rock": "حجر", "Paper": "ورقة", "Scissors": "مقص"}
                res = "تعادل" if choice == bot_c_val else ("لقد فزت" if wins[choice] == bot_c_val else "فاز البوت")
                await i.response.edit_message(embed=games.embed("حجر ورقة مقص", f"أنت: {trans[choice]}\nالبوت: {trans[bot_c_val]}\n\n**{res}**"), view=None)
            btn.callback = cb
            self.add_item(btn)

bot.run(config.TOKEN)
                
