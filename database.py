"""
نظام قاعدة البيانات - Nightfall Games
يستخدم ملفات JSON لتخزين بيانات اللاعبين بشكل دائم
"""
import json
import os
from pathlib import Path
from threading import Lock

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

ECONOMY_FILE = DATA_DIR / "economy.json"
STATS_FILE = DATA_DIR / "stats.json"

_lock = Lock()


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save(path: Path, data: dict) -> None:
    with _lock:
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)


# ---------------- الاقتصاد (Economy) ----------------

def get_balance(user_id: int) -> int:
    data = _load(ECONOMY_FILE)
    return data.get(str(user_id), {}).get("balance", 0)


def get_wallet(user_id: int) -> dict:
    """يرجع كل بيانات محفظة اللاعب (رصيد + آخر يومية)"""
    data = _load(ECONOMY_FILE)
    return data.get(str(user_id), {"balance": 0, "last_daily": 0})


def add_balance(user_id: int, amount: int) -> int:
    data = _load(ECONOMY_FILE)
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"balance": 0, "last_daily": 0}
    data[uid]["balance"] = max(0, data[uid].get("balance", 0) + amount)
    _save(ECONOMY_FILE, data)
    return data[uid]["balance"]


def set_balance(user_id: int, amount: int) -> None:
    data = _load(ECONOMY_FILE)
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"balance": 0, "last_daily": 0}
    data[uid]["balance"] = max(0, amount)
    _save(ECONOMY_FILE, data)


def set_last_daily(user_id: int, timestamp: float) -> None:
    data = _load(ECONOMY_FILE)
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"balance": 0, "last_daily": 0}
    data[uid]["last_daily"] = timestamp
    _save(ECONOMY_FILE, data)


def transfer(sender_id: int, receiver_id: int, amount: int) -> bool:
    data = _load(ECONOMY_FILE)
    sid, rid = str(sender_id), str(receiver_id)
    if sid not in data or data[sid].get("balance", 0) < amount:
        return False
    if rid not in data:
        data[rid] = {"balance": 0, "last_daily": 0}
    data[sid]["balance"] -= amount
    data[rid]["balance"] += amount
    _save(ECONOMY_FILE, data)
    return True


def get_leaderboard(limit: int = 10) -> list:
    data = _load(ECONOMY_FILE)
    sorted_users = sorted(
        data.items(), key=lambda x: x[1].get("balance", 0), reverse=True
    )
    return sorted_users[:limit]


# ---------------- الإحصائيات (Stats) ----------------

def get_stats(user_id: int) -> dict:
    data = _load(STATS_FILE)
    return data.get(str(user_id), {"wins": 0, "losses": 0, "games_played": 0})


def add_win(user_id: int, game: str = "") -> None:
    data = _load(STATS_FILE)
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"wins": 0, "losses": 0, "games_played": 0}
    data[uid]["wins"] += 1
    data[uid]["games_played"] += 1
    _save(STATS_FILE, data)


def add_loss(user_id: int, game: str = "") -> None:
    data = _load(STATS_FILE)
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"wins": 0, "losses": 0, "games_played": 0}
    data[uid]["losses"] += 1
    data[uid]["games_played"] += 1
    _save(STATS_FILE, data)
