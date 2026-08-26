import asyncio
import math
import random
from io import BytesIO
import discord
from PIL import Image, ImageDraw, ImageFont
import config

GAMES = {
    "roulette": "Roulette",
    "mafia": "Mafia",
    "country": "Guess Country",
    "hide": "Hide and Seek",
    "chairs": "Musical Chairs",
    "dice": "Dice Roll",
    "replica": "Replica",
    "rps": "Rock Paper Scissors",
    "xo": "XO",
    "hotxo": "Hot XO",
    "bus": "Bus Complete",
    "bank": "Bank Game"
}

def embed(title, text, color=None):
    return discord.Embed(
        title=title,
        description=text,
        color=color or config.COLORS["main"]
    )

# =========================================================
# 🎰 ROULETTE (مع أيقونة png1.png في المنتصف)
# =========================================================
def create_roulette_gif(players, winner):
    W = H = 600
    C = 300
    R = 235

    count = len(players)
    segment = 360 / count
    winner_i = players.index(winner)

    target = -90 - (winner_i * segment + segment / 2) + 360 * 10
    colors = [(237, 66, 69), (88, 101, 242), (87, 242, 135), (254, 231, 92), (235, 69, 158), (32, 178, 170)]

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    except:
        font = ImageFont.load_default()

    frames = []
    total_frames = 100

    for n in range(total_frames):
        p = n / (total_frames - 1)
        ease = 1 - (1 - p) ** 4
        rotation = target * ease

        img = Image.new("RGB", (W, H), (18, 18, 25))
        d = ImageDraw.Draw(img)

        for i, name in enumerate(players):
            start = -90 + rotation + i * segment
            end = start + segment

            d.pieslice((C-R, C-R, C+R, C+R), start, end, fill=colors[i % len(colors)], outline="white", width=2)

            a = math.radians(start + segment / 2)
            x = C + math.cos(a) * R * .62
            y = C + math.sin(a) * R * .62

            text = str(name)
            if len(text) > 11:
                text = text[:11] + "…"

            try:
                box = d.textbbox((0, 0), text, font=font)
                tw, th = box[2] - box[0], box[3] - box[1]
            except:
                tw, th = 60, 18

            d.text((x - tw / 2, y - th / 2), text, fill="white", font=font)

        try:
            logo = Image.open("png1.png").convert("RGBA")
            logo = logo.resize((130, 130))
            mask = Image.new("L", (130, 130), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, 130, 130), fill=255)
            img.paste(logo, (C - 65, C - 65), mask)
        except:
            d.ellipse((235, 235, 365, 365), fill=(20, 20, 28), outline="white", width=4)
            d.text((263, 288), "NIGHTFALL", fill="white", font=font)

        d.polygon([(300, 5), (275, 55), (325, 55)], fill="white")
        frames.append(img)

    out = BytesIO()
    frames[0].save(out, "GIF", save_all=True, append_images=frames[1:], duration=100, loop=0)
    out.seek(0)
    return out

def roulette_winner(players):
    return random.choice(players)

def roll_dice(players):
    results = {name: random.randint(1, 6) for name in players}
    max_val = max(results.values())
    winners = [name for name, val in results.items() if val == max_val]
    return results, winners

def random_country():
    countries = [
        ("🇪🇬", "Egypt", ["Egypt", "Japan", "France", "Brazil"]),
        ("🇯🇵", "Japan", ["India", "Japan", "Canada", "Spain"]),
        ("🇫🇷", "France", ["France", "Egypt", "Turkey", "Italy"]),
    ]
    f, a, c = random.choice(countries)
    return {"flag": f, "answer": a, "choices": c}

def hide_and_seek(players):
    seeker = random.choice(players)
    hidden = [p for p in players if p != seeker]
    return seeker, hidden

def replica(players):
    return random.choice(players)

def create_mafia_roles(player_ids):
    if len(player_ids) < 4:
        return None
    random.shuffle(player_ids)
    roles = {}
    mafia_count = max(1, len(player_ids) // 4)
    for uid in player_ids[:mafia_count]:
        roles[uid] = "Mafia"
    remaining = player_ids[mafia_count:]
    if remaining:
        roles[remaining.pop(0)] = "Doctor"
    if len(player_ids) >= 6 and remaining:
        roles[remaining.pop(0)] = "Detective"
    for uid in remaining:
        roles[uid] = "Citizen"
    return roles
        
