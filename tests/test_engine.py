import random

import pytest

from motl.engine import (
    FLAWLESS_BONUS,
    HINT_COST,
    LIFE_BONUS,
    MAX_HINTS,
    WIN_BONUS,
    WRONG_WORD_PENALTY,
    Outcome,
    Round,
    is_playable,
    normalize_word,
)


def test_normalize_strips_accents_and_spaces():
    assert normalize_word("  café  crème ") == "CAFE CREME"
    assert normalize_word("naïve") == "NAIVE"


@pytest.mark.parametrize("word,ok", [
    ("CAT", True), ("ICE CREAM", True), ("LUNA PARK", True), ("A", False),
    ("", False), ("C4T", False), ("ROCK-N-ROLL", True),
])
def test_is_playable(word, ok):
    assert is_playable(normalize_word(word)) is ok


def test_unplayable_word_rejected():
    with pytest.raises(ValueError):
        Round("X")


def test_spaces_are_free_and_multiword_is_winnable():
    rnd = Round("ice cream")
    assert rnd.masked() == ["_", "_", "_", " ", "_", "_", "_", "_", "_"]
    for letter in "ICERAM":
        rnd.guess_letter(letter)
    assert rnd.won and not rnd.lost


def test_hit_miss_repeat_invalid():
    rnd = Round("BALL")
    hit = rnd.guess_letter("l")
    assert hit.outcome == Outcome.HIT and hit.occurrences == 2
    assert rnd.guess_letter("L").outcome == Outcome.REPEAT
    assert rnd.guess_letter("1").outcome == Outcome.INVALID
    assert rnd.guess_letter("AB").outcome == Outcome.INVALID
    miss = rnd.guess_letter("Z")
    assert miss.outcome == Outcome.MISS
    assert rnd.lives == 5 and rnd.wrong == ["Z"] and rnd.misses == 1


def test_accented_guess_counts_as_plain_letter():
    rnd = Round("CAFE")
    assert rnd.guess_letter("é").outcome == Outcome.HIT


def test_losing_after_six_misses():
    rnd = Round("CAT")
    for letter in "BDEFGH":
        rnd.guess_letter(letter)
    assert rnd.lost and not rnd.won and rnd.over
    assert rnd.guess_letter("C").outcome == Outcome.INVALID  # no moves after the end
    assert rnd.final_breakdown()["total"] == 0


def test_combo_multiplier_grows_and_resets():
    rnd = Round("ABCDEFGHIJ")
    rnd.guess_letter("A")
    assert rnd.combo_multiplier() == 1.0
    rnd.guess_letter("B")
    assert rnd.combo_multiplier() == 1.5
    for letter in "CDEFG":
        rnd.guess_letter(letter)
    assert rnd.combo_multiplier() == 3.0  # capped
    rnd.guess_letter("Z")
    assert rnd.combo == 0 and rnd.best_combo == 7


def test_word_guess_right_and_wrong():
    rnd = Round("LUNA PARK")
    rnd.guess_letter("A")
    assert rnd.guess_word("lunapark")  # spaces don't matter
    assert rnd.won and rnd.solved_by_word and rnd.word_guess_hidden_letters == 6

    rnd = Round("HOUSE")
    assert not rnd.guess_word("MOUSE")
    assert rnd.lives == 6 - WRONG_WORD_PENALTY and rnd.misses == 1


def test_wrong_word_can_kill():
    rnd = Round("HOUSE", lives=1)
    rnd.guess_word("MOUSE")
    assert rnd.lost and rnd.lives == 0


def test_hint_reveals_missing_letter_and_costs_points():
    rnd = Round("ABCDE")
    rnd.guess_letter("A")
    before = rnd.score
    letter = rnd.hint(random.Random(1))
    assert letter in "BCDE" and letter in rnd.guessed and letter in rnd.hinted
    assert rnd.score == max(0, before - HINT_COST)
    assert letter not in rnd.typed


def test_hint_limits():
    rnd = Round("ABCDEFG")
    for _ in range(MAX_HINTS):
        assert rnd.hint() is not None
    assert rnd.hint() is None
    # Never hands out the final letter
    rnd = Round("AB")
    rnd.guess_letter("A")
    assert not rnd.can_hint()


def test_win_breakdown_flawless():
    rnd = Round("AB", difficulty="hard")
    rnd.guess_letter("A")
    rnd.guess_letter("B")
    parts = rnd.final_breakdown(mode_multiplier=3.0)
    assert parts["win"] == WIN_BONUS
    assert parts["flawless"] == FLAWLESS_BONUS
    assert parts["lives"] == 6 * LIFE_BONUS
    assert parts["multiplier"] == 6.0
    base = sum(parts[k] for k in ("letters", "win", "time", "lives", "flawless"))
    assert parts["total"] == int(base * 6.0)


def test_flawless_uses_round_misses_not_carried_lives():
    rnd = Round("AB", max_lives=6, lives=3)
    rnd.guess_letter("A")
    rnd.guess_letter("B")
    assert rnd.mistakes == 3 and rnd.misses == 0
    assert rnd.final_breakdown()["flawless"] == FLAWLESS_BONUS


def test_surrender_and_timeout():
    rnd = Round("CAT")
    rnd.surrender()
    assert rnd.lost and rnd.surrendered
    rnd = Round("CAT")
    rnd.time_out()
    assert rnd.lost and rnd.timed_out


def test_vowel_tracking():
    rnd = Round("RHYTHM")
    for letter in "RHYTM":
        rnd.guess_letter(letter)
    assert rnd.won and not rnd.typed_any_vowel()
    rnd = Round("CAT")
    rnd.guess_letter("A")
    assert rnd.typed_any_vowel()
