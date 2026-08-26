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
bank_games = {}

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Bot is online: {bot.user} | Synced {len(synced)} commands")
    except Exception as e:
        print(f"Sync error: {e}")

@bot.tree.command(name="games", description="Show all games")
async def games_cmd(interaction: discord.Interaction):
    text = "\n".join(f"> {name}" for name in games.GAMES.values())
    await interaction.response.send_message(embed=games.embed("Nightfall Games", f"**Available Games**\n\n{text}\n\nUse /game to start"))

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

@bot.tree.command(name="game", description="Start a game")
@discord.app_commands.choices(choice=GAME_CHOICES)
async def game_cmd(interaction: discord.Interaction, choice: discord.app_commands.Choice[str]):
    g, p = choice.value, interaction.user
    
    if g == "roulette":
        cid = interaction.channel_id
        if cid in roulette_games:
            return await interaction.response.send_message("Game already running.", ephemeral=True)
        roulette_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
        return await interaction.response.send_message(embed=games.embed("Roulette Lobby", f"Host: {p.display_name}\nPlayers: 1\n\nClick Join! (10s)"), view=RouletteLobbyView(cid))

    if g == "dice":
        res, wins = games.roll_dice([p.display_name, "Nightfall Bot"])
        txt = "\n".join(f"**{k}** -> `{v}`" for k, v in res.items())
        return await interaction.response.send_message(embed=games.embed("Dice Roll", f"{txt}\n\n**Winner:** {', '.join(wins)}", config.COLORS["success"]))

    if g == "mafia":
        cid = interaction.channel_id
        if cid in mafia_games:
            return await interaction.response.send_message("Game already running.", ephemeral=True)
        mafia_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
        return await interaction.response.send_message(embed=games.embed("Mafia Lobby", f"Host: {p.display_name}\nPlayers: 1\n\nMin: 4 players"), view=MafiaView(cid))

    if g == "country":
        c = games.random_country()
        return await interaction.response.send_message(embed=games.embed("Guess Country", f"Which country is this?\n\n# {c['flag']}"), view=CountryView(c))

    if g == "hide":
        seeker, hidden = games.hide_and_seek([p.display_name, "Player 2", "Player 3", "Player 4"])
        return await interaction.response.send_message(embed=games.embed("Hide and Seek", f"**Seeker:** {seeker}\n**Hiders:**\n" + "".join(f"- {x}\n" for x in hidden)))

    if g == "chairs":
        cid = interaction.channel_id
        if cid in chairs_games:
            return await interaction.response.send_message("Game already running.", ephemeral=True)
        chairs_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False, "round": 0}
        return await interaction.response.send_message(embed=games.embed("Musical Chairs Lobby", f"Host: {p.display_name}\nPlayers: 1"), view=ChairsLobbyView(cid))

    if g == "replica":
        return await interaction.response.send_message(embed=games.embed("Replica", f"Selected:\n# {games.replica([p.display_name, 'Player 2', 'Player 3'])}"))

    if g == "rps":
        return await interaction.response.send_message(embed=games.embed("Rock Paper Scissors", "Choose your move:"), view=RPSView())

    if g in ("xo", "hotxo"):
        return await interaction.response.send_message(embed=games.embed("XO Game", "Turn: X"), view=XoView())

    if g == "bus":
        letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        return await interaction.response.send_message(embed=games.embed("Bus Complete", f"Letter: **{letter}**"), view=BusView(letter))

    if g == "bank":
        cid = interaction.channel_id
        if cid in bank_games:
            return await interaction.response.send_message("Bank game already running.", ephemeral=True)
        bank_games[cid] = {"players": {p.id: {"name": p.display_name, "balance": 1000}}}
        return await interaction.response.send_message(embed=games.embed("Bank Game", f"Welcome {p.display_name} to the Bank!\nStarting Balance: $1000"), view=BankView(cid, p.id))


# ================= VIEWS =================
class RouletteLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=10)
        self.cid = cid

    @discord.ui.button(label="Join", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = roulette_games.get(self.cid)
        if not game or game["started"] or interaction.user.id in game["players"]:
            return await interaction.response.send_message("Cannot join.", ephemeral=True)
        game["players"][interaction.user.id] = interaction.user
        await interaction.response.send_message("Joined!", ephemeral=True)

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

        msg = await channel.send(embed=games.embed("Roulette", "Spinning for 10 seconds..."))
        gif = games.create_roulette_gif(display_names, winner)
        file = discord.File(gif, filename="roulette.gif")
        
        await msg.edit(content="Spinning...", attachments=[file])
        await asyncio.sleep(10)
        await channel.send(embed=games.embed("Roulette Winner", f"Winner:\n# {winner}", config.COLORS["success"]))

class MafiaView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=300)
        self.cid = cid

    @discord.ui.button(label="Join", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = mafia_games.get(self.cid)
        if not game or game["started"] or i.user.id in game["players"]:
            return await i.response.send_message("Error", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("Mafia Lobby", f"Players: {len(game['players'])}"))

    @discord.ui.button(label="Start", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        game = mafia_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 4:
            return await i.response.send_message("Need at least 4 players.", ephemeral=True)
        game["started"] = True
        roles = games.create_mafia_roles(list(game["players"].keys()))
        for uid, usr in game["players"].items():
            try:
                await usr.send(embed=games.embed("Mafia Role", f"Your Role: {roles.get(uid, 'Citizen')}"))
            except:
                pass
        mafia_games.pop(self.cid, None)
        await i.response.edit_message(embed=games.embed("Mafia Started", "Roles sent via DM."), view=None)

class ChairsLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=300)
        self.cid = cid

    @discord.ui.button(label="Join", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = chairs_games.get(self.cid)
        if not game or i.user.id in game["players"]:
            return await i.response.send_message("Error", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("Musical Chairs", f"Players: {len(game['players'])}"))

    @discord.ui.button(label="Start", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        game = chairs_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 2:
            return await i.response.send_message("Need at least 2 players.", ephemeral=True)
        game["started"] = True
        await i.response.edit_message(embed=games.embed("Chairs", "Music started!"), view=None)
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
            return await ch.send(embed=games.embed("Chairs Winner", f"# {players[0].display_name}", config.COLORS["success"]))
        return
    
    game["round"] += 1
    view = ChairView(cid, len(players) - 1)
    ch = bot.get_channel(cid)
    if ch:
        await ch.send(embed=games.embed(f"Round {game['round']}", f"Chairs: {len(players)-1} - Click fast!"), view=view)
    await asyncio.sleep(4)
    view.stop()
    
    loser = next((p for p in players if p.id not in view.taken), None)
    if loser and loser.id in game["players"]:
        del game["players"][loser.id]
        if ch:
            await ch.send(embed=games.embed("Eliminated", f"{loser.display_name} out!"))
    await asyncio.sleep(2)
    asyncio.create_task(run_chairs(cid))

class ChairView(discord.ui.View):
    def __init__(self, cid, count):
        super().__init__(timeout=4)
        self.taken = set()
        for i in range(count):
            btn = discord.ui.Button(label=f"Chair {i+1}", style=discord.ButtonStyle.primary)
            async def cb(interaction: discord.Interaction, b=btn):
                game = chairs_games.get(cid)
                if not game or interaction.user.id not in game["players"] or interaction.user.id in self.taken:
                    return await interaction.response.send_message("Not allowed", ephemeral=True)
                self.taken.add(interaction.user.id)
                b.disabled = True
                await interaction.response.send_message("Seated!", ephemeral=True)
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
            return await interaction.response.send_message("Taken!", ephemeral=True)
        self.label = "X"
        self.style = discord.ButtonStyle.danger
        await interaction.response.edit_message(view=self.view)

class XoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for x in range(3):
            for y in range(3):
                self.add_item(XoButton(x, y))

class BankView(discord.ui.View):
    def __init__(self, cid, user_id):
        super().__init__(timeout=120)
        self.cid = cid
        self.user_id = user_id

    @discord.ui.button(label="Deposit $200", style=discord.ButtonStyle.success)
    async def deposit(self, i: discord.Interaction, b: discord.ui.Button):
        data = bank_games.get(self.cid)
        if not data or i.user.id != self.user_id:
            return await i.response.send_message("Not your session.", ephemeral=True)
        data["players"][self.user_id]["balance"] += 200
        bal = data["players"][self.user_id]["balance"]
        await i.response.edit_message(embed=games.embed("Bank Game", f"Current Balance: ${bal}"))

    @discord.ui.button(label="Withdraw $200", style=discord.ButtonStyle.danger)
    async def withdraw(self, i: discord.Interaction, b: discord.ui.Button):
        data = bank_games.get(self.cid)
        if not data or i.user.id != self.user_id:
            return await i.response.send_message("Not your session.", ephemeral=True)
        if data["players"][self.user_id]["balance"] < 200:
            return await i.response.send_message("Insufficient funds!", ephemeral=True)
        data["players"][self.user_id]["balance"] -= 200
        bal = data["players"][self.user_id]["balance"]
        await i.response.edit_message(embed=games.embed("Bank Game", f"Current Balance: ${bal}"))

class CountryView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=30)
        for choice in data["choices"]:
            btn = discord.ui.Button(label=choice, style=discord.ButtonStyle.secondary)
            async def cb(i: discord.Interaction, ch=choice):
                res = "Correct!" if ch == data["answer"] else "Wrong!"
                await i.response.edit_message(embed=games.embed(res, f"Answer: {data['answer']}"), view=None)
            btn.callback = cb
            self.add_item(btn)

class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        for c in ["Rock", "Paper", "Scissors"]:
            btn = discord.ui.Button(label=c, style=discord.ButtonStyle.primary)
            async def cb(i: discord.Interaction, choice=c):
                bot_c = random.choice(["Rock", "Paper", "Scissors"])
                wins = {"Rock": "Scissors", "Scissors": "Paper", "Paper": "Rock"}
                res = "Tie" if choice == bot_c else ("You Won" if wins[choice] == bot_c else "Bot Won")
                await i.response.edit_message(embed=games.embed("RPS", f"You: {choice}\nBot: {bot_c}\n**{res}**"), view=None)
            btn.callback = cb
            self.add_item(btn)

class BusView(discord.ui.View):
    def __init__(self, letter):
        super().__init__(timeout=60)
        self.letter = letter
    @discord.ui.button(label="Type Word", style=discord.ButtonStyle.success)
    async def cb(self, i: discord.Interaction, b: discord.ui.Button):
        await i.response.send_message(f"Type a word starting with: **{self.letter}**", ephemeral=True)

bot.run(config.TOKEN)
