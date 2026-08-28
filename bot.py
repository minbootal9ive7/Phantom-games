import os
import asyncio
import random
import discord
from discord.ext import commands
import config
import games

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

mafia_games, chairs_games, roulette_games, bus_games = {}, {}, {}, {}

ARABIC_LETTERS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
BUS_CATEGORIES = ["اسم", "جماد", "حيوان", "نبات", "بلاد"]

VALID_BUS_WORDS = {
    "اسم": {
        'ا': ["احمد", "ابراهيم", "اسماعيل", "ايمن", "اسامة", "امين", "اسراء", "اية", "امل", "اميرة", "انجي"],
        'ب': ["باسم", "بهاء", "بلال", "بركات", "بدر", "بتول", "بثينة"],
        'ت': ["تامر", "توفيق", "تميم", "تقى", "تحية"],
        'ث': ["ثامر", "ثابت", "ثريا"],
        'ج': ["جمال", "جلال", "جابر", "جهاد", "جميلة", "جومانة"],
        'ح': ["حسن", "حسين", "حامد", "حلمي", "حنان", "حليمة", "حورية"],
        'خ': ["خالد", "خليل", "خميس", "خديجة", "خلود"],
        'د': ["داود", "داليا", "دعاء", "دينا"],
        'ذ': ["ذكي", "ذكريات"],
        'ر': ["رامي", "رجب", "رشدي", "رضا", "رانيا", "رحمة", "ريم"],
        'ز': ["زياد", "زكريا", "زينب", "زهراء", "زينة"],
        'س': ["سامح", "سعيد", "سليم", "سامي", "سارة", "سلوى", "سحر"],
        'ش': ["شريف", "شفيق", "صلاح", "شروق", "شيماء"],
        'ص': ["صلاح", "صقر", "صفاء", "صباح"],
        'ض': ["ضياء", "ضاحي", "ضحى"],
        'ط': ["طارق", "طه", "طلعت", "طيب", "فاطمة"],
        'ظ': ["ظافر", "ظريف", "ظريفة"],
        'ع': ["علي", "عمر", "عثمان", "عصام", "عادل", "عائشة", "عزيزة"],
        'غ': ["غالب", "غسان", "غادة", "غزلان"],
        'ف': ["فهد", "فاروق", "فؤاد", "فاطمة", "فريدة", "فرح"],
        'ق': ["قاسم", "قيس", "قمر"],
        'ك': ["كريم", "كمال", "كاظم", "كريمة", "كندا"],
        'ل': ["لطفي", "لقمان", "ليلى", "لمياء", "لبنى"],
        'م': ["محمد", "محمود", "مصطفى", "معاذ", "مريم", "منى", "مها"],
        'ن': ["نبيل", "ناصر", "نادر", "نورا", "نهى", "نجلاء"],
        'ه': ["هاني", "هشام", "هيثم", "هالة", "هدى", "هند"],
        'و': ["وليد", "وائل", "وحيد", "وداد", "وفاء"],
        'ي': ["يوسف", "ياسر", "يحيى", "ياسمين", "يسرا"]
    },
    "جماد": {
        'ا': ["ابريق", "ابر", "استيكة", "اسطوانة", "اسفنج", "اباجورة"],
        'ب': ["باب", "برطمان", "برج", "برواز", "بطانية", "بطارية"],
        'ت': ["تاج", "تلفزيون", "تليفون", "تفاح", "ترابيزة", "تيشيرت"],
        'ث': ["ثلاجة", "ثوب"],
        'ج': ["جدار", "جرس", "جزمة", "جوارب", "جيتار", "جسر"],
        'ح': ["حزام", "حقيبة", "حائط", "حديد", "حوض", "حبل"],
        'خ': ["خاتم", "خزانة", "خريطة", "خيط", "خلخال", "خشبة"],
        'د': ["درج", "دولاب", "دفتر", "دراجة", "دلو", "درع"],
        'ذ': ["ذهب", "ذراع", "ذيل"],
        'ر': ["راديو", "رسالة", "رمان", "رمح", "رف", "رصاص"],
        'ز': ["زجاجة", "زيت", "زر", "زهرية"],
        'س': ["سجادة", "سيارة", "سرير", "ساعة", "سيف", "سكين"],
        'ش': ["شباك", "شارع", "شاشة", "شمعدان", "شوكة", "شاحن"],
        'ص': ["صندوق", "صواني", "صاروخ", "صنبور", "صخرة"],
        'ض': ["ضوء", "طرد", "ضرس"],
        'ط': ["طاولة", "طائرة", "طوب", "طبلة", "طوق", "طفاية"],
        'ظ': ["ظرف", "ظلال"],
        'ع': ["عقد", "عصا", "علم", "عربة", "عمود", "عطر"],
        'غ': ["غسالة", "غطاء", "غرفة", "غسول"],
        'ف': ["فانوس", "فرن", "فنجان", "فأس", "فستان", "فرشاة"],
        'ق': ["قلم", "قفل", "قدر", "قماش", "قطار", "قارب"],
        'ك': ["كرسي", "كتاب", "كوب", "كتالوج", "كمبيوتر", "كيس"],
        'ل': ["لعبة", "لمبة", "لحاف", "لجام", "لوحة"],
        'م': ["مكتب", "مفتاح", "مقص", "مرآة", "مروحة", "مطرقة"],
        'ن': ["نجفة", "نظارة", "نهر", "وسادة", "نرد"],
        'ه': ["هاتف", "هرم"],
        'و': ["ورقة", "وسام", "وعاء"],
        'ي': ["يد", "يخوت", "يمامة"]
    },
    "حيوان": {
        'ا': ["اسد", "ارنب", "اتان", "افعى", "اخطبوط", "ابل"],
        'ب': ["بطة", "بقرة", "بومة", "باز", "ببر", "بلبل", "ببغاء"],
        'ت': ["تمساح", "ترس", "تيس", "تنين"],
        'ث': ["ثعلب", "ثور", "ثعبان"],
        'ج': ["جمل", "جاموس", "جرو", "جراد"],
        'ح': ["حصان", "حمار", "حوت", "حمام", "حرباء", "حمار وحشي"],
        'خ': ["خروف", "خنزير", "خلد", "خرتيت", "خطاف"],
        'د': ["دب", "دجاجة", "دولفين", "ديك", "ضفدع", "دود"],
        'ذ': ["ذئب", "ذباب"],
        'ر': ["راكون", "رافل", "روبيان"],
        'ز': ["زرافة", "زنبور", "زبابة"],
        'س': ["سلحفاة", "سنجاب", "سمكة", "سبع", "سرطان", "سحلية"],
        'ش': ["شاهين", "شيمبانزي", "شبوط"],
        'ص': ["صقر", "صيصان", "صعوة"],
        'ض': ["ضفدع", "ضبع", "ضب"],
        'ط': ["طاووس", "طائر", "طيطوي"],
        'ظ': ["ظبي", "ظربان"],
        'ع': ["عصفور", "عقرب", "عنزة", "عجل", "عنكبوت"],
        'غ': ["غزال", "غراب", "غوريلا", "غرير"],
        'ف': ["فيل", "فأر", "فهد", "فراشة", "فقمة"],
        'ق': ["قرد", "قط", "قنفذ", "قندس", "قرش"],
        'ك': ["كلب", "كنغر", "كوالا"],
        'ل': ["ليمور"],
        'م': ["ماعز", "معز"],
        'ن': ["نمر", "نسر", "ناقة", "نعامة", "نحلة", "نورس"],
        'ه': ["هدهد", "هامستر", "هراس"],
        'و': ["وعل", "ورل"],
        'ي': ["يمامة", "يعسوب", "يربوع"]
    },
    "نبات": {
        'ا': ["اناناس", "ازهار", "ارز", "انجاص"],
        'ب': ["برتقال", "بصل", "بطاطس", "بامية", "بقدونس"],
        'ت': ["تفاح", "تمر", "تين", "ترمس", "توليب"],
        'ث': ["ثوم"],
        'ج': ["جزر", "جوز", "جوافة", "جرجير", "زنجبيل"],
        'ح': ["حلبة", "حمص", "حناء", "حبق", "حشيش"],
        'خ': ["خيار", "خس", "خوخ", "خردل"],
        'د': ["دراق", "دخن"],
        'ذ': ["ذرة"],
        'ر': ["رمان", "ريحان", "روزماري"],
        'ز': ["زيتون", "زعتر", "زعفران", "زنبق", "زهرة"],
        'س': ["سبانخ", "سمسم", "سنوبر", "سريس"],
        'ش': ["شعير", "شمندر", "شيح", "شبت"],
        'ص': ["صبار", "صندل"],
        'ض': ["ضريع"],
        'ط': ["طماطم", "طحلب"],
        'ظ': ["ظيان"],
        'ع': ["عنب", "عدس", "عناب", "عفص"],
        'غ': ["غار", "غاب", "غرقد"],
        'ف': ["فراولة", "فاصوليا", "فجل", "فلفل", "فول", "فستق"],
        'ق': ["قرفة", "قرع", "قرنفل", "قصب", "قطن", "قمح"],
        'ك': ["كمثرى", "كوسة", "كمون", "كرز", "كرنب", "كنتالوب"],
        'ل': ["ليمون", "لوبيا", "لافاندر", "لبلاب"],
        'م': ["موز", "مانجو", "ملوخية", "نعناع", "مشمش", "ميرمية"],
        'ن': ["نعناع", "نرجس", "نسرين"],
        'ه': ["هليون", "هيل", "هندباء"],
        'و': ["ورد"],
        'ي': ["يوسفي", "ياسمين"]
    },
    "بلاد": {
        'ا': ["اردن", "امريكا", "اسبانيا", "المانيا", "ايطاليا", "امارات", "ايران"],
        'ب': ["بريطانيا", "برازيل", "بلجيكا", "بحرين", "بلغاريا"],
        'ت': ["تركيا", "تونس", "تشاد", "تايوان", "تشيلي", "تايلاند"],
        'ث': ["ثيودسيا"],
        'ج': ["جزائر", "يابان", "جيبوتي", "جامايكا"],
        'ح': ["حبشة"],
        'خ': ["خليج"],
        'د': ["دانمارك", "دبي"],
        'ذ': ["ذمار"],
        'ر': ["روسيا", "رومانيا", "رواندا"],
        'ز': ["زيمبابوي", "زامبيا"],
        'س': ["سعودية", "سودان", "سوريا", "سويسرا", "سنغال", "سنغافورة"],
        'ش': ["صين", "شيلي"],
        'ص': ["صومال", "صربيا"],
        'ض': ["ضفة الغربية"],
        'ط': ["طاجيكستان", "طنجة"],
        'ظ': ["ظفار"],
        'ع': ["عراق", "عمان"],
        'غ': ["غانا", "غواتيمالا", "غينيا"],
        'ف': ["فرنسا", "فلسطين", "فلبين", "فنلندا", "فنزويلا", "فيتنام"],
        'ق': ["قطر", "قبرص", "قيرغيزستان"],
        'ك': ["كويت", "كندا", "كولومبيا", "كوبا", "كينيا", "كاميرون"],
        'ل': ["لبنان", "ليبيا", "لوكسمبورغ", "ليتوانيا", "لاتفيا"],
        'م': ["مصر", "مغرب", "موريتانيا", "ماليزيا", "المكسيك", "مالي"],
        'ن': ["نرويج", "نمسا", "نيبال", "نيجيريا", "نيوزيلندا"],
        'ه': ["هند", "هولندا", "هونج كونج"],
        'و': ["ويلز", "واتيكان"],
        'ي': ["يمن", "يابان", "يونان"]
    }
}

def normalize_arabic(text):
    text = text.strip()
    replacements = {'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ى': 'ي', 'ة': 'ه'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def check_word_validity(word: str, category: str, letter: str) -> bool:
    clean_word = normalize_arabic(word)
    clean_letter = normalize_arabic(letter)
    if not clean_word.startswith(clean_letter):
        return False
    cat_dict = VALID_BUS_WORDS.get(category, {})
    possible_words = cat_dict.get(letter, [])
    normalized_db_words = [normalize_arabic(w) for w in possible_words]
    return clean_word in normalized_db_words

@bot.event
async def on_ready():
    try:
        guild_id = 1527415229279895744
        guild = discord.Object(id=guild_id)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Bot online | Synced {len(synced)} commands to guild {guild_id}.")
    except Exception as e:
        print(f"Sync error: {e}")

async def start_bus_timer(cid, channel):
    await asyncio.sleep(60)
    game = bus_games.get(cid)
    if game and game.get("started", False):
        bus_games.pop(cid, None)
        try:
            await channel.send(embed=games.embed("انتهت اللعبة ⌛", "تم إيقاف أتوبيس كومبليت لعدم وجود تفاعل أو إجابات خلال دقيقة واحدة.", 0xFF0000))
        except:
            pass

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    cid = message.channel.id
    if cid in bus_games:
        g_data = bus_games[cid]
        if g_data.get("started", False) and message.author.id in g_data["players"]:
            content = message.content.strip()
            if not content:
                return
            
            is_valid = check_word_validity(content, g_data["category"], g_data["letter"])

            if is_valid:
                n_letter, n_cat = random.choice(ARABIC_LETTERS), random.choice(BUS_CATEGORIES)
                bus_games[cid].update({"letter": n_letter, "category": n_cat})
                
                if "timer_task" in g_data and g_data["timer_task"]:
                    g_data["timer_task"].cancel()
                
                new_task = asyncio.create_task(start_bus_timer(cid, message.channel))
                bus_games[cid]["timer_task"] = new_task

                await message.reply(
                    embed=games.embed("إجابة صحيحة ✨", f"أحسنت {message.author.mention}! الكلمة (**{message.content}**) صحيحة.\n\nالمطلوب الجديد: **{n_cat}** بحرف **{n_letter}**\n*(لديك دقيقة واحدة للإجابة أو التخطي!)*", config.COLORS["success"]),
                    view=BusGameActiveView(cid)
                )
                return
            else:
                await message.reply("إجابتك غلط")

    await bot.process_commands(message)

# ==================== أمر الإيقاف (Slash Command فقط بدون تكرار) ====================
@bot.tree.command(name="stop", description="إيقاف أي لعبة جارية في هذه الروم")
async def stop_cmd(interaction: discord.Interaction):
    cid = interaction.channel_id
    stopped_any = False
    
    if cid in bus_games:
        if "timer_task" in bus_games[cid] and bus_games[cid]["timer_task"]:
            bus_games[cid]["timer_task"].cancel()
        bus_games.pop(cid, None)
        stopped_any = True
        
    if roulette_games.pop(cid, None): stopped_any = True
    if mafia_games.pop(cid, None): stopped_any = True
    if chairs_games.pop(cid, None): stopped_any = True
    
    if stopped_any:
        await interaction.response.send_message(embed=games.embed("تم إيقاف اللعبة 🛑", f"تم إنهاء جميع الألعاب النشطة في هذه الروم بواسطة {interaction.user.mention}", 0xFF0000))
    else:
        await interaction.response.send_message("لا توجد أي لعبة تعمل حالياً في هذه الروم لإيقافها.", ephemeral=True)
# ====================================================================================

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

# ==================== أمر التشغيل (Slash Command فقط بدون تكرار) ====================
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
                "started": False,
                "timer_task": None
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
# ====================================================================================

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
        
        timer_task = asyncio.create_task(start_bus_timer(self.cid, i.channel))
        game["timer_task"] = timer_task

        await i.response.edit_message(
            embed=games.embed(
                "أتوبيس كومبليت 🚌",
                f"اللاعبون المشاركون: {len(game['players'])}\n\nالمطلوب للجميع: **{game['category']}** بحرف **{game['letter']}**\n\nأكتب الإجابة في الشات ليعرف عليها البوت تلقائياً!\n*(لديك دقيقة واحدة للإجابة أو التخطي)*"
            ),
            view=BusGameActiveView(self.cid)
        )

class BusGameActiveView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=None)
        self.cid = cid

    @discord.ui.button(label="انضمام للعبة 🎯", style=discord.ButtonStyle.success)
    async def join_active(self, i: discord.Interaction, b: discord.ui.Button):
        game = bus_games.get(self.cid)
        if not game or not game["started"]:
            return await i.response.send_message("اللعبة غير نشطة.", ephemeral=True)
        if i.user.id in game["players"]:
            return await i.response.send_message("أنت منضم بالفعل لهذه اللعبة!", ephemeral=True)
        
        game["players"].append(i.user.id)
        await i.response.send_message(f"🎯 انضم {i.user.mention} إلى اللعبة بنجاح!", ephemeral=False)

    @discord.ui.button(label="تخطي السؤال ⏭️", style=discord.ButtonStyle.secondary)
    async def skip_question(self, i: discord.Interaction, b: discord.ui.Button):
        game = bus_games.get(self.cid)
        if not game or not game["started"]:
            return await i.response.send_message("اللعبة غير نشطة.", ephemeral=True)
        
        n_letter, n_cat = random.choice(ARABIC_LETTERS), random.choice(BUS_CATEGORIES)
        game.update({"letter": n_letter, "category": n_cat})

        if "timer_task" in game and game["timer_task"]:
            game["timer_task"].cancel()
        game["timer_task"] = asyncio.create_task(start_bus_timer(self.cid, i.channel))

        await i.response.edit_message(
            embed=games.embed(
                "تم تخطي السؤال ⏭️",
                f"قام {i.user.mention} بتخطي السؤال!\n\nالمطلوب الجديد: **{n_cat}** بحرف **{n_letter}**\n*(لديك دقيقة واحدة للإجابة أو التخطي)*"
            ),
            view=self
        )

    @discord.ui.button(label="إيقاف اللعبة 🛑", style=discord.ButtonStyle.danger)
    async def stop_bus_active(self, i: discord.Interaction, b: discord.ui.Button):
        game = bus_games.get(self.cid)
        if game and "timer_task" in game and game["timer_task"]:
            game["timer_task"].cancel()
            
        if bus_games.pop(self.cid, None):
            await i.response.edit_message(embed=games.embed("تم إيقاف اللعبة", f"تم الإنهاء بواسطة {i.user.mention}", 0xFF0000), view=None)
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
    def __init__(self, cid=None):
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
