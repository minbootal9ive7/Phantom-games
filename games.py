import asyncio
import math
import random
from io import BytesIO

import discord
from PIL import Image, ImageDraw, ImageFont

import config


# =========================================================
# الألعاب
# =========================================================

GAMES = {
    "roulette": "🎰 الروليت",
    "mafia": "🕵️ المافيا",
    "country": "🌍 خمن الدولة",
    "hide": "🫣 الغميضة",
    "chairs": "🪑 الكراسي الموسيقية",
    "dice": "🎲 النرد",
    "replica": "🪞 Replica",
    "rps": "✊ حجر ورق مقص",
    "xo": "❌⭕ XO",
    "hotxo": "🔥 Hot XO",
    "bus": "🚌 أتوبيس كومبليت"
}


def embed(title, text, color=None):
    return discord.Embed(
        title=title,
        description=text,
        color=color or config.COLOR
    )


# =========================================================
# 🎰 ROULETTE
# =========================================================

def roulette_gif(players, winner):

    W = H = 600
    C = 300
    R = 235

    count = len(players)
    segment = 360 / count
    winner_i = players.index(winner)

    target = (
        -90
        - (winner_i * segment + segment / 2)
        + 360 * 7
    )

    colors = [
        (237, 66, 69),
        (88, 101, 242),
        (87, 242, 135),
        (254, 231, 92),
        (235, 69, 158),
        (32, 178, 170)
    ]

    try:
        font = ImageFont.truetype(
            "DejaVuSans-Bold.ttf", 18
        )
    except:
        font = ImageFont.load_default()

    frames = []

    for n in range(70):
        p = n / 69
        ease = 1 - (1 - p) ** 4
        rotation = target * ease

        img = Image.new("RGB", (W, H), (18, 18, 25))
        d = ImageDraw.Draw(img)

        for i, name in enumerate(players):
            start = -90 + rotation + i * segment
            end = start + segment

            d.pieslice(
                (C-R, C-R, C+R, C+R),
                start,
                end,
                fill=colors[i % len(colors)],
                outline="white",
                width=2
            )

            a = math.radians(start + segment / 2)
            x = C + math.cos(a) * R * .62
            y = C + math.sin(a) * R * .62

            text = str(name)
            if len(text) > 11:
                text = text[:11] + "…"

            box = d.textbbox((0, 0), text, font=font)
            d.text(
                (x - (box[2]-box[0])/2, y - (box[3]-box[1])/2),
                text,
                fill="white",
                font=font
            )

        d.ellipse(
            (235, 235, 365, 365),
            fill=(20, 20, 28),
            outline="white",
            width=4
        )

        d.text((263, 288), "NIGHTFALL", fill="white", font=font)

        d.polygon([(300, 5), (275, 55), (325, 55)], fill="white")
        frames.append(img)

    out = BytesIO()
    frames[0].save(
        out,
        "GIF",
        save_all=True,
        append_images=frames[1:],
        duration=55,
        loop=0
    )
    out.seek(0)
    return out


async def roulette(interaction):
    players = [
        interaction.user.display_name,
        "Nightfall 🤖",
        "لاعب 2",
        "لاعب 3",
        "لاعب 4",
        "لاعب 5"
    ]
    winner = random.choice(players)

    await interaction.response.send_message(
        embed=embed("🎰 Nightfall Roulette", "🎡 **العجلة بدأت الدوران...**")
    )

    gif = roulette_gif(players, winner)

    await interaction.edit_original_response(
        attachments=[discord.File(gif, "roulette.gif")]
    )

    await asyncio.sleep(4)

    await interaction.followup.send(
        embed=embed("🏆 انتهت الجولة", f"🎰 الفائز هو:\n\n# {winner}", config.SUCCESS)
    )


# =========================================================
# 🕵️ MAFIA
# =========================================================

mafia = {}


class MafiaView(discord.ui.View):

    def __init__(self, channel_id):
        super().__init__(timeout=300)
        self.channel_id = channel_id

    @discord.ui.button(label="انضمام 👤", style=discord.ButtonStyle.success)
    async def join(self, interaction, button):
        game = mafia.get(self.channel_id)
        if not game:
            return await interaction.response.send_message("❌ انتهت اللعبة.", ephemeral=True)

        if interaction.user.id in [p.id for p in game["players"]]:
            return await interaction.response.send_message("⚠️ أنت داخل اللعبة بالفعل.", ephemeral=True)

        if len(game["players"]) >= 12:
            return await interaction.response.send_message("❌ اللعبة ممتلئة.", ephemeral=True)

        game["players"].append(interaction.user)

        players_list = "".join(f"• {p.display_name}\n" for p in game["players"])
        await interaction.response.edit_message(
            embed=embed("🕵️ Nightfall Mafia", f"👥 اللاعبين: **{len(game['players'])}**\n\n{players_list}\nالحد الأدنى: **4**"),
            view=self
        )

    @discord.ui.button(label="بدء ▶️", style=discord.ButtonStyle.primary)
    async def start(self, interaction, button):
        game = mafia.get(self.channel_id)
        if not game:
            return await interaction.response.send_message("❌ انتهت اللعبة.", ephemeral=True)

        if interaction.user.id != game["host"]:
            return await interaction.response.send_message("❌ المضيف فقط يستطيع البدء.", ephemeral=True)

        if len(game["players"]) < 4:
            return await interaction.response.send_message("❌ تحتاج 4 لاعبين على الأقل.", ephemeral=True)

        players = game["players"][:]
        random.shuffle(players)
        roles = {}

        mafia_count = max(1, len(players) // 4)
        for p in players[:mafia_count]:
            roles[p.id] = "🕵️ المافيا"

        remaining = players[mafia_count:]
        if remaining:
            roles[remaining.pop(0).id] = "👨‍⚕️ الطبيب"

        if len(players) >= 6 and remaining:
            roles[remaining.pop(0).id] = "🔎 المحقق"

        for p in remaining:
            roles[p.id] = "👤 مواطن"

        for p in players:
            try:
                await p.send(embed=embed("🕵️ دورك في المافيا", f"🎭 **دورك:**\n\n# {roles[p.id]}\n\n🤫 لا تخبر أي شخص."))
            except:
                pass

        del mafia[self.channel_id]

        await interaction.response.edit_message(
            embed=embed("🕵️ المافيا بدأت!", f"👥 عدد اللاعبين:\n**{len(players)}**\n\n📩 تم إرسال الأدوار في الخاص.\n\n🤫 حظًا سعيدًا!", config.DANGER),
            view=None
        )


# =========================================================
# 🪑 MUSICAL CHAIRS
# =========================================================

chairs = {}


class ChairsLobby(discord.ui.View):

    def __init__(self, channel_id):
        super().__init__(timeout=300)
        self.channel_id = channel_id

    @discord.ui.button(label="انضمام 👤", style=discord.ButtonStyle.success)
    async def join(self, interaction, button):
        game = chairs.get(self.channel_id)
        if not game:
            return await interaction.response.send_message("❌ انتهت اللعبة.", ephemeral=True)

        if interaction.user.id in [p.id for p in game["players"]]:
            return await interaction.response.send_message("⚠️ أنت داخل اللعبة.", ephemeral=True)

        game["players"].append(interaction.user)
        players_list = "".join(f"• {p.display_name}\n" for p in game["players"])

        await interaction.response.edit_message(
            embed=embed("🪑 Musical Chairs", f"🎵 **لوبي الكراسي**\n\n👥 اللاعبين:\n**{len(game['players'])}**\n\n{players_list}\nاضغط **بدء ▶️** عندما تكون جاهزًا."),
            view=self
        )

    @discord.ui.button(label="بدء ▶️", style=discord.ButtonStyle.primary)
    async def start(self, interaction, button):
        game = chairs.get(self.channel_id)
        if not game:
            return await interaction.response.send_message("❌ انتهت اللعبة.", ephemeral=True)

        if interaction.user.id != game["host"]:
            return await interaction.response.send_message("❌ المضيف فقط.", ephemeral=True)

        if len(game["players"]) < 2:
            return await interaction.response.send_message("❌ تحتاج لاعبين على الأقل.", ephemeral=True)

        await interaction.response.edit_message(
            embed=embed("🪑 Musical Chairs", "🎵 **الموسيقى بدأت...**"),
            view=None
        )

        asyncio.create_task(chair_round(interaction.channel))


class ChairButtons(discord.ui.View):

    def __init__(self, channel, count, game_ref):
        super().__init__(timeout=4)
        self.channel = channel
        self.taken = set()
        self.game_ref = game_ref

        for i in range(count):
            button = discord.ui.Button(label=f"🪑 كرسي {i+1}", style=discord.ButtonStyle.primary)

            async def callback(interaction, idx=i, btn=button):
                game = chairs.get(self.channel.id)
                if not game:
                    return

                if interaction.user.id not in [p.id for p in game["players"]]:
                    return await interaction.response.send_message("❌ أنت لست داخل اللعبة.", ephemeral=True)

                if interaction.user.id in self.taken:
                    return await interaction.response.send_message("🪑 أخذت كرسيًا بالفعل!", ephemeral=True)

                if idx in [x[1] for x in self.taken]:
                    return await interaction.response.send_message("❌ هذا الكرسي محجوز!", ephemeral=True)

                self.taken.add((interaction.user.id, idx))
                btn.disabled = True

                await interaction.response.send_message("🪑 **جلست!**", ephemeral=True)
                try:
                    await interaction.message.edit(view=self)
                except:
                    pass

            button.callback = callback
            self.add_item(button)


async def chair_round(channel):
    game = chairs.get(channel.id)
    if not game:
        return

    players = game["players"]

    if len(players) == 1:
        winner = players[0]
        del chairs[channel.id]
        await channel.send(
            embed=embed("🏆 الفائز!", f"# {winner.display_name}\n\n🎉 فاز بـ Musical Chairs!", config.SUCCESS)
        )
        return

    await asyncio.sleep(random.uniform(2.5, 4))
    count = len(players) - 1

    view = ChairButtons(channel, count, game)

    message = await channel.send(
        embed=embed("🚨 توقفت الموسيقى!", f"🪑 **اجلس بسرعة!**\n\nالكراسي: **{count}**\n\n⏱️ الوقت: **4 ثوانٍ**"),
        view=view
    )

    await asyncio.sleep(4)

    seated = {uid for uid, chair in view.taken}
    available = [p for p in players if p.id not in seated]

    if available:
        loser = random.choice(available)
        if loser in game["players"]:
            game["players"].remove(loser)

        await channel.send(
            embed=embed("💀 خرج لاعب!", f"**{loser.display_name}** لم يجد كرسيًا!", config.DANGER)
        )

    view.stop()
    await asyncio.sleep(2)
    asyncio.create_task(chair_round(channel))


# =========================================================
# 🌍 COUNTRY
# =========================================================

countries = [
    ("🇪🇬", "مصر", ["مصر", "اليابان", "فرنسا", "البرازيل"]),
    ("🇯🇵", "اليابان", ["الهند", "اليابان", "كندا", "إسبانيا"]),
    ("🇫🇷", "فرنسا", ["فرنسا", "مصر", "تركيا", "إيطاليا"]),
]


class CountryView(discord.ui.View):

    def __init__(self, data):
        super().__init__(timeout=30)
        flag, answer, choices = data

        for choice in choices:
            button = discord.ui.Button(label=choice, style=discord.ButtonStyle.secondary)

            async def callback(interaction, choice=choice):
                if choice == answer:
                    await interaction.response.edit_message(
                        embed=embed("🎉 صحيح!", f"🏆 الإجابة هي **{answer}**", config.SUCCESS),
                        view=None
                    )
                else:
                    await interaction.response.edit_message(
                        embed=embed("❌ خطأ!", f"الإجابة الصحيحة: **{answer}**", config.DANGER),
                        view=None
                    )

            button.callback = callback
            self.add_item(button)


# =========================================================
# ✊ RPS
# =========================================================

class RPSView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=30)
        choices = ["حجر", "ورق", "مقص"]

        for choice in choices:
            button = discord.ui.Button(label=choice, style=discord.ButtonStyle.primary)

            async def callback(interaction, choice=choice):
                bot_choice = random.choice(choices)
                result = rps(choice, bot_choice)

                await interaction.response.edit_message(
                    embed=embed(
                        "✊ حجر ورق مقص",
                        f"👤 اختيارك: **{choice}**\n\n🤖 Nightfall: **{bot_choice}**\n\n🏆 **{result}**"
                    ),
                    view=None
                )

            button.callback = callback
            self.add_item(button)


def rps(a, b):
    if a == b:
        return "تعادل 🤝"
    wins = {"حجر": "مقص", "مقص": "ورق", "ورق": "حجر"}
    return "أنت الفائز 🏆" if wins[a] == b else "Nightfall فاز 🤖"


# =========================================================
# 🚌 BUS COMPLETE (أتوبيس كومبليت)
# =========================================================

class BusView(discord.ui.View):
    def __init__(self, letter):
        super().__init__(timeout=60)
        self.letter = letter

    @discord.ui.button(label="إرسال كلمة ✍️", style=discord.ButtonStyle.success)
    async def send_word(self, interaction, button):
        await interaction.response.send_message(
            f"✏️ اكتب في الشات كلمة تبدأ بالحرف: **{self.letter}** (تضم: إنسان، حيوان، نبات، جماد، بلاد)",
            ephemeral=True
        )


# =========================================================
# ❌⭕ XO & HOT XO
# =========================================================

class XoButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="⬜", row=x)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        if self.label != "⬜":
            return await interaction.response.send_message("❌ الخانة محجوزة!", ephemeral=True)
        self.label = "❌"
        self.style = discord.ButtonStyle.danger
        await interaction.response.edit_message(view=self.view)


class XoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for x in range(3):
            for y in range(3):
                self.add_item(XoButton(x, y))


# =========================================================
# تشغيل الألعاب
# =========================================================

async def start(interaction, game):

    if game == "roulette":
        return await roulette(interaction)

    if game == "mafia":
        channel_id = interaction.channel_id
        if channel_id in mafia:
            return await interaction.response.send_message("❌ توجد لعبة مافيا بالفعل.", ephemeral=True)

        mafia[channel_id] = {
            "host": interaction.user.id,
            "players": [interaction.user]
        }
        return await interaction.response.send_message(
            embed=embed("🕵️ Nightfall Mafia", f"👑 المضيف:\n**{interaction.user.display_name}**\n\n👥 اللاعبين: **1**\n\nاضغط **انضمام 👤**\n\nالحد الأدنى: **4 لاعبين**"),
            view=MafiaView(channel_id)
        )

    if game == "chairs":
        channel_id = interaction.channel_id
        if channel_id in chairs:
            return await interaction.response.send_message("❌ توجد لعبة كراسي بالفعل.", ephemeral=True)

        chairs[channel_id] = {
            "host": interaction.user.id,
            "players": [interaction.user]
        }
        return await interaction.response.send_message(
            embed=embed("🪑 Musical Chairs", f"👑 المضيف:\n**{interaction.user.display_name}**\n\n👥 اللاعبين: **1**\n\nاضغط **انضمام 👤**\n\nالحد الأدنى: **2**"),
            view=ChairsLobby(channel_id)
        )

    if game == "country":
        data = random.choice(countries)
        return await interaction.response.send_message(
            embed=embed("🌍 خمن الدولة", f"ما الدولة صاحبة العلم؟\n\n# {data[0]}\n\n👇 اختر الإجابة:"),
            view=CountryView(data)
        )

    if game == "rps":
        return await interaction.response.send_message(
            embed=embed("✊ حجر ورق مقص", "اختر حركتك 👇"),
            view=RPSView()
        )

    if game == "dice":
        a = random.randint(1, 6)
        b = random.randint(1, 6)
        winner = interaction.user.display_name if a > b else "Nightfall 🤖" if b > a else "تعادل 🤝"
        return await interaction.response.send_message(
            embed=embed("🎲 النرد", f"👤 **أنت:** `{a}`\n\n🤖 **Nightfall:** `{b}`\n\n🏆 **{winner}**")
        )

    if game == "hide":
        seeker = interaction.user.display_name
        return await interaction.response.send_message(
            embed=embed("🫣 الغميضة", f"👀 الباحث:\n\n# {seeker}\n\n🏃 حاولوا الاختباء!")
        )

    if game == "replica":
        return await interaction.response.send_message(
            embed=embed("🪞 Replica", f"🎯 تم اختيار:\n\n# {interaction.user.display_name}\n\n😂 حاول تقليده!")
        )

    if game in ("xo", "hotxo"):
        return await interaction.response.send_message(
            embed=embed("❌⭕ " + ("XO" if game == "xo" else "Hot XO"), "🎮 اللعبة جاهزة، ابدأ اللعب بالضغط على المربعات!"),
            view=XoView()
        )

    if game == "bus":
        letters = "أبتثجحخدذرزسشصضطظعغفقكلمنهوي"
        selected_letter = random.choice(letters)
        return await interaction.response.send_message(
            embed=embed("🚌 أتوبيس كومبليت", f"الحرف الحائز على الاختيار:\n\n# 【 {selected_letter} 】\n\nتنافسوا الآن وأكملوا الأقسام (إنسان، حيوان، نبات، جماد، بلاد)!"),
            view=BusView(selected_letter)
        )
