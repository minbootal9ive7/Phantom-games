import math
import random
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


# =========================================================
# الألعاب
# =========================================================

GAMES = {
    "roulette": "🎰 الروليت",
    "mafia": "🕵️ المافيا",
    "country": "🌍 خمن الدولة",
    "hide": "🫣 الغميضة",
    "chairs": "🪑 الكراسي",
    "dice": "🎲 النرد",
    "replica": "🪞 Replica",
    "rps": "✊ حجر ورق مقص",
    "xo": "❌⭕ XO",
    "hotxo": "🔥 Hot XO"
}


# =========================================================
# النرد
# =========================================================

def roll_dice(players):
    results = {}

    for player in players:
        results[player] = random.randint(1, 6)

    highest = max(results.values())

    winners = [
        player
        for player, number in results.items()
        if number == highest
    ]

    return results, winners


# =========================================================
# الروليت
# =========================================================

def roulette_winner(players):
    if not players:
        return None

    return random.choice(players)


def create_roulette_gif(players, winner):
    """
    إنشاء عجلة روليت متحركة GIF.

    players:
        أسماء اللاعبين الموجودين في الجولة.

    winner:
        اللاعب الذي يجب أن تتوقف العجلة عليه.
    """

    if not players:
        return None

    # -----------------------------------------------------
    # إعدادات العجلة
    # -----------------------------------------------------

    size = 700

    center = size // 2

    radius = 280

    frames = []

    # عدد الإطارات
    frame_count = 55

    # -----------------------------------------------------
    # تحميل الخط
    # -----------------------------------------------------

    try:
        font_big = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            25
        )

        font_small = ImageFont.truetype(
            "DejaVuSans.ttf",
            20
        )

    except Exception:

        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # -----------------------------------------------------
    # الفائز
    # -----------------------------------------------------

    winner_index = players.index(winner)

    count = len(players)

    segment_angle = 360 / count

    # -----------------------------------------------------
    # دوران طويل قبل التوقف
    # -----------------------------------------------------

    total_rotations = 6

    # الزاوية التي تجعل الفائز أمام السهم
    target_angle = (
        winner_index * segment_angle
        + segment_angle / 2
    )

    final_rotation = (
        total_rotations * 360
        + target_angle
    )

    # -----------------------------------------------------
    # إنشاء Frames
    # -----------------------------------------------------

    for frame in range(frame_count):

        progress = frame / (frame_count - 1)

        # Ease Out
        eased = 1 - (1 - progress) ** 4

        rotation = final_rotation * eased

        image = Image.new(
            "RGB",
            (size, size),
            (18, 18, 24)
        )

        draw = ImageDraw.Draw(image)

        # -------------------------------------------------
        # الدائرة الخارجية
        # -------------------------------------------------

        draw.ellipse(
            (
                center - radius - 8,
                center - radius - 8,
                center + radius + 8,
                center + radius + 8
            ),
            fill=(230, 230, 235)
        )

        draw.ellipse(
            (
                center - radius,
                center - radius,
                center + radius,
                center + radius
            ),
            fill=(35, 35, 45)
        )

        # -------------------------------------------------
        # قطاعات العجلة
        # -------------------------------------------------

        colors = [
            (237, 66, 69),
            (88, 101, 242),
            (87, 242, 135),
            (254, 231, 92),
            (235, 69, 158),
            (32, 178, 170),
            (255, 145, 77),
            (155, 89, 182)
        ]

        for i, player in enumerate(players):

            start = (
                -90
                + i * segment_angle
                + rotation
            )

            end = start + segment_angle

            color = colors[i % len(colors)]

            draw.pieslice(
                (
                    center - radius,
                    center - radius,
                    center + radius,
                    center + radius
                ),
                start=start,
                end=end,
                fill=color,
                outline=(255, 255, 255),
                width=3
            )

            # -------------------------------------------------
            # مكان اسم اللاعب
            # -------------------------------------------------

            middle = math.radians(
                start + segment_angle / 2
            )

            text_radius = radius * 0.62

            x = (
                center
                + math.cos(middle)
                * text_radius
            )

            y = (
                center
                + math.sin(middle)
                * text_radius
            )

            # تقصير الاسم الطويل
            name = player

            if len(name) > 12:
                name = name[:12] + "…"

            bbox = draw.textbbox(
                (0, 0),
                name,
                font=font_small
            )

            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            draw.text(
                (
                    x - text_width / 2,
                    y - text_height / 2
                ),
                name,
                fill=(255, 255, 255),
                font=font_small
            )

        # -------------------------------------------------
        # دائرة المنتصف
        # -------------------------------------------------

        draw.ellipse(
            (
                center - 65,
                center - 65,
                center + 65,
                center + 65
            ),
            fill=(20, 20, 28),
            outline=(255, 255, 255),
            width=4
        )

        title = "NIGHTFALL"

        bbox = draw.textbbox(
            (0, 0),
            title,
            font=font_big
        )

        draw.text(
            (
                center - (bbox[2] - bbox[0]) / 2,
                center - (bbox[3] - bbox[1]) / 2
            ),
            title,
            fill=(255, 255, 255),
            font=font_big
        )

        # -------------------------------------------------
        # السهم الثابت
        # -------------------------------------------------

        arrow = [
            (center, 18),
            (center - 25, 65),
            (center + 25, 65)
        ]

        draw.polygon(
            arrow,
            fill=(255, 255, 255)
        )

        draw.polygon(
            [
                (center, 30),
                (center - 12, 55),
                (center + 12, 55)
            ],
            fill=(237, 66, 69)
        )

        # -------------------------------------------------
        # اسم اللعبة
        # -------------------------------------------------

        label = "🎰 ROULETTE"

        bbox = draw.textbbox(
            (0, 0),
            label,
            font=font_big
        )

        draw.text(
            (
                center - (bbox[2] - bbox[0]) / 2,
                size - 55
            ),
            label,
            fill=(255, 255, 255),
            font=font_big
        )

        frames.append(image)

    # -----------------------------------------------------
    # تحويل الإطارات إلى GIF
    # -----------------------------------------------------

    output = BytesIO()

    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=45,
        loop=0
    )

    output.seek(0)

    return output


# =========================================================
# خمن الدولة
# =========================================================

COUNTRIES = [
    {
        "name": "مصر",
        "flag": "🇪🇬",
        "choices": [
            "مصر",
            "اليابان",
            "فرنسا",
            "البرازيل"
        ]
    },

    {
        "name": "اليابان",
        "flag": "🇯🇵",
        "choices": [
            "الهند",
            "اليابان",
            "كندا",
            "إسبانيا"
        ]
    },

    {
        "name": "فرنسا",
        "flag": "🇫🇷",
        "choices": [
            "فرنسا",
            "مصر",
            "تركيا",
            "إيطاليا"
        ]
    },

    {
        "name": "البرازيل",
        "flag": "🇧🇷",
        "choices": [
            "الأرجنتين",
            "البرازيل",
            "ألمانيا",
            "المكسيك"
        ]
    }
]


def random_country():
    return random.choice(COUNTRIES)


# =========================================================
# الغميضة
# =========================================================

def hide_and_seek(players):

    seeker = random.choice(players)

    hidden = [
        player
        for player in players
        if player != seeker
    ]

    return seeker, hidden


# =========================================================
# الكراسي
# =========================================================

def chairs_round(players):

    shuffled = players.copy()

    random.shuffle(shuffled)

    winner = shuffled[0]

    eliminated = shuffled[-1]

    return winner, eliminated


# =========================================================
# Replica
# =========================================================

def replica(players):

    return random.choice(players)


# =========================================================
# حجر ورق مقص
# =========================================================

def rps(player_choice, bot_choice):

    if player_choice == bot_choice:
        return "تعادل 🤝"

    wins = {
        "حجر": "مقص",
        "ورق": "حجر",
        "مقص": "ورق"
    }

    if wins[player_choice] == bot_choice:
        return "أنت الفائز 🏆"

    return "Nightfall فاز 🤖"


# =========================================================
# XO
# =========================================================

def empty_xo():

    return ["⬜"] * 9


def check_xo(board):

    combinations = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6)
    ]

    for a, b, c in combinations:

        if (
            board[a] != "⬜"
            and board[a] == board[b]
            and board[a] == board[c]
        ):
            return board[a]

    if "⬜" not in board:
        return "تعادل"

    return None
