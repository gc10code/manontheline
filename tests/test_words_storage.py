import datetime as dt
import json
import os
import random

from motl.achievements import ACHIEVEMENTS, evaluate_round
from motl.engine import Round, is_playable
from motl.paths import resource_path
from motl.storage import Profile
from motl.words import DIFFICULTIES, WordPicker, daily_word, load_word_file, load_words


def test_bundled_lists_are_clean():
    lists = load_words(resource_path("words"))
    for diff in DIFFICULTIES:
        words = lists[diff]
        assert len(words) >= 20, diff
        assert all(is_playable(w) for w in words)


def test_word_file_parsing(tmp_path):
    f = tmp_path / "easy.txt"
    f.write_text("# comment\ncat\n\nCAT\nc4t\nX\nice  cream\n", encoding="utf-8")
    assert load_word_file(str(f)) == ["CAT", "ICE CREAM"]


def test_extra_folder_merges(tmp_path):
    (tmp_path / "easy.txt").write_text("ZEBRA\nCAT\n", encoding="utf-8")
    lists = load_words(resource_path("words"), str(tmp_path), "/does/not/exist")
    assert "ZEBRA" in lists["easy"]
    assert lists["easy"].count("CAT") == 1


def test_picker_avoids_repeats():
    lists = {"easy": ["AA", "BB", "CC"], "medium": [], "hard": []}
    picker = WordPicker(lists, random.Random(0))
    assert sorted(picker.pick("easy") for _ in range(3)) == ["AA", "BB", "CC"]
    picker.pick("easy")  # wraps around without crashing


def test_daily_word_is_deterministic():
    lists = load_words(resource_path("words"))
    day = dt.date(2026, 10, 3)
    assert daily_word(lists, day) == daily_word(lists, day)
    words = {daily_word(lists, day + dt.timedelta(days=i)) for i in range(30)}
    assert len(words) > 5


def _won_round(word="CAT", **kw):
    rnd = Round(word, **kw)
    for c in set(rnd.word.replace(" ", "")):
        rnd.guess_letter(c)
    return rnd


def test_profile_roundtrip_and_stats(tmp_path):
    path = str(tmp_path / "save.json")
    p = Profile(path)
    p.name = "Tester"
    p.record_round(_won_round(), 1234)
    lost = Round("DOG")
    for c in "XYZQWK":
        lost.guess_letter(c)
    p.record_round(lost, 0)
    assert p.save()

    q = Profile(path)
    s = q.stats
    assert q.name == "Tester"
    assert (s["played"], s["won"], s["lost"]) == (2, 1, 1)
    assert s["best_streak"] == 1 and s["current_streak"] == 0
    assert s["total_score"] == 1234
    assert s["mistakes_on_win"][0] == 1


def test_corrupt_save_is_moved_aside(tmp_path):
    path = tmp_path / "save.json"
    path.write_text("{not json", encoding="utf-8")
    p = Profile(str(path))
    assert p.load_error
    assert os.path.exists(str(path) + ".broken")
    assert p.stats["played"] == 0


def test_old_or_partial_save_gets_defaults(tmp_path):
    path = tmp_path / "save.json"
    path.write_text(json.dumps({"name": "Old", "stats": {"won": 3, "played": "bad"}}), encoding="utf-8")
    p = Profile(str(path))
    assert p.name == "Old" and p.stats["won"] == 3 and p.stats["played"] == 0
    assert p.settings["difficulty"] == "easy"


def test_leaderboard_ranking():
    p = Profile(None)
    assert p.add_leaderboard(0, "classic", "easy") == 0
    assert p.add_leaderboard(100, "classic", "easy") == 1
    assert p.add_leaderboard(500, "classic", "easy") == 1
    assert p.add_leaderboard(300, "classic", "easy") == 2
    assert p.add_leaderboard(50, "sudden", "easy") == 1
    assert [e["score"] for e in p.top("classic")] == [500, 300, 100]
    assert p.stats["best_session"] == 500


def test_daily_streak():
    p = Profile(None)
    today = dt.date(2026, 10, 3)
    for back in (0, 1, 2):
        p.record_daily(today - dt.timedelta(days=back), _won_round())
    assert p.daily_streak(today) == 3
    assert p.daily_streak(today + dt.timedelta(days=1)) == 3  # today not played yet
    assert p.daily_streak(today + dt.timedelta(days=2)) == 0


def test_achievements_unlock_once():
    p = Profile(None)
    rnd = _won_round("RHYTHM")
    p.record_round(rnd, 100)
    got = evaluate_round(rnd, "sudden", p, now=dt.datetime(2026, 1, 1, 3, 0))
    assert {"first_win", "flawless", "sudden_death", "no_vowels", "night_owl"} <= set(got)
    assert evaluate_round(rnd, "sudden", p) == []


def test_well_rounded_needs_every_difficulty():
    p = Profile(None)
    for diff in ("easy", "medium"):
        rnd = _won_round(difficulty=diff)
        p.record_round(rnd, 100)
        assert "well_rounded" not in evaluate_round(rnd, "classic", p)
    rnd = _won_round(difficulty="hard")
    p.record_round(rnd, 100)
    assert "well_rounded" in evaluate_round(rnd, "classic", p)


def test_achievement_table_is_well_formed():
    for ach in ACHIEVEMENTS.values():
        assert len(ach) == 3 and all(isinstance(x, str) and x for x in ach)
