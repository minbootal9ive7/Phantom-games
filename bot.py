import random

import discord

from discord.ext import commands

import config
import games


# =========================================================
# إعداد البوت
# =========================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# Embed
# =========================================================

def make_embed(
    title,
    description,
    color=None
):

    if color is None:
        color = config.COLORS["main"]

    return discord.Embed(
        title=title,
        description=description,
        color=color
    )


# =========================================================
# تشغيل البوت
# =========================================================

@bot.event
async def on_ready():

    await bot.tree.sync()

    print(
        f"🌙 تم تشغيل {bot.user}"
    )

    print(
        "🎮 Nightfall Games جاهز!"
    )


# =========================================================
# /العاب
# =========================================================

@bot.tree.command(
    name="العاب",
    description="عرض جميع ألعاب Nightfall"
)
async def games_command(
    interaction: discord.Interaction
):

    text = "\n".join(
        f"> {game}"
        for game in games.GAMES.values()
    )

    await interaction.response.send_message(
        embed=make_embed(
            "🌙 Nightfall Games",
            f"""
🎮 **ألعاب السيرفر**

{text}

استخدم:
`/لعبة`
لبدء لعبة.
"""
        )
    )


# =========================================================
# /مساعدة
# =========================================================

@bot.tree.command(
    name="مساعدة",
    description="عرض مساعدة Nightfall Games"
)
async def help_command(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        embed=make_embed(
            "🌙 Nightfall Games",
            """
🎮 **الأوامر**

`/العاب`
عرض الألعاب.

`/لعبة`
بدء لعبة.

`/مساعدة`
عرض المساعدة.

🌙 استمتع!
"""
        )
    )


# =========================================================
# اختيارات الألعاب
# =========================================================

GAME_CHOICES = [

    discord.app_commands.Choice(
        name="🎰 الروليت",
        value="roulette"
    ),

    discord.app_commands.Choice(
        name="🕵️ المافيا",
        value="mafia"
    ),

    discord.app_commands.Choice(
        name="🌍 خمن الدولة",
        value="country"
    ),

    discord.app_commands.Choice(
        name="🫣 الغميضة",
        value="hide"
    ),

    discord.app_commands.Choice(
        name="🪑 الكراسي",
        value="chairs"
    ),

    discord.app_commands.Choice(
        name="🎲 النرد",
        value="dice"
    ),

    discord.app_commands.Choice(
        name="🪞 Replica",
        value="replica"
    ),

    discord.app_commands.Choice(
        name="✊ حجر ورق مقص",
        value="rps"
    ),

    discord.app_commands.Choice(
        name="❌⭕ XO",
        value="xo"
    ),

    discord.app_commands.Choice(
        name="🔥 Hot XO",
        value="hotxo"
    )
]


# =========================================================
# /لعبة
# =========================================================

@bot.tree.command(
    name="لعبة",
    description="ابدأ لعبة"
)
@discord.app_commands.describe(
    الاختيار="اختر اللعبة"
)
@discord.app_commands.choices(
    الاختيار=GAME_CHOICES
)
async def play_command(
    interaction: discord.Interaction,
    الاختيار: discord.app_commands.Choice[str]
):

    game = الاختيار.value

    player = interaction.user.display_name


    # =====================================================
    # 🎰 الروليت
    # =====================================================

    if game == "roulette":

        # في النسخة الحالية:
        # اللاعب + بوت Nightfall

        players = [
            player,
            "Nightfall 🤖"
        ]

        winner = games.roulette_winner(
            players
        )

        await interaction.response.send_message(
            embed=make_embed(
                "🎰 Nightfall Roulette",
                """
🎡 **العجلة تستعد للدوران...**

🔥 سيتم اختيار الفائز الآن!
"""
            )
        )

        gif = games.create_roulette_gif(
            players,
            winner
        )

        if gif is None:
            return

        file = discord.File(
            gif,
            filename="nightfall_roulette.gif"
        )

        await interaction.edit_original_response(
            content="🎰 **العجلة تدور...**",
            attachments=[file]
        )

        # النتيجة بعد إرسال الـGIF

        await interaction.followup.send(
            embed=make_embed(
                "🏆 انتهت الجولة!",
                f"""
🎰 توقفت العجلة!

👑 **الفائز:**
# {winner}

🌙 **Nightfall Games**
""",
                config.COLORS["success"]
            )
        )

        return


    # =====================================================
    # 🎲 النرد
    # =====================================================

    if game == "dice":

        players = [
            player,
            "Nightfall 🤖"
        ]

        results, winners = games.roll_dice(
            players
        )

        result_text = "\n".join(
            f"🎲 **{name}** → `{number}`"
            for name, number in results.items()
        )

        winners_text = ", ".join(winners)

        await interaction.response.send_message(
            embed=make_embed(
                "🎲 النرد",
                f"""
{result_text}

🏆 **الفائز:**
{winners_text}
""",
                config.COLORS["success"]
            )
        )

        return


    # =====================================================
    # 🕵️ المافيا
    # =====================================================

    if game == "mafia":

        players = [
            player,
            "لاعب 2",
            "لاعب 3",
            "لاعب 4"
        ]

        roles = games.choose_mafia(
            players
        )

        role = roles[player]

        await interaction.response.send_message(
            embed=make_embed(
                "🕵️ المافيا",
                f"""
🌙 بدأت اللعبة!

🎭 **دورك السري:**

# {role}

🤫 لا تخبر أي شخص بدورك!
""",
                config.COLORS["danger"]
            ),
            ephemeral=True
        )

        return


    # =====================================================
    # 🌍 خمن الدولة
    # =====================================================

    if game == "country":

        country = games.random_country()

        view = discord.ui.View(
            timeout=30
        )

        for choice in country["choices"]:

            button = discord.ui.Button(
                label=choice,
                style=discord.ButtonStyle.secondary
            )

            async def callback(
                button_interaction,
                choice=choice
            ):

                correct = (
                    choice == country["name"]
                )

                if correct:

                    title = "🎉 إجابة صحيحة!"

                    description = (
                        f"أحسنت يا "
                        f"**{button_interaction.user.display_name}** 🏆"
                    )

                    color = config.COLORS["success"]

                else:

                    title = "❌ إجابة خاطئة!"

                    description = (
                        f"الإجابة الصحيحة:\n"
                        f"**{country['name']}**"
                    )

                    color = config.COLORS["danger"]

                await button_interaction.response.edit_message(
                    embed=make_embed(
                        title,
                        description,
                        color
                    ),
                    view=None
                )

            button.callback = callback

            view.add_item(button)

        await interaction.response.send_message(
            embed=make_embed(
                "🌍 خمن الدولة",
                f"""
ما هي الدولة صاحبة العلم؟

# {country["flag"]}

👇 اختر الإجابة الصحيحة
"""
            ),
            view=view
        )

        return


    # =====================================================
    # 🫣 الغميضة
    # =====================================================

    if game == "hide":

        players = [
            player,
            "لاعب 2",
            "لاعب 3",
            "لاعب 4"
        ]

        seeker, hidden = games.hide_and_seek(
            players
        )

        hidden_text = "\n".join(
            f"• {name}"
            for name in hidden
        )

        await interaction.response.send_message(
            embed=make_embed(
                "🫣 الغميضة",
                f"""
👀 **الباحث:**
{seeker}

🏃 **المختبئون:**
{hidden_text}
"""
            )
        )

        return


    # =====================================================
    # 🪑 الكراسي
    # =====================================================

    if game == "chairs":

        players = [
            player,
            "لاعب 2",
            "لاعب 3",
            "لاعب 4"
        ]

        winner, eliminated = games.chairs_round(
            players
        )

        await interaction.response.send_message(
            embed=make_embed(
                "🪑 الكراسي",
                f"""
🎵 الموسيقى بدأت...

🪑 **الفائز:**
{winner}

💀 **خرج من الجولة:**
{eliminated}
""",
                config.COLORS["success"]
            )
        )

        return


    # =====================================================
    # 🪞 Replica
    # =====================================================

    if game == "replica":

        players = [
            player,
            "لاعب 2",
            "لاعب 3"
        ]

        target = games.replica(
            players
        )

        await interaction.response.send_message(
            embed=make_embed(
                "🪞 Replica",
                f"""
🎯 اللاعب المختار:

# {target}

😂 حاول تقليده بأفضل طريقة!
"""
            )
        )

        return


    # =====================================================
    # ✊ حجر ورق مقص
    # =====================================================

    if game == "rps":

        choices = [
            "حجر",
            "ورق",
            "مقص"
        ]

        view = discord.ui.View(
            timeout=30
        )

        for choice in choices:

            button = discord.ui.Button(
                label=choice,
                style=discord.ButtonStyle.primary
            )

            async def callback(
                button_interaction,
                choice=choice
            ):

                bot_choice = random.choice(
                    choices
                )

                result = games.rps(
                    choice,
                    bot_choice
                )

                await button_interaction.response.edit_message(
                    embed=make_embed(
                        "✊ حجر ورق مقص",
                        f"""
👤 اختيارك:
**{choice}**

🤖 اختيار Nightfall:
**{bot_choice}**

🏆 **{result}**
"""
                    ),
                    view=None
                )

            button.callback = callback

            view.add_item(button)

        await interaction.response.send_message(
            embed=make_embed(
                "✊ حجر ورق مقص",
                "اختر حركتك 👇"
            ),
            view=view
        )

        return


    # =====================================================
    # ❌⭕ XO
    # =====================================================

    if game == "xo":

        board = games.empty_xo()

        await interaction.response.send_message(
            embed=make_embed(
                "❌⭕ XO",
                """
🎮 **بدأت لعبة XO!**

❌ اللاعب الأول

⭕ اللاعب الثاني

⬜ ⬜ ⬜
⬜ ⬜ ⬜
⬜ ⬜ ⬜
"""
            )
        )

        return


    # =====================================================
    # 🔥 Hot XO
    # =====================================================

    if game == "hotxo":

        board = games.empty_xo()

        await interaction.response.send_message(
            embed=make_embed(
                "🔥 Hot XO",
                """
🔥 **Hot XO**

⬜ ⬜ ⬜
⬜ ⬜ ⬜
⬜ ⬜ ⬜

😈 استعد!
"""
            )
        )

        return


# =========================================================
# تشغيل
# =========================================================

bot.run(config.TOKEN)
