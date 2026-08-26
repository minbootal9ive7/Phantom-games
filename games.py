"""
Nightfall Games - كل الألعاب في ملف واحد
مافيا | الكراسي | عجلة الحظ | أتوبيس كومبليت | البنك
تصميم Glassmorphism داكن نيون - بدون AI - كله كود محلي + أزرار + JSON
"""
import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import time
from datetime import datetime, timedelta

import database as db

MAX_PLAYERS = 20

# ==================== تصميم موحّد (Glassmorphism Colors) ====================

COLORS = {
    "mafia_night": 0x1a1a2e,
    "mafia_day": 0x2d2b42,
    "chairs": 0x0f3460,
    "wheel": 0x2e1a47,
    "bus": 0x16213e,
    "bank": 0x0d1b2a,
    "success": 0x1db954,
    "danger": 0xe63950,
    "warning": 0xf5a623,
    "info": 0x4cc9f0,
    "neutral": 0x232342,
}
FOOTER = "✦ Nightfall Games ✦"


def base_embed(title: str, description: str = "", color_key: str = "neutral") -> discord.Embed:
    embed = discord.Embed(title=title, description=description,
                           color=COLORS.get(color_key, COLORS["neutral"]),
                           timestamp=datetime.now())
    embed.set_footer(text=FOOTER)
    return embed


def player_list(players: list) -> str:
    if not players:
        return "*لا يوجد لاعبين بعد...*"
    return "\n".join(f"• <@{p}>" for p in players)


# ==================== 1) لعبة المافيا ====================

class MafiaJoinView(discord.ui.View):
    def __init__(self, host_id: int):
        super().__init__(timeout=60)
        self.players = [host_id]
        self.message: discord.Message | None = None
        self.started = False

    async def update_embed(self, interaction: discord.Interaction | None = None):
        embed = base_embed(
            "🌙 لعبة المافيا - انضم الآن",
            f"اضغط الزر للانضمام! يبدأ التوزيع خلال 60 ثانية أو عند الاكتمال.\n\n"
            f"**اللاعبون ({len(self.players)}/{MAX_PLAYERS}):**\n{player_list(self.players)}",
            "mafia_night",
        )
        if self.message:
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="🕵️ انضم للعبة", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.started:
            return await interaction.response.send_message("اللعبة بدأت بالفعل!", ephemeral=True)
        if interaction.user.id in self.players:
            return await interaction.response.send_message("أنت منضم بالفعل!", ephemeral=True)
        if len(self.players) >= MAX_PLAYERS:
            return await interaction.response.send_message("اكتمل العدد!", ephemeral=True)
        self.players.append(interaction.user.id)
        await interaction.response.defer()
        await self.update_embed()
        if len(self.players) >= MAX_PLAYERS:
            await self.start_game(interaction)

    @discord.ui.button(label="▶️ ابدأ الآن", style=discord.ButtonStyle.primary)
    async def start_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.players[0]:
            return await interaction.response.send_message("فقط منشئ اللعبة يقدر يبدأ!", ephemeral=True)
        if len(self.players) < 4:
            return await interaction.response.send_message("محتاج 4 لاعبين على الأقل!", ephemeral=True)
        await interaction.response.defer()
        await self.start_game(interaction)

    async def start_game(self, interaction: discord.Interaction):
        self.started = True
        for child in self.children:
            child.disabled = True
        await self.update_embed()

        roles = assign_mafia_roles(self.players)
        game = MafiaGameState(self.players, roles, interaction.channel)
        for uid, role in roles.items():
            try:
                user = await interaction.client.fetch_user(uid)
                await user.send(embed=base_embed(
                    "🎭 دورك في اللعبة",
                    f"دورك هو: **{role}**\n\n{role_description(role)}",
                    "mafia_night",
                ))
            except discord.Forbidden:
                pass
        await game.run_night()


def assign_mafia_roles(players: list) -> dict:
    n = len(players)
    mafia_count = max(1, n // 4)
    shuffled = players.copy()
    random.shuffle(shuffled)
    roles = {}
    for i, uid in enumerate(shuffled):
        if i < mafia_count:
            roles[uid] = "مافيا 🔪"
        elif i == mafia_count:
            roles[uid] = "شرطي 🚓"
        else:
            roles[uid] = "مواطن 👤"
    return roles


def role_description(role: str) -> str:
    return {
        "مافيا 🔪": "هدفك القضاء على المواطنين ليلاً دون أن يتم اكتشافك!",
        "شرطي 🚓": "تقدر تحقق مع لاعب كل ليلة لمعرفة هل هو مافيا أم لا.",
        "مواطن 👤": "شارك في التصويت النهاري لإقصاء المشتبه بهم المافيا!",
    }.get(role, "")


class MafiaGameState:
    def __init__(self, players, roles, channel):
        self.players = players
        self.roles = roles
        self.alive = set(players)
        self.channel = channel

    async def run_night(self):
        embed = base_embed(
            "🌙 الليل نزل...",
            "المافيا يختارون ضحيتهم سراً... النهار سيبدأ خلال لحظات.",
            "mafia_night",
        )
        await self.channel.send(embed=embed)
        await asyncio.sleep(3)

        alive_list = list(self.alive)
        victim = random.choice(alive_list) if alive_list else None
        if victim:
            self.alive.discard(victim)

        await self.run_day(victim)

    async def run_day(self, victim):
        mafia_alive = [p for p in self.alive if self.roles.get(p) == "مافيا 🔪"]
        others_alive = [p for p in self.alive if self.roles.get(p) != "مافيا 🔪"]

        desc = f"💀 تم إقصاء <@{victim}> الليلة الماضية.\n\n" if victim else "لم يحدث شيء الليلة الماضية.\n\n"
        desc += f"**الأحياء ({len(self.alive)}):**\n{player_list(list(self.alive))}"

        if not mafia_alive or not others_alive:
            winner = "المافيا 🔪" if mafia_alive else "المواطنون 👤"
            for p in self.alive:
                db.add_win(p, "mafia")
            embed = base_embed("🏆 انتهت اللعبة!", f"{desc}\n\n**الفائز: {winner}**", "mafia_day")
            await self.channel.send(embed=embed)
            return

        embed = base_embed("☀️ النهار طلع", desc, "mafia_day")
        vote_view = MafiaVoteView(list(self.alive), self)
        msg = await self.channel.send(embed=embed, view=vote_view)
        vote_view.message = msg


class MafiaVoteView(discord.ui.View):
    def __init__(self, alive_players, game: MafiaGameState):
        super().__init__(timeout=45)
        self.votes = {}
        self.game = game
        self.message = None
        for uid in alive_players[:20]:
            self.add_item(MafiaVoteButton(uid))

    async def on_timeout(self):
        if not self.votes:
            return
        tally = {}
        for target in self.votes.values():
            tally[target] = tally.get(target, 0) + 1
        eliminated = max(tally, key=tally.get)
        self.game.alive.discard(eliminated)
        role = self.game.roles.get(eliminated, "؟")
        embed = base_embed(
            "🗳️ نتيجة التصويت",
            f"تم إقصاء <@{eliminated}>!\nكان دوره: **{role}**",
            "danger",
        )
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)
            await self.message.channel.send(embed=embed)
        await self.game.run_night()


class MafiaVoteButton(discord.ui.Button):
    def __init__(self, target_id: int):
        super().__init__(label=f"صوّت لإقصاء", style=discord.ButtonStyle.danger, custom_id=str(target_id))
        self.target_id = target_id

    async def callback(self, interaction: discord.Interaction):
        view: MafiaVoteView = self.view
        if interaction.user.id not in view.game.alive:
            return await interaction.response.send_message("أنت خارج اللعبة!", ephemeral=True)
        view.votes[interaction.user.id] = self.target_id
        await interaction.response.send_message(f"صوّتت لإقصاء <@{self.target_id}>", ephemeral=True)


# ==================== 2) لعبة الكراسي ====================

class ChairsView(discord.ui.View):
    def __init__(self, host_id: int):
        super().__init__(timeout=30)
        self.players = [host_id]
        self.message = None
        self.started = False

    async def update_embed(self):
        embed = base_embed(
            "🪑 لعبة الكراسي - انضم الآن",
            f"اضغط للانضمام! تبدأ الجولة خلال 30 ثانية.\n\n"
            f"**اللاعبون ({len(self.players)}/{MAX_PLAYERS}):**\n{player_list(self.players)}",
            "chairs",
        )
        if self.message:
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="🎟️ انضم", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.started:
            return await interaction.response.send_message("اللعبة بدأت!", ephemeral=True)
        if interaction.user.id in self.players:
            return await interaction.response.send_message("أنت منضم بالفعل!", ephemeral=True)
        if len(self.players) >= MAX_PLAYERS:
            return await interaction.response.send_message("اكتمل العدد!", ephemeral=True)
        self.players.append(interaction.user.id)
        await interaction.response.defer()
        await self.update_embed()

    @discord.ui.button(label="▶️ ابدأ", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.players[0]:
            return await interaction.response.send_message("فقط منشئ اللعبة يقدر يبدأ!", ephemeral=True)
        if len(self.players) < 2:
            return await interaction.response.send_message("محتاج لاعبين اثنين على الأقل!", ephemeral=True)
        self.started = True
        for child in self.children:
            child.disabled = True
        await interaction.response.defer()
        await self.update_embed()
        await run_chairs_round(interaction.channel, self.players.copy())


async def run_chairs_round(channel, players):
    round_num = 1
    while len(players) > 1:
        wait_time = random.uniform(3, 7)
        embed = base_embed(
            f"🪑 الجولة {round_num}",
            f"استعدوا... الكرسي هيفتح بعد لحظات عشوائية!\n\n**اللاعبون المتبقّون:** {len(players)}",
            "chairs",
        )
        await channel.send(embed=embed)
        await asyncio.sleep(wait_time)

        view = ChairsSitView(players)
        embed2 = base_embed("🚨 اجلس الآن!", "اضغط الزر بأسرع وقت!", "warning")
        msg = await channel.send(embed=embed2, view=view)
        view.message = msg
        await asyncio.sleep(3)
        for child in view.children:
            child.disabled = True
        await msg.edit(view=view)

        if not view.clicked_order:
            embed3 = base_embed("😴 محدش جلس!", "هنعيد الجولة...", "warning")
            await channel.send(embed=embed3)
            round_num += 1
            continue

        loser_pool = [p for p in players if p not in view.clicked_order]
        eliminated = random.choice(loser_pool) if loser_pool else view.clicked_order[-1]
        players.remove(eliminated)
        db.add_loss(eliminated, "chairs")
        embed3 = base_embed(
            "💥 خرج من اللعبة",
            f"<@{eliminated}> ما وصلش للكرسي بالوقت!\n\n**المتبقّون ({len(players)}):**\n{player_list(players)}",
            "danger",
        )
        await channel.send(embed=embed3)
        round_num += 1

    if players:
        winner = players[0]
        db.add_win(winner, "chairs")
        db.add_balance(winner, 50)
        embed = base_embed("🏆 الفائز!", f"مبروك <@{winner}>! فزت بـ 50 نقطة 🪙", "success")
        await channel.send(embed=embed)


class ChairsSitView(discord.ui.View):
    def __init__(self, players):
        super().__init__(timeout=5)
        self.players = players
        self.clicked_order = []
        self.message = None

    @discord.ui.button(label="🪑 اجلس الآن!", style=discord.ButtonStyle.danger)
    async def sit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.players:
            return await interaction.response.send_message("أنت مش في اللعبة!", ephemeral=True)
        if interaction.user.id in self.clicked_order:
            return await interaction.response.send_message("جلست بالفعل!", ephemeral=True)
        self.clicked_order.append(interaction.user.id)
        await interaction.response.send_message("جلست بنجاح! ✅", ephemeral=True)


# ==================== 3) عجلة الحظ ====================

WHEEL_PRIZES = [10, 20, 50, 100, 0, 25, 200, 15, 75, 5]


class WheelSpinView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=30)
        self.user_id = user_id

    @discord.ui.button(label="🎡 لف العجلة!", style=discord.ButtonStyle.primary, emoji="✨")
    async def spin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("مش دورك تلف العجلة!", ephemeral=True)
        button.disabled = True
        prize = random.choice(WHEEL_PRIZES)

        spinning_embed = base_embed("🎡 العجلة بتلف...", "🌀 " * 5, "wheel")
        await interaction.response.edit_message(embed=spinning_embed, view=self)
        await asyncio.sleep(2)

        if prize > 0:
            db.add_balance(interaction.user.id, prize)
            desc = f"🎉 مبروك! ربحت **{prize}** نقطة 🪙\n\nرصيدك الجديد: **{db.get_balance(interaction.user.id)}** 🪙"
            color = "success"
        else:
            desc = "💨 للأسف! العجلة وقفت على الصفر... حظ أوفر المرة الجاية!"
            color = "neutral"

        result_embed = base_embed("🎡 نتيجة العجلة", desc, color)
        await interaction.edit_original_response(embed=result_embed, view=self)


# ==================== 4) أتوبيس كومبليت ====================

BUS_CATEGORIES = ["اسم", "حيوان", "جماد", "نبات", "بلد"]
ARABIC_LETTERS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")


class BusGameState:
    def __init__(self, channel, players):
        self.channel = channel
        self.players = players
        self.letter = random.choice(ARABIC_LETTERS)
        self.answers = {}  # user_id -> {category: word}
        self.scores = {p: 0 for p in players}


async def start_bus_game(channel, players):
    game = BusGameState(channel, players)
    embed = base_embed(
        "🚌 أتوبيس كومبليت",
        f"**الحرف المختار: `{game.letter}`**\n\n"
        f"اكتب في الشات إجاباتك بالترتيب التالي مفصولة بفواصل:\n"
        f"`{' , '.join(BUS_CATEGORIES)}`\n\n"
        f"⏱️ عندكم **30 ثانية**!",
        "bus",
    )
    await channel.send(embed=embed)

    def check(m):
        return m.channel.id == channel.id and m.author.id in players and not m.author.bot

    end_time = time.time() + 30
    while time.time() < end_time:
        try:
            remaining = end_time - time.time()
            msg = await channel.client.wait_for("message", check=check, timeout=remaining)
            parts = [p.strip() for p in msg.content.split(",")]
            if len(parts) == len(BUS_CATEGORIES):
                valid = all(w.startswith(game.letter) for w in parts if w)
                if valid:
                    game.answers[msg.author.id] = parts
                    game.scores[msg.author.id] = sum(1 for w in parts if w) * 10
                    await msg.add_reaction("✅")
                else:
                    await msg.add_reaction("❌")
        except asyncio.TimeoutError:
            break

    result_lines = []
    for uid, score in sorted(game.scores.items(), key=lambda x: -x[1]):
        if score > 0:
            db.add_balance(uid, score)
            db.add_win(uid, "bus")
            result_lines.append(f"<@{uid}> — **{score}** نقطة 🪙")
        else:
            db.add_loss(uid, "bus")

    desc = "\n".join(result_lines) if result_lines else "محدش جاوب في الوقت! 😅"
    embed2 = base_embed("📊 نتائج الجولة", f"**الحرف كان: `{game.letter}`**\n\n{desc}", "bus")
    await channel.send(embed=embed2)


class BusJoinView(discord.ui.View):
    def __init__(self, host_id: int):
        super().__init__(timeout=30)
        self.players = [host_id]
        self.message = None
        self.started = False

    async def update_embed(self):
        embed = base_embed(
            "🚌 أتوبيس كومبليت - انضم",
            f"اضغط للانضمام! يبدأ خلال 30 ثانية.\n\n"
            f"**اللاعبون ({len(self.players)}/{MAX_PLAYERS}):**\n{player_list(self.players)}",
            "bus",
        )
        if self.message:
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="🚌 انضم", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.started:
            return await interaction.response.send_message("اللعبة بدأت!", ephemeral=True)
        if interaction.user.id in self.players:
            return await interaction.response.send_message("أنت منضم بالفعل!", ephemeral=True)
        if len(self.players) >= MAX_PLAYERS:
            return await interaction.response.send_message("اكتمل العدد!", ephemeral=True)
        self.players.append(interaction.user.id)
        await interaction.response.defer()
        await self.update_embed()

    @discord.ui.button(label="▶️ ابدأ", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.players[0]:
            return await interaction.response.send_message("فقط منشئ اللعبة يقدر يبدأ!", ephemeral=True)
        if len(self.players) < 1:
            return await interaction.response.send_message("محتاج لاعب واحد على الأقل!", ephemeral=True)
        self.started = True
        for child in self.children:
            child.disabled = True
        await interaction.response.defer()
        await self.update_embed()
        await start_bus_game(interaction.channel, self.players.copy())


# ==================== 5) لعبة البنك (Economy) ====================

DAILY_AMOUNT = 100
DAILY_COOLDOWN_HOURS = 24


def bank_embed(user: discord.User) -> discord.Embed:
    wallet = db.get_wallet(user.id)
    embed = discord.Embed(
        title="💳 البطاقة البنكية الرقمية",
        color=COLORS["bank"],
        timestamp=datetime.now(),
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    embed.add_field(name="💰 الرصيد الحالي", value=f"**{wallet.get('balance', 0)}** 🪙", inline=False)
    embed.set_footer(text=FOOTER)
    return embed


class BankCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="رصيد", description="اعرض رصيدك الحالي")
    async def balance(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=bank_embed(interaction.user))

    @app_commands.command(name="يومية", description="احصل على مكافأتك اليومية")
    async def daily(self, interaction: discord.Interaction):
        wallet = db.get_wallet(interaction.user.id)
        last = wallet.get("last_daily", 0)
        now = time.time()
        cooldown = DAILY_COOLDOWN_HOURS * 3600

        if now - last < cooldown:
            remaining = cooldown - (now - last)
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            embed = base_embed("⏳ لسه بدري", f"لازم تستنى **{hours} ساعة و{minutes} دقيقة** قبل اليومية الجاية.", "warning")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        db.add_balance(interaction.user.id, DAILY_AMOUNT)
        db.set_last_daily(interaction.user.id, now)
        new_balance = db.get_balance(interaction.user.id)
        embed = base_embed(
            "🎁 مكافأة يومية!",
            f"استلمت **{DAILY_AMOUNT}** 🪙\n\nرصيدك الجديد: **{new_balance}** 🪙",
            "success",
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="تحويل", description="حوّل نقاط للاعب آخر")
    @app_commands.describe(العضو="الشخص اللي هتحول له", المبلغ="عدد النقاط")
    async def transfer(self, interaction: discord.Interaction, العضو: discord.Member, المبلغ: int):
        if العضو.id == interaction.user.id:
            return await interaction.response.send_message("مينفعش تحول لنفسك!", ephemeral=True)
        if المبلغ <= 0:
            return await interaction.response.send_message("المبلغ لازم يكون أكبر من صفر!", ephemeral=True)
        success = db.transfer(interaction.user.id, العضو.id, المبلغ)
        if not success:
            embed = base_embed("❌ فشل التحويل", "رصيدك مش كافي!", "danger")
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        embed = base_embed(
            "✅ تم التحويل",
            f"حوّلت **{المبلغ}** 🪙 لـ {العضو.mention}\n\nرصيدك الجديد: **{db.get_balance(interaction.user.id)}** 🪙",
            "success",
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="المتصدرين", description="اعرض قائمة أغنى اللاعبين")
    async def leaderboard(self, interaction: discord.Interaction):
        top = db.get_leaderboard(10)
        if not top:
            embed = base_embed("🏆 المتصدرين", "محدش عنده رصيد لسه!", "bank")
            return await interaction.response.send_message(embed=embed)
        medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
        lines = [f"{medals[i]} <@{uid}> — **{data.get('balance', 0)}** 🪙" for i, (uid, data) in enumerate(top)]
        embed = base_embed("🏆 المتصدرين", "\n".join(lines), "bank")
        await interaction.response.send_message(embed=embed)


# ==================== تسجيل كل الأوامر في البوت ====================

async def setup_games(bot: commands.Bot):
    await bot.add_cog(BankCog(bot))

    @bot.tree.command(name="مافيا", description="ابدأ لعبة المافيا الجماعية")
    async def mafia_cmd(interaction: discord.Interaction):
        view = MafiaJoinView(interaction.user.id)
        embed = base_embed(
            "🌙 لعبة المافيا - انضم الآن",
            f"اضغط الزر للانضمام!\n\n**اللاعبون (1/{MAX_PLAYERS}):**\n{player_list([interaction.user.id])}",
            "mafia_night",
        )
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

    @bot.tree.command(name="كراسي", description="ابدأ لعبة الكراسي الموسيقية")
    async def chairs_cmd(interaction: discord.Interaction):
        view = ChairsView(interaction.user.id)
        embed = base_embed(
            "🪑 لعبة الكراسي - انضم الآن",
            f"اضغط للانضمام!\n\n**اللاعبون (1/{MAX_PLAYERS}):**\n{player_list([interaction.user.id])}",
            "chairs",
        )
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

    @bot.tree.command(name="عجلة", description="لف عجلة الحظ واربح نقاط فورية")
    async def wheel_cmd(interaction: discord.Interaction):
        view = WheelSpinView(interaction.user.id)
        embed = base_embed("🎡 عجلة الحظ", "اضغط الزر عشان تلف العجلة وتربح نقاط فورية! ✨", "wheel")
        await interaction.response.send_message(embed=embed, view=view)

    @bot.tree.command(name="اتوبيس", description="ابدأ لعبة أتوبيس كومبليت")
    async def bus_cmd(interaction: discord.Interaction):
        view = BusJoinView(interaction.user.id)
        embed = base_embed(
            "🚌 أتوبيس كومبليت - انضم",
            f"اضغط للانضمام!\n\n**اللاعبون (1/{MAX_PLAYERS}):**\n{player_list([interaction.user.id])}",
            "bus",
        )
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
