"""Achievements: (emoji, name, description), plus the rules that unlock them."""

import datetime as dt
from typing import Callable, Dict, List, Optional, Tuple

from .engine import Round

ACHIEVEMENTS: Dict[str, Tuple[str, str, str]] = {
    "first_win": ("🩸", "First Blood", "Win your first game. Even a broken clock..."),
    "flawless": ("💎", "Untouchable", "Win without a single mistake."),
    "close_call": ("🧵", "Hanging by a Thread", "Win with exactly one life left."),
    "speed_demon": ("⚡", "Speed Demon", "Win in under 15 seconds."),
    "streak_5": ("🔥", "On Fire", "Win 5 games in a row."),
    "streak_10": ("🚀", "Unstoppable", "Win 10 games in a row. Suspicious."),
    "galaxy_brain": ("🧠", "Galaxy Brain", "Guess the whole word with 3+ letters still hidden."),
    "purist": ("🧘", "Purist", "Win on hard without hints."),
    "sudden_death": ("💀", "Living Dangerously", "Win a Sudden Death round."),
    "beat_clock": ("⌛", "Beat the Clock", "Win a Time Attack round."),
    "daily": ("📅", "Creature of Habit", "Win a Daily Challenge."),
    "daily_3": ("📆", "Committed", "Win the Daily Challenge 3 days in a row."),
    "well_rounded": ("🌍", "Well-Rounded", "Win at least once on every difficulty."),
    "pro_loser": ("🤡", "Professional Loser", "Lose 10 games. Dedication!"),
    "combo_5": ("🎯", "C-C-C-Combo!", "Hit 5 correct letters in a row."),
    "marathon_5": ("🏃", "Marathoner", "Survive 5 words in a single Marathon."),
    "no_vowels": ("🚫", "Vowel Hater", "Win without typing a single vowel."),
    "night_owl": ("🦉", "Night Owl", "Win between midnight and 5 AM. Go to sleep."),
    "five_digits": ("💰", "Five Digits", "Reach 10,000 total points."),
    "versus": ("🤝", "Friendship Ender", "Play a Versus game."),
    "surrender": ("🐔", "Tactical Retreat", "Give up. Coward."),
    "curious": ("🥚", "Curious Mind", "Find a secret command."),
    "konami": ("🌈", "Old School", "Enter the Konami code in the main menu."),
}


def evaluate_round(
    rnd: Round,
    mode: str,
    profile,
    marathon_words: int = 0,
    now: Optional[dt.datetime] = None,
) -> List[str]:
    """Return the ids of achievements that this finished round newly unlocks (and unlock them)."""
    now = now or dt.datetime.now()
    s = profile.stats
    won = rnd.won
    rules: Dict[str, Callable[[], bool]] = {
        "first_win": lambda: won,
        "flawless": lambda: won and rnd.misses == 0,
        "close_call": lambda: won and rnd.lives == 1 and rnd.max_lives > 1,
        "speed_demon": lambda: won and rnd.elapsed < 15,
        "streak_5": lambda: s["current_streak"] >= 5,
        "streak_10": lambda: s["current_streak"] >= 10,
        "galaxy_brain": lambda: won and rnd.solved_by_word and rnd.word_guess_hidden_letters >= 3,
        "purist": lambda: won and rnd.difficulty == "hard" and rnd.hints_used == 0,
        "sudden_death": lambda: won and mode == "sudden",
        "beat_clock": lambda: won and mode == "time",
        "daily": lambda: won and mode == "daily",
        "daily_3": lambda: mode == "daily" and profile.daily_streak(now.date()) >= 3,
        "well_rounded": lambda: all(s["wins_by_difficulty"].get(d, 0) > 0 for d in ("easy", "medium", "hard")),
        "pro_loser": lambda: s["lost"] >= 10,
        "combo_5": lambda: rnd.best_combo >= 5,
        "marathon_5": lambda: mode == "marathon" and marathon_words >= 5,
        "no_vowels": lambda: won and not rnd.typed_any_vowel(),
        "night_owl": lambda: won and 0 <= now.hour < 5,
        "five_digits": lambda: s["total_score"] >= 10_000,
        "versus": lambda: mode == "versus",
        "surrender": lambda: rnd.surrendered,
    }
    unlocked = []
    for ach_id, rule in rules.items():
        if ach_id not in profile.achievements and rule():
            profile.unlock(ach_id)
            unlocked.append(ach_id)
    return unlocked
