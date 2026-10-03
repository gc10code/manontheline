"""Word list loading and word picking."""

import datetime as dt
import os
import random
from typing import Dict, List, Optional

from .engine import is_playable, normalize_word

DIFFICULTIES = ("easy", "medium", "hard")

WordLists = Dict[str, List[str]]


def load_word_file(path: str) -> List[str]:
    """Read one word per line. Skips blanks, '#' comments, duplicates and unplayable entries."""
    words: List[str] = []
    seen = set()
    with open(path, "r", encoding="utf-8-sig") as fh:
        for line in fh:
            if line.lstrip().startswith("#"):
                continue
            word = normalize_word(line)
            if word and word not in seen and is_playable(word):
                seen.add(word)
                words.append(word)
    return words


def load_words(*folders: str) -> WordLists:
    """Load <difficulty>.txt from each folder. Later folders add to earlier ones."""
    lists: WordLists = {d: [] for d in DIFFICULTIES}
    for folder in folders:
        if not folder or not os.path.isdir(folder):
            continue
        for diff in DIFFICULTIES:
            path = os.path.join(folder, f"{diff}.txt")
            if os.path.isfile(path):
                current = lists[diff]
                current.extend(w for w in load_word_file(path) if w not in current)
    return lists


class WordPicker:
    """Picks random words, avoiding repeats until the pool is exhausted."""

    def __init__(self, lists: WordLists, rng: Optional[random.Random] = None):
        self.lists = lists
        self.rng = rng or random.Random()
        self._recent: Dict[str, List[str]] = {}

    def has_words(self, diff: str) -> bool:
        return bool(self.lists.get(diff))

    def pick(self, diff: str) -> str:
        pool = self.lists[diff]
        if not pool:
            raise LookupError(f"No words for {diff}")
        recent = self._recent.setdefault(diff, [])
        fresh = [w for w in pool if w not in recent] or pool
        word = self.rng.choice(fresh)
        recent.append(word)
        if len(recent) >= len(pool):
            recent[:] = [word]
        return word


def daily_word(lists: WordLists, day: dt.date) -> str:
    """Same word for everyone on the same day, picked from medium+hard."""
    pool = sorted(set(lists["medium"]) | set(lists["hard"])) or sorted(set(lists["easy"]))
    if not pool:
        raise LookupError("No words")
    return random.Random(f"motl-daily-{day.isoformat()}").choice(pool)
