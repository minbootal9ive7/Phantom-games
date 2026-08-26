import asyncio
import math
import random
from io import BytesIO
import aiohttp
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

async def download_avatar(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(BytesIO(data)).convert("RGBA")
    except:
        pass
    return None

def create_roulette_gif(players_data, winner_name):
    W = H = 600
    C = 300
    R = 235

    count = len(players_data)
    segment = 360 / count
    
    winner_i = 0
    for idx, p in enumerate(players_data):
        if p["name"] == winner_name:
            winner_i = idx
            break

    target = -(winner_i * segment + segment / 2) + 360 * 4
    colors = [(216, 147, 201), (138, 91, 133)]

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    except:
        font = ImageFont.load_default()

    frames = []
    total_frames = 45

    for n in range(total_frames):
        p = n / (total_frames - 1)
        ease = 1 - (1 - p) ** 3
        rotation = target * ease

        img = Image.new("RGB", (W, H), (15, 15, 20))
        d = ImageDraw.Draw(img)

        current_angle = (-rotation) % 360
        active_player_idx = int((current_angle // segment)) % count
        active_avatar = players_data[active_player_idx].get("avatar")

        # رسم قطع العجلة والنصوص
        for i, player in enumerate(players_data):
            name = player["name"]
            start = rotation + i * segment
            end = start + segment

            d.pieslice((C-R, C-R, C+R, C+R), start, end, fill=colors[i % len(colors)], outline="white", width=3)

            a = math.radians(start + segment / 2)
            x = C + math.cos(a) * R * .62
            y = C + math.sin(a) * R * .62

            text = str(name)
            if len(text) > 10:
                text = text[:10] + "…"

            try:
                box = d.textbbox((0, 0), text, font=font)
                tw, th = box[2] - box[0], box[3] - box[1]
            except:
                tw, th = 60, 18

            d.text((x - tw / 2, y - th / 2), text, fill="white", font=font)

        # رسم السهم الصغير الثابت على الحافة اليمنى (بنفس مكان الشكل في الصورة)
        # إحداثيات رأس السهم وجانبيه ليكون مثلثاً بارزاً للخارج من جهة اليمين عند زاوية 0 (3 إحداثيات للـ polygon)
        arrow_tip = (C + R + 3, C)         # رأس السهم على حافة الدائرة يميناً
        arrow_top = (C + R + 20, C - 10)   # الزاوية العلوية للخارج
        arrow_bottom = (C + R + 20, C + 10) # الزاوية السفلية للخارج
        d.polygon([arrow_tip, arrow_top, arrow_bottom], fill="white")

        # عرض صورة الشخص الذي تمر العجلة عليه في المنتصف لحظياً
        if active_avatar:
            avatar = active_avatar.resize((180, 180))
            mask = Image.new("L", (150, 150), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, 150, 150), fill=255)
            
            img.paste(avatar, (C - 90, C - 90), mask)
            d.ellipse((C-92, C-92, C+92, C+92), outline="white", width=3)
        else:
            d.ellipse((C-90, C-90, C+90, C+90), fill=(40, 40, 50), outline="white", width=3)
            d.text((C-45, C-10), "SPIN", fill="white", font=font)

        frames.append(img)

    out = BytesIO()
    frames[0].save(out, "GIF", save_all=True, append_images=frames[1:], duration=140, loop=0)
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
        ("علم مصر", "مصر", ["مصر", "اليابان", "فرنسا", "البرازيل"]),
        ("علم اليابان", "اليابان", ["الهند", "اليابان", "كندا", "إسبانيا"]),
        ("علم فرنسا", "فرنسا", ["فرنسا", "مصر", "تركيا", "إيطاليا"]),
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
        roles[uid] = "مافيا"
    remaining = player_ids[mafia_count:]
    if remaining:
        roles[remaining.pop(0)] = "طبيب"
    if len(player_ids) >= 6 and remaining:
        roles[remaining.pop(0)] = "محقق"
    for uid in remaining:
        roles[uid] = "مواطن"
    return roles
    
