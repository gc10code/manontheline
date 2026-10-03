"""Persistent profile: settings, stats, achievements, leaderboard, daily results."""

import copy
import datetime as dt
import json
import os
import tempfile
from typing import Any, Dict, List, Optional

LEADERBOARD_SIZE = 50
MAX_MISTAKES_TRACKED = 7  # index 0..6 for the wins histogram


def _defaults() -> Dict[str, Any]:
    return {
        "version": 3,
        "name": "",
        "settings": {
            "difficulty": "easy",
            "animations": True,
            "sound": False,
            "rainbow": False,
        },
        "stats": {
            "played": 0,
            "won": 0,
            "lost": 0,
            "current_streak": 0,
            "best_streak": 0,
            "total_score": 0,
            "best_session": 0,
            "letters_typed": {},
            "mistakes_on_win": [0] * MAX_MISTAKES_TRACKED,
            "fastest_win": None,
            "hints_used": 0,
            "word_guesses_right": 0,
            "time_played": 0.0,
            "wins_by_difficulty": {"easy": 0, "medium": 0, "hard": 0},
            "max_combo": 0,
            "marathon_best": 0,
            "easter_eggs": [],
        },
        "achievements": {},
        "leaderboard": [],
        "daily": {},
    }


def _merge(defaults: Any, loaded: Any) -> Any:
    """Recursively fill missing keys from defaults, keeping types sane."""
    if isinstance(defaults, dict):
        if not isinstance(loaded, dict):
            return copy.deepcopy(defaults)
        out = {k: _merge(v, loaded.get(k, v)) for k, v in defaults.items()}
        for k, v in loaded.items():
            if k not in out:
                out[k] = v
        return out
    if defaults is None:
        return loaded
    if isinstance(defaults, bool):
        return loaded if isinstance(loaded, bool) else defaults
    if isinstance(defaults, (int, float)) and not isinstance(defaults, bool):
        return loaded if isinstance(loaded, (int, float)) and not isinstance(loaded, bool) else defaults
    if type(loaded) is not type(defaults):
        return copy.deepcopy(defaults)
    return loaded


class Profile:
    def __init__(self, path: Optional[str]):
        self.path = path
        self.data = _defaults()
        self.load_error: Optional[str] = None
        if path:
            self.load()

    # ----- io ------------------------------------------------------------
    def load(self) -> None:
        if not self.path or not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            self.data = _merge(_defaults(), loaded)
            hist = self.data["stats"]["mistakes_on_win"]
            hist = (list(hist) + [0] * MAX_MISTAKES_TRACKED)[:MAX_MISTAKES_TRACKED]
            self.data["stats"]["mistakes_on_win"] = hist
        except (OSError, ValueError) as exc:
            # Keep the broken file around instead of silently destroying progress.
            self.load_error = str(exc)
            try:
                os.replace(self.path, self.path + ".broken")
            except OSError:
                pass
            self.data = _defaults()

    def save(self) -> bool:
        if not self.path:
            return False
        try:
            folder = os.path.dirname(self.path)
            os.makedirs(folder, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=folder, prefix=".save-", suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
            return True
        except OSError:
            return False

    def reset(self) -> None:
        keep_settings = copy.deepcopy(self.data["settings"])
        name = self.data["name"]
        self.data = _defaults()
        self.data["settings"] = keep_settings
        self.data["name"] = name

    # ----- shortcuts -----------------------------------------------------
    @property
    def settings(self) -> Dict[str, Any]:
        return self.data["settings"]

    @property
    def stats(self) -> Dict[str, Any]:
        return self.data["stats"]

    @property
    def achievements(self) -> Dict[str, str]:
        return self.data["achievements"]

    @property
    def name(self) -> str:
        return self.data["name"]

    @name.setter
    def name(self, value: str) -> None:
        self.data["name"] = value.strip()[:20]

    # ----- recording -----------------------------------------------------
    def record_round(self, rnd, points: int) -> None:
        s = self.stats
        s["played"] += 1
        s["time_played"] += rnd.elapsed
        s["hints_used"] += rnd.hints_used
        s["max_combo"] = max(s["max_combo"], rnd.best_combo)
        for letter in rnd.typed:
            s["letters_typed"][letter] = s["letters_typed"].get(letter, 0) + 1
        if rnd.won:
            s["won"] += 1
            s["current_streak"] += 1
            s["best_streak"] = max(s["best_streak"], s["current_streak"])
            s["total_score"] += points
            wins = s["wins_by_difficulty"]
            wins[rnd.difficulty] = wins.get(rnd.difficulty, 0) + 1
            idx = min(rnd.misses, MAX_MISTAKES_TRACKED - 1)
            s["mistakes_on_win"][idx] += 1
            if s["fastest_win"] is None or rnd.elapsed < s["fastest_win"]:
                s["fastest_win"] = round(rnd.elapsed, 2)
            if rnd.solved_by_word:
                s["word_guesses_right"] += 1
        else:
            s["lost"] += 1
            s["current_streak"] = 0

    def add_leaderboard(self, score: int, mode: str, difficulty: str) -> int:
        """Insert a session score. Returns its 1-based rank within the mode, or 0 if not placed."""
        if score <= 0:
            return 0
        self.stats["best_session"] = max(self.stats["best_session"], score)
        entry = {
            "name": self.name or "???",
            "score": int(score),
            "mode": mode,
            "difficulty": difficulty,
            "date": dt.date.today().isoformat(),
        }
        board: List[dict] = self.data["leaderboard"]
        board.append(entry)
        board.sort(key=lambda e: e.get("score", 0), reverse=True)
        del board[LEADERBOARD_SIZE:]
        same_mode = [e for e in board if e.get("mode") == mode]
        for i, e in enumerate(same_mode):
            if e is entry:
                return i + 1 if i < 10 else 0
        return 0

    def top(self, mode: Optional[str] = None, n: int = 10) -> List[dict]:
        board = self.data["leaderboard"]
        if mode:
            board = [e for e in board if e.get("mode") == mode]
        return board[:n]

    # ----- daily ---------------------------------------------------------
    def daily_result(self, day: dt.date) -> Optional[dict]:
        return self.data["daily"].get(day.isoformat())

    def record_daily(self, day: dt.date, rnd) -> None:
        self.data["daily"][day.isoformat()] = {
            "won": rnd.won,
            "mistakes": rnd.misses,
            "max_lives": rnd.max_lives,
            "history": "".join("1" if h else "0" for h in rnd.history),
            "seconds": round(rnd.elapsed, 1),
            "hints": rnd.hints_used,
        }

    def daily_streak(self, today: dt.date) -> int:
        """Consecutive days (ending today or yesterday) with at least one daily win."""
        won_days = {
            k[:10] for k, v in self.data["daily"].items() if isinstance(v, dict) and v.get("won")
        }
        day = today if today.isoformat() in won_days else today - dt.timedelta(days=1)
        streak = 0
        while day.isoformat() in won_days:
            streak += 1
            day -= dt.timedelta(days=1)
        return streak

    # ----- achievements --------------------------------------------------
    def unlock(self, ach_id: str) -> bool:
        if ach_id in self.achievements:
            return False
        self.achievements[ach_id] = dt.datetime.now().isoformat(timespec="seconds")
        return True
