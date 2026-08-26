import math
import random
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


# =========================================================
# أسماء الألعاب
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


# =========================================================
# 🎲 النرد
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
# 🎰 الروليت
# =========================================================

def roulette_winner(players):
    if not players:
        return None

    return random.choice(players)


def create_roulette_gif(players, winner):
    """
    ينشئ عجلة متحركة وتتوقف فعليًا على الفائز.
    """

    if not players or winner not in players:
        return None

    WIDTH = 700
    HEIGHT = 700

    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT // 2

    RADIUS = 270

    FRAME_COUNT = 80
    FULL_TURNS = 7

    count = len(players)

    segment = 360 / count

    winner_index = players.index(winner)

    # مركز قطاع الفائز
    winner_center = (
        winner_index * segment
        + segment / 2
    )

    # السهم موجود عند أعلى العجلة = -90°
    #
    # نريد مركز قطاع الفائز أن يصل إلى -90°
    #
    # الدوران النهائي:
    target_rotation = (
        -90
        - winner_center
        + FULL_TURNS * 360
    )

    try:
        font = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            20
        )
    except Exception:
        font = ImageFont.load_default()

    try:
        small_font = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            17
        )
    except Exception:
        small_font = font

    colors = [
        (237, 66, 69),
        (88, 101, 242),
        (87, 242, 135),
        (254, 231, 92),
        (235, 69, 158),
        (32, 178, 170),
        (255, 145, 77),
        (155, 89, 182),
    ]

    frames = []

    for frame_number in range(FRAME_COUNT):

        progress = frame_number / (FRAME_COUNT - 1)

        # Ease Out قوي
        eased = 1 - ((1 - progress) ** 4)

        rotation = target_rotation * eased

        image = Image.new(
            "RGB",
            (WIDTH, HEIGHT),
            (18, 18, 25)
        )

        draw = ImageDraw.Draw(image)

        # الحلقة الخارجية
        draw.ellipse(
            (
                CENTER_X - RADIUS - 12,
                CENTER_Y - RADIUS - 12,
                CENTER_X + RADIUS + 12,
                CENTER_Y + RADIUS + 12
            ),
            fill=(235, 235, 240)
        )

        # القطاعات
        for i, player in enumerate(players):

            start_angle = (
                -90
                + rotation
                + i * segment
            )

            end_angle = (
                start_angle
                + segment
            )

            draw.pieslice(
                (
                    CENTER_X - RADIUS,
                    CENTER_Y - RADIUS,
                    CENTER_X + RADIUS,
                    CENTER_Y + RADIUS
                ),
                start=start_angle,
                end=end_angle,
                fill=colors[i % len(colors)],
                outline=(255, 255, 255),
                width=3
            )

            # مكان الاسم
            middle_angle = math.radians(
                start_angle + segment / 2
            )

            text_radius = RADIUS * 0.63

            x = (
                CENTER_X
                + math.cos(middle_angle)
                * text_radius
            )

            y = (
                CENTER_Y
                + math.sin(middle_angle)
                * text_radius
            )

            name = str(player)

            if len(name) > 12:
                name = name[:12] + "..."

            bbox = draw.textbbox(
                (0, 0),
                name,
                font=small_font
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
                font=small_font
            )

        # دائرة المنتصف
        inner = 70

        draw.ellipse(
            (
                CENTER_X - inner,
                CENTER_Y - inner,
                CENTER_X + inner,
                CENTER_Y + inner
            ),
            fill=(22, 22, 30),
            outline=(255, 255, 255),
            width=4
        )

        title = "NIGHTFALL"

        bbox = draw.textbbox(
            (0, 0),
            title,
            font=font
        )

        draw.text(
            (
                CENTER_X -
                (bbox[2] - bbox[0]) / 2,

                CENTER_Y -
                (bbox[3] - bbox[1]) / 2
            ),
            title,
            fill=(255, 255, 255),
            font=font
        )

        # السهم الثابت
        draw.polygon(
            [
                (CENTER_X, 10),
                (CENTER_X - 28, 65),
                (CENTER_X + 28, 65)
            ],
            fill=(255, 255, 255)
        )

        draw.polygon(
            [
                (CENTER_X, 25),
                (CENTER_X - 12, 52),
                (CENTER_X + 12, 52)
            ],
            fill=(237, 66, 69)
        )

        frames.append(image)

    output = BytesIO()

    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=55,
        loop=0,
        disposal=2
    )

    output.seek(0)

    return output


# =========================================================
# 🕵️ المافيا
# =========================================================

def create_mafia_roles(players):
    """
    توزيع أدوار المافيا.

    4-5 لاعبين:
        1 مافيا
        1 طبيب
        الباقي مواطن

    6+:
        مافيا أكثر.
    """

    if len(players) < 4:
        return None

    shuffled = players.copy()

    random.shuffle(shuffled)

    roles = {}

    mafia_count = max(
        1,
        len(players) // 4
    )

    # المافيا
    for player in shuffled[:mafia_count]:
        roles[player] = "🕵️ المافيا"

    remaining = shuffled[mafia_count:]

    # طبيب
    if remaining:
        doctor = remaining.pop(0)
        roles[doctor] = "👨‍⚕️ الطبيب"

    # محقق
    if len(players) >= 6 and remaining:
        detective = remaining.pop(0)
        roles[detective] = "🔎 المحقق"

    # مواطنون
    for player in remaining:
        roles[player] = "👤 مواطن"

    return roles


# =========================================================
# 🌍 خمن الدولة
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
# 🫣 الغميضة
# =========================================================

def hide_and_seek(players):

    if len(players) < 2:
        return None, []

    seeker = random.choice(players)

    hidden = [
        player
        for player in players
        if player != seeker
    ]

    return seeker, hidden


# =========================================================
# 🪑 Musical Chairs
# =========================================================

def create_chairs(number_of_players):
    """
    عدد الكراسي = اللاعبين - 1
    """

    return max(1, number_of_players - 1)


def choose_chair_winner(players, selected_chairs):
    """
    selected_chairs:
        dict {user_id: chair_number}

    اللاعب الذي اختار كرسيًا صحيحًا يبقى.
    """

    winners = list(selected_chairs.keys())

    return winners


# =========================================================
# 🪞 Replica
# =========================================================

def replica(players):

    if not players:
        return None

    return random.choice(players)


# =========================================================
# ✊ حجر ورق مقص
# =========================================================

def rps(player_choice, bot_choice):

    if player_choice == bot_choice:
        return "تعادل 🤝"

    wins = {
        "حجر": "مقص",
        "ورق": "حجر",
        "مقص": "ورق"
    }

    if wins.get(player_choice) == bot_choice:
        return "أنت الفائز 🏆"

    return "Nightfall فاز 🤖"


# =========================================================
# ❌⭕ XO
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
