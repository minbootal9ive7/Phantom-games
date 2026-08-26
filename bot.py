
import asyncio, random, discord
from discord.ext import commands
import config, games

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

mafia_games, chairs_games = {}, {}

def make_embed(title, description, color=None):
    return discord.Embed(title=title, description=description, color=color or config.COLORS["main"])

@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"🌙 Bot is online: {bot.user} | Synced {len(synced)} commands")

@bot.tree.command(name="games", description="Show all games")
async def games_cmd(interaction: discord.Interaction):
    text = "\n".join(f"> {name}" for name in games.GAMES.values())
    await interaction.response.send_message(embed=make_embed("🌙 Nightfall Games", f"🎮 **Available Games**\n\n{text}\n\n👇 Use `/game`"))

GAME_CHOICES = [
    discord.app_commands.Choice(name="🎰 Roulette", value="roulette"),
    discord.app_commands.Choice(name="🕵️ Mafia", value="mafia"),
    discord.app_commands.Choice(name="🌍 Country", value="country"),
    discord.app_commands.Choice(name="🫣 Hide & Seek", value="hide"),
    discord.app_commands.Choice(name="🪑 Chairs", value="chairs"),
    discord.app_commands.Choice(name="🎲 Dice", value="dice"),
    discord.app_commands.Choice(name="🪞 Replica", value="replica"),
    discord.app_commands.Choice(name="✊ RPS", value="rps"),
    discord.app_commands.Choice(name="❌⭕ XO", value="xo"),
    discord.app_commands.Choice(name="🔥 Hot XO", value="hotxo"),
    discord.app_commands.Choice(name="🚌 Bus Complete", value="bus")
]

@bot.tree.command(name="game", description="Start a game")
@discord.app_commands.choices(choice=GAME_CHOICES)
async def game_cmd(interaction: discord.Interaction, choice: discord.app_commands.Choice[str]):
    g, p = choice.value, interaction.user
    
    if g == "roulette":
        players = [p.display_name, "Nightfall 🤖", "Player 2", "Player 3", "Player 4", "Player 5"]
        winner = games.roulette_winner(players)
        await interaction.response.send_message(embed=make_embed("🎰 Roulette", "🎡 Spinning..."))
        file = discord.File(games.create_roulette_gif(players, winner), filename="r.gif")
        await interaction.edit_original_response(content="🎰 **Spinning...**", attachments=[file])
        await asyncio.sleep(5)
        return await interaction.followup.send(embed=make_embed("🏆 Winner", f"# {winner}", config.COLORS["success"]))

    if g == "dice":
        res, wins = games.roll_dice([p.display_name, "Nightfall 🤖"])
        txt = "\n".join(f"🎲 **{k}** → `{v}`" for k, v in res.items())
        return await interaction.response.send_message(embed=make_embed("🎲 Dice", f"{txt}\n\n🏆 **Winner:** {', '.join(wins)}", config.COLORS["success"]))

    if g == "mafia":
        if interaction.channel_id in mafia_games:
            return await interaction.response.send_message("❌ Game already running.", ephemeral=True)
        mafia_games[interaction.channel_id] = {"host": p.id, "players": {p.id: p}, "started": False}
        return await interaction.response.send_message(embed=make_embed("🕵️ Mafia", f"👑 Host: **{p.display_name}**\n👥 Players: **1**\n\nMin: 4"), view=MafiaView(interaction.channel_id))

    if g == "country":
        c = games.random_country()
        return await interaction.response.send_message(embed=make_embed("🌍 Guess Country", f"# {c['flag']}"), view=CountryView(c))

    if g == "hide":
        seeker, hidden = games.hide_and_seek([p.display_name, "P2", "P3", "P4"])
        return await interaction.response.send_message(embed=make_embed("🫣 Hide & Seek", f"👀 **Seeker:** {seeker}\n🏃 **Hiders:**\n" + "".join(f"• {x}\n" for x in hidden)))

    if g == "chairs":
        cid = interaction.channel_id
        if cid in chairs_games:
            return await interaction.response.send_message("❌ Game already running.", ephemeral=True)
        chairs_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False, "round": 0}
        return await interaction.response.send_message(embed=make_embed("🪑 Chairs", f"👑 Host: **{p.display_name}**\n👥 Players: **1**"), view=ChairsLobbyView(cid))

    if g == "replica":
        return await interaction.response.send_message(embed=make_embed("🪞 Replica", f"# {games.replica([p.display_name, 'P2', 'P3'])}"))

    if g == "rps":
        return await interaction.response.send_message(embed=make_embed("✊ RPS", "Choose:"), view=RPSView())

    if g in ("xo", "hotxo"):
        return await interaction.response.send_message(embed=make_embed("❌⭕ XO", "🎮 Ready!"), view=XoView())

    if g == "bus":
        letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        return await interaction.response.send_message(embed=make_embed("🚌 Bus", f"# 【 {letter} 】"), view=BusView(letter))

class MafiaView(discord.ui.View):
    def __init__(self, cid): super().__init__(timeout=300); self.cid = cid
    @discord.ui.button(label="Join 👤", style=discord.ButtonStyle.success)
    async def join(self, i, b):
        game = mafia_games.get(self.cid)
        if not game or game["started"] or i.user.id in game["players"]: return await i.response.send_message("❌", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=make_embed("🕵️ Mafia", f"Players: **{len(game['players'])}**"))
    @discord.ui.button(label="Start ▶️", style=discord.ButtonStyle.primary)
    async def start(self, i, b):
        game = mafia_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 4: return await i.response.send_message("❌", ephemeral=True)
        game["started"] = True
        roles = games.create_mafia_roles(list(game["players"].keys()))
        for uid, usr in game["players"].items():
            try: await usr.send(embed=make_embed("Role", f"# {roles.get(uid, 'Citizen')}"))
            except: pass
        mafia_games.pop(self.cid, None)
        await i.response.edit_message(embed=make_embed("🕵️ Started!", "Check DMs."), view=None)

class ChairsLobbyView(discord.ui.View):
    def __init__(self, cid): super().__init__(timeout=300); self.cid = cid
    @discord.ui.button(label="Join 👤", style=discord.ButtonStyle.success)
    async def join(self, i, b):
        game = chairs_games.get(self.cid)
        if not game or i.user.id in game["players"]: return await i.response.send_message("❌", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=make_embed("🪑 Chairs", f"Players: **{len(game['players'])}**"))
    @discord.ui.button(label="Start ▶️", style=discord.ButtonStyle.primary)
    async def start(self, i, b):
        game = chairs_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 2: return await i.response.send_message("❌", ephemeral=True)
        game["started"] = True
        await i.response.edit_message(embed=make_embed("🪑", "Music started!"), view=None)
        asyncio.create_task(run_chairs(self.cid))

async def run_chairs(cid):
    game = chairs_games.get(cid)
    if not game: return
    players = list(game["players"].values())
    if len(players) == 1:
        chairs_games.pop(cid, None)
        return await (bot.get_channel(cid) or players[0].dm_channel).send(embed=make_embed("🏆 Winner", f"# {players[0].display_name}", config.COLORS["success"]))
    
    game["round"] += 1
    view = ChairView(cid, len(players) - 1)
    ch = bot.get_channel(cid)
    await ch.send(embed=make_embed(f"Round {game["round"]}", f"Chairs: {len(players)-1} - Click fast!"), view=view)
    await asyncio.sleep(4)
    view.stop()
    
    loser = next((p for p in players if p.id not in view.taken), None)
    if loser and loser.id in game["players"]:
        del game["players"][loser.id]
        await ch.send(embed=make_embed("💀 Eliminated", f"{loser.display_name}"))
    await asyncio.sleep(2)
    asyncio.create_task(run_chairs(cid))

class ChairView(discord.ui.View):
    def __init__(self, cid, count):
        super().__init__(timeout=4)
        self.taken = set()
        for i in range(count):
            btn = discord.ui.Button(label=f"🪑 {i+1}", style=discord.ButtonStyle.primary)
            async def cb(i, idx=i, b=btn):
                game = chairs_games.get(cid)
                if not game or i.user.id not in game["players"] or i.user.id in self.taken: return await i.response.send_message("❌", ephemeral=True)
                self.taken.add(i.user.id)
                b.disabled = True
                await i.response.send_message("🪑 Seated!", ephemeral=True)
                try: await i.message.edit(view=self)
                except: pass
            btn.callback = cb
            self.add_item(btn)

class CountryView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=30)
        for choice in data[2]:
            btn = discord.ui.Button(label=choice, style=discord.ButtonStyle.secondary)
            async def cb(i, ch=choice):
                res = "🎉 Correct!" if ch == data[1] else "❌ Wrong!"
                await i.response.edit_message(embed=make_embed(res, f"Answer: {data[1]}"), view=None)
            btn.callback = cb
            self.add_item(btn)

class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        for c in ["Rock", "Paper", "Scissors"]:
            btn = discord.ui.Button(label=c, style=discord.ButtonStyle.primary)
            async def cb(i, choice=c):
                bot_c = random.choice(["Rock", "Paper", "Scissors"])
                res = "Tie 🤝" if choice == bot_c else ("You Won 🏆" if {"Rock": "Scissors", "Scissors": "Paper", "Paper": "Rock"}[choice] == bot_c else "Bot Won 🤖")
                await i.response.edit_message(embed=make_embed("RPS", f"You: {choice}\nBot: {bot_c}\n**{res}**"), view=None)
            btn.callback = cb
            self.add_item(btn)

class XoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for x in range(3):
            for y in range(3):
                self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="⬜", row=x))

class BusView(discord.ui.View):
    def __init__(self, letter):
        super().__init__(timeout=60)
        self.letter = letter
    @discord.ui.button(label="Send Word ✍️", style=discord.ButtonStyle.success)
    async def cb(self, i, b):
        await i.response.send_message(f"Type a word starting with: **{self.letter}**", ephemeral=True)

bot.run(config.TOKEN)

