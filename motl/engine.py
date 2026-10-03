"""Pure game logic: no printing, no input, fully testable."""

import random
import string
import time
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set

LETTERS = set(string.ascii_uppercase)
VOWELS = set("AEIOU")
# Characters that are part of a word but never need to be guessed.
FREE_CHARS = set(" -'")

LETTER_POINTS = 100
WIN_BONUS = 500
LIFE_BONUS = 100
FLAWLESS_BONUS = 300
WORD_GUESS_BONUS_PER_LETTER = 75
HINT_COST = 150
MAX_HINTS = 2
WRONG_WORD_PENALTY = 2
MAX_COMBO_MULTIPLIER = 3.0

DIFFICULTY_MULTIPLIER = {"easy": 1.0, "medium": 1.5, "hard": 2.0}


def normalize_word(raw: str) -> str:
    """Uppercase, strip accents and collapse whitespace: 'Café  crème' -> 'CAFE CREME'."""
    decomposed = unicodedata.normalize("NFD", raw.strip())
    no_accents = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return " ".join(no_accents.upper().split())


def is_playable(word: str) -> bool:
    """A word is playable if it only contains A-Z plus free chars and has at least 2 letters."""
    letters = [c for c in word if c not in FREE_CHARS]
    return len(letters) >= 2 and all(c in LETTERS for c in letters)


class Outcome(Enum):
    HIT = "hit"
    MISS = "miss"
    REPEAT = "repeat"
    INVALID = "invalid"


@dataclass
class GuessResult:
    outcome: Outcome
    letter: str = ""
    occurrences: int = 0
    points: int = 0
    combo: int = 0


@dataclass
class Round:
    """A single word to guess."""

    word: str
    max_lives: int = 6
    lives: Optional[int] = None
    difficulty: str = "easy"
    guessed: Set[str] = field(default_factory=set)
    wrong: List[str] = field(default_factory=list)
    history: List[bool] = field(default_factory=list)
    hinted: Set[str] = field(default_factory=set)
    typed: Set[str] = field(default_factory=set)
    score: int = 0
    combo: int = 0
    best_combo: int = 0
    hints_used: int = 0
    solved_by_word: bool = False
    word_guess_hidden_letters: int = 0
    start_time: float = field(default_factory=time.monotonic)
    end_time: Optional[float] = None
    surrendered: bool = False
    timed_out: bool = False

    def __post_init__(self) -> None:
        self.word = normalize_word(self.word)
        if not is_playable(self.word):
            raise ValueError(f"Unplayable word: {self.word!r}")
        if self.lives is None:
            self.lives = self.max_lives

    # ----- state ---------------------------------------------------------
    @property
    def letters_needed(self) -> Set[str]:
        return {c for c in self.word if c in LETTERS}

    @property
    def missing(self) -> Set[str]:
        return self.letters_needed - self.guessed

    @property
    def mistakes(self) -> int:
        """Lives lost compared to a full bar (drives the drawing)."""
        return self.max_lives - self.lives

    @property
    def misses(self) -> int:
        """Wrong guesses made in this round (letters or whole words)."""
        return self.history.count(False)

    @property
    def lost(self) -> bool:
        return self.lives <= 0 or self.surrendered or self.timed_out

    @property
    def won(self) -> bool:
        return not self.missing and not self.lost

    @property
    def over(self) -> bool:
        return self.won or self.lost

    @property
    def elapsed(self) -> float:
        end = self.end_time if self.end_time is not None else time.monotonic()
        return end - self.start_time

    def masked(self, blank: str = "_") -> List[str]:
        return [c if (c in FREE_CHARS or c in self.guessed) else blank for c in self.word]

    def combo_multiplier(self) -> float:
        return min(MAX_COMBO_MULTIPLIER, 1.0 + 0.5 * max(0, self.combo - 1))

    def _check_end(self) -> None:
        if self.over and self.end_time is None:
            self.end_time = time.monotonic()

    # ----- actions -------------------------------------------------------
    def guess_letter(self, raw: str) -> GuessResult:
        letter = normalize_word(raw)
        if self.over or len(letter) != 1 or letter not in LETTERS:
            return GuessResult(Outcome.INVALID, letter)
        if letter in self.guessed:
            return GuessResult(Outcome.REPEAT, letter)

        self.guessed.add(letter)
        self.typed.add(letter)
        occurrences = self.word.count(letter)
        if occurrences:
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)
            points = int(LETTER_POINTS * occurrences * self.combo_multiplier())
            self.score += points
            self.history.append(True)
            self._check_end()
            return GuessResult(Outcome.HIT, letter, occurrences, points, self.combo)

        self.combo = 0
        self.lives -= 1
        self.wrong.append(letter)
        self.history.append(False)
        self._check_end()
        return GuessResult(Outcome.MISS, letter)

    def guess_word(self, raw: str) -> bool:
        """Guess the whole word. Right: instant win + bonus. Wrong: lose WRONG_WORD_PENALTY lives."""
        if self.over:
            return False
        guess = normalize_word(raw)
        strip = lambda w: "".join(c for c in w if c in LETTERS)  # noqa: E731
        if strip(guess) == strip(self.word):
            hidden = len([c for c in self.word if c in self.missing])
            self.word_guess_hidden_letters = hidden
            self.score += hidden * WORD_GUESS_BONUS_PER_LETTER
            self.guessed |= self.letters_needed
            self.solved_by_word = True
            self.history.append(True)
            self._check_end()
            return True
        self.combo = 0
        self.lives = max(0, self.lives - WRONG_WORD_PENALTY)
        self.history.append(False)
        self._check_end()
        return False

    def can_hint(self) -> bool:
        return not self.over and self.hints_used < MAX_HINTS and len(self.missing) > 1

    def hint(self, rng: Optional[random.Random] = None) -> Optional[str]:
        """Reveal a random missing letter at the cost of HINT_COST points (score may not go below 0)."""
        if not self.can_hint():
            return None
        letter = (rng or random).choice(sorted(self.missing))
        self.guessed.add(letter)
        self.hinted.add(letter)
        self.hints_used += 1
        self.score = max(0, self.score - HINT_COST)
        self._check_end()
        return letter

    def surrender(self) -> None:
        if not self.over:
            self.surrendered = True
            self._check_end()

    def time_out(self) -> None:
        if not self.over:
            self.timed_out = True
            self._check_end()

    # ----- scoring -------------------------------------------------------
    def time_bonus(self) -> int:
        return max(0, int(1000 - self.elapsed * 10))

    def final_breakdown(self, mode_multiplier: float = 1.0) -> dict:
        """Points awarded at the end of the round. Losing keeps nothing but the shame."""
        if not self.won:
            return {"letters": self.score, "total": 0}
        diff_mult = DIFFICULTY_MULTIPLIER.get(self.difficulty, 1.0)
        parts = {
            "letters": self.score,
            "win": WIN_BONUS,
            "time": self.time_bonus(),
            "lives": self.lives * LIFE_BONUS,
            "flawless": FLAWLESS_BONUS if self.misses == 0 else 0,
        }
        base = sum(parts.values())
        parts["multiplier"] = round(diff_mult * mode_multiplier, 2)
        parts["total"] = int(base * diff_mult * mode_multiplier)
        return parts

    def typed_any_vowel(self) -> bool:
        """True if the player typed a vowel themselves (hints and word guesses don't count)."""
        return bool(self.typed & VOWELS)
