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
    "hotxo": "🔥 Hot XO"
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

    # جعل الفائز أمام السهم
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

        # تباطؤ تدريجي
        ease = 1 - (1 - p) ** 4

        rotation = target * ease

        img = Image.new(
            "RGB",
            (W, H),
            (18, 18, 25)
        )

        d = ImageDraw.Draw(img)

        for i, name in enumerate(players):

            start = (
                -90
                + rotation
                + i * segment
            )

            end = start + segment

            d.pieslice(
                (
                    C-R,
                    C-R,
                    C+R,
                    C+R
                ),
                start,
                end,
                fill=colors[i % len(colors)],
                outline="white",
                width=2
            )

            a = math.radians(
                start + segment / 2
            )

            x = C + math.cos(a) * R * .62
            y = C + math.sin(a) * R * .62

            text = str(name)

            if len(text) > 11:
                text = text[:11] + "…"

            box = d.textbbox(
                (0, 0),
                text,
                font=font
            )

            d.text(
                (
                    x - (box[2]-box[0])/2,
                    y - (box[3]-box[1])/2
                ),
                text,
                fill="white",
                font=font
            )

        # المنتصف
        d.ellipse(
            (235, 235, 365, 365),
            fill=(20, 20, 28),
            outline="white",
            width=4
        )

        d.text(
            (263, 288),
            "NIGHTFALL",
            fill="white",
            font=font
        )

        # السهم
        d.polygon(
            [
                (300, 5),
                (275, 55),
                (325, 55)
            ],
            fill="white"
        )

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
        embed=embed(
            "🎰 Nightfall Roulette",
            "🎡 **العجلة بدأت الدوران...**"
        )
    )

    gif = roulette_gif(
        players,
        winner
    )

    await interaction.edit_original_response(
        attachments=[
            discord.File(
                gif,
                "roulette.gif"
            )
        ]
    )

    await asyncio.sleep(4)

    await interaction.followup.send(
        embed=embed(
            "🏆 انتهت الجولة",
            f"🎰 الفائز هو:\n\n# {winner}",
            config.SUCCESS
        )
    )


# =========================================================
# 🕵️ MAFIA
# =========================================================

mafia = {}


class MafiaView(discord.ui.View):

    def __init__(self, channel):

        super().__init__(timeout=300)

        self.channel = channel

    @discord.ui.button(
        label="انضمام 👤",
        style=discord.ButtonStyle.success
    )
    async def join(self, interaction, button):

        game = mafia[self.channel]

        if interaction.user.id in game["players"]:
            return await interaction.response.send_message(
                "⚠️ أنت داخل اللعبة بالفعل.",
                ephemeral=True
            )

        if len(game["players"]) >= 12:
            return await interaction.response.send_message(
                "❌ اللعبة ممتلئة.",
                ephemeral=True
            )

        game["players"].append(
            interaction.user
        )

        await interaction.response.edit_message(
            embed=embed(
                "🕵️ Nightfall Mafia",
                f"""
👥 اللاعبين: **{len(game["players"])}**

{"".join(
    f"• {p.display_name}\n"
    for p in game["players"]
)}

الحد الأدنى: **4**
"""
            ),
            view=self
        )

    @discord.ui.button(
        label="بدء ▶️",
        style=discord.ButtonStyle.primary
    )
    async def start(self, interaction, button):

        game = mafia[self.channel]

        if interaction.user.id != game["host"]:
            return await interaction.response.send_message(
                "❌ المضيف فقط يستطيع البدء.",
                ephemeral=True
            )

        if len(game["players"]) < 4:
            return await interaction.response.send_message(
                "❌ تحتاج 4 لاعبين على الأقل.",
                ephemeral=True
            )

        players = game["players"][:]
        random.shuffle(players)

        roles = {}

        mafia_count = max(
            1,
            len(players) // 4
        )

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
                await p.send(
                    embed=embed(
                        "🕵️ دورك في المافيا",
                        f"""
🎭 **دورك:**

# {roles[p.id]}

🤫 لا تخبر أي شخص.
"""
                    )
                )
            except:
                pass

        del mafia[self.channel]

        await interaction.response.edit_message(
            embed=embed(
                "🕵️ المافيا بدأت!",
                f"""
👥 عدد اللاعبين:
**{len(players)}**

📩 تم إرسال الأدوار في الخاص.

🤫 حظًا سعيدًا!
""",
                config.DANGER
            ),
            view=None
        )


# =========================================================
# 🪑 MUSICAL CHAIRS
# =========================================================

chairs = {}


class ChairsLobby(discord.ui.View):

    def __init__(self, channel):

        super().__init__(timeout=300)

        self.channel = channel

    @discord.ui.button(
        label="انضمام 👤",
        style=discord.ButtonStyle.success
    )
    async def join(self, interaction, button):

        game = chairs[self.channel]

        if interaction.user.id in [
            p.id for p in game["players"]
        ]:
            return await interaction.response.send_message(
                "⚠️ أنت داخل اللعبة.",
                ephemeral=True
            )

        game["players"].append(
            interaction.user
        )

        await interaction.response.edit_message(
            embed=embed(
                "🪑 Musical Chairs",
                f"""
🎵 **لوبي الكراسي**

👥 اللاعبين:
**{len(game["players"])}**

{"".join(
    f"• {p.display_name}\n"
    for p in game["players"]
)}

اضغط **بدء ▶️** عندما تكون جاهزًا.
"""
            ),
            view=self
        )

    @discord.ui.button(
        label="بدء ▶️",
        style=discord.ButtonStyle.primary
    )
    async def start(self, interaction, button):

        game = chairs[self.channel]

        if interaction.user.id != game["host"]:
            return await interaction.response.send_message(
                "❌ المضيف فقط.",
                ephemeral=True
            )

        if len(game["players"]) < 2:
            return await interaction.response.send_message(
                "❌ تحتاج لاعبين على الأقل.",
                ephemeral=True
            )

        await interaction.response.edit_message(
            embed=embed(
                "🪑 Musical Chairs",
                "🎵 **الموسيقى بدأت...**"
            ),
            view=None
        )

        await chair_round(
            self.channel
        )


class ChairButtons(discord.ui.View):

    def __init__(
        self,
        channel,
        count
    ):

        super().__init__(timeout=4)

        self.channel = channel
        self.taken = set()

        for i in range(count):

            button = discord.ui.Button(
                label=f"🪑 كرسي {i+1}",
                style=discord.ButtonStyle.primary
            )

            async def callback(
                interaction,
                i=i
            ):

                game = chairs.get(
                    self.channel
                )

                if not game:
                    return

                if interaction.user.id not in [
                    p.id for p in game["players"]
                ]:
                    return await interaction.response.send_message(
                        "❌ أنت لست داخل اللعبة.",
                        ephemeral=True
                    )

                if interaction.user.id in self.taken:
                    return await interaction.response.send_message(
                        "🪑 أخذت كرسيًا بالفعل!",
                        ephemeral=True
                    )

                if i in [
                    x[1] for x in self.taken
                ]:
                    return await interaction.response.send_message(
                        "❌ هذا الكرسي محجوز!",
                        ephemeral=True
                    )

                self.taken.add(
                    (interaction.user.id, i)
                )

                button.disabled = True

                await interaction.response.send_message(
                    "🪑 **جلست!**",
                    ephemeral=True
                )

                await interaction.message.edit(
                    view=self
                )

            button.callback = callback

            self.add_item(button)


async def chair_round(channel):

    game = chairs.get(channel)

    if not game:
        return

    players = game["players"]

    if len(players) == 1:

        winner = players[0]

        del chairs[channel]

        ch = interaction_channel(channel)

        if ch:
            await ch.send(
                embed=embed(
                    "🏆 الفائز!",
                    f"# {winner.display_name}\n\n🎉 فاز بـ Musical Chairs!",
                    config.SUCCESS
                )
            )

        return

    await asyncio.sleep(
        random.uniform(2.5, 4)
    )

    count = len(players) - 1

    view = ChairButtons(
        channel,
        count
    )

    ch = interaction_channel(channel)

    if not ch:
        return

    message = await ch.send(
        embed=embed(
            "🚨 توقفت الموسيقى!",
            f"""
🪑 **اجلس بسرعة!**

الكراسي: **{count}**

⏱️ الوقت: **4 ثوانٍ**
"""
        ),
        view=view
    )

    await asyncio.sleep(4)

    seated = {
        uid for uid, chair in view.taken
    }

    available = [
        p for p in players
        if p.id not in seated
    ]

    if available:

        loser = random.choice(
            available
        )

        game["players"].remove(
            loser
        )

        await ch.send(
            embed=embed(
                "💀 خرج لاعب!",
                f"**{loser.display_name}** لم يجد كرسيًا!",
                config.DANGER
            )
        )

    view.stop()

    await asyncio.sleep(2)

    await chair_round(channel)


def interaction_channel(channel_id):
    return None


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

            button = discord.ui.Button(
                label=choice
            )

            async def callback(
                interaction,
                choice=choice
            ):

                if choice == answer:

                    await interaction.response.edit_message(
                        embed=embed(
                            "🎉 صحيح!",
                            f"🏆 الإجابة هي **{answer}**",
                            config.SUCCESS
                        ),
                        view=None
                    )

                else:

                    await interaction.response.edit_message(
                        embed=embed(
                            "❌ خطأ!",
                            f"الإجابة الصحيحة: **{answer}**",
                            config.DANGER
                        ),
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

            button = discord.ui.Button(
                label=choice
            )

            async def callback(
                interaction,
                choice=choice
            ):

                bot_choice = random.choice(
                    choices
                )

                result = rps(
                    choice,
                    bot_choice
                )

                await interaction.response.edit_message(
                    embed=embed(
                        "✊ حجر ورق مقص",
                        f"""
👤 اختيارك: **{choice}**

🤖 Nightfall: **{bot_choice}**

🏆 **{result}**
"""
                    ),
                    view=None
                )

            button.callback = callback

            self.add_item(button)


def rps(a, b):

    if a == b:
        return "تعادل 🤝"

    wins = {
        "حجر": "مقص",
        "مقص": "ورق",
        "ورق": "حجر"
    }

    return (
        "أنت الفائز 🏆"
        if wins[a] == b
        else "Nightfall فاز 🤖"
    )


# =========================================================
# تشغيل الألعاب
# =========================================================

async def start(interaction, game):

    if game == "roulette":
        return await roulette(interaction)

    if game == "mafia":

        channel = interaction.channel_id

        if channel in mafia:
            return await interaction.response.send_message(
                "❌ توجد لعبة مافيا بالفعل.",
                ephemeral=True
            )

        mafia[channel] = {
            "host": interaction.user.id,
            "players": [interaction.user]
        }

        return await interaction.response.send_message(
            embed=embed(
                "🕵️ Nightfall Mafia",
                f"""
👑 المضيف:
**{interaction.user.display_name}**

👥 اللاعبين: **1**

اضغط **انضمام 👤**

الحد الأدنى: **4 لاعبين**
"""
            ),
            view=MafiaView(channel)
        )

    if game == "chairs":

        channel = interaction.channel_id

        if channel in chairs:
            return await interaction.response.send_message(
                "❌ توجد لعبة كراسي بالفعل.",
                ephemeral=True
            )

        chairs[channel] = {
            "host": interaction.user.id,
            "players": [interaction.user]
        }

        return await interaction.response.send_message(
            embed=embed(
                "🪑 Musical Chairs",
                f"""
👑 المضيف:
**{interaction.user.display_name}**

👥 اللاعبين: **1**

اضغط **انضمام 👤**

الحد الأدنى: **2**
"""
            ),
            view=ChairsLobby(channel)
        )

    if game == "country":

        data = random.choice(countries)

        return await interaction.response.send_message(
            embed=embed(
                "🌍 خمن الدولة",
                f"""
ما الدولة صاحبة العلم؟

# {data[0]}

👇 اختر الإجابة:
"""
            ),
            view=CountryView(data)
        )

    if game == "rps":

        return await interaction.response.send_message(
            embed=embed(
                "✊ حجر ورق مقص",
                "اختر حركتك 👇"
            ),
            view=RPSView()
        )

    if game == "dice":

        a = random.randint(1, 6)
        b = random.randint(1, 6)

        winner = (
            interaction.user.display_name
            if a > b
            else "Nightfall 🤖"
            if b > a
            else "تعادل 🤝"
        )

        return await interaction.response.send_message(
            embed=embed(
                "🎲 النرد",
                f"""
👤 **أنت:** `{a}`

🤖 **Nightfall:** `{b}`

🏆 **{winner}**
"""
            )
        )

    if game == "hide":

        seeker = interaction.user.display_name

        return await interaction.response.send_message(
            embed=embed(
                "🫣 الغميضة",
                f"""
👀 الباحث:

# {seeker}

🏃 حاولوا الاختباء!
"""
            )
        )

    if game == "replica":

        return await interaction.response.send_message(
            embed=embed(
                "🪞 Replica",
                f"""
🎯 تم اختيار:

# {interaction.user.display_name}

😂 حاول تقليده!
"""
            )
        )

    if game in ("xo", "hotxo"):

        return await interaction.response.send_message(
            embed=embed(
                "❌⭕ " + (
                    "XO"
                    if game == "xo"
                    else "Hot XO"
                ),
                """
⬜ ⬜ ⬜
⬜ ⬜ ⬜
⬜ ⬜ ⬜

🎮 اللعبة جاهزة!
"""
            )
        )
