"""Drive the whole app with scripted input to make sure every screen and mode runs end to end."""

import builtins
import itertools
import random
import string

import pytest

from motl import ui
from motl.game import MENU_KEYS, App
from motl.paths import resource_path
from motl.storage import Profile
from motl.words import load_words


class Script:
    def __init__(self, menu, guesses=None):
        self.menu = list(menu)
        self.guesses = guesses or itertools.cycle(list("ETAOINSHRDLUCMFWYPVBGKJQXZ"))
        self.secrets = itertools.cycle(["luna park", "luna park", "gatto", "gatto"])
        self.log = []

    def __call__(self, prompt=""):
        self.log.append(prompt)
        p = prompt.lower()
        if "who dares" in p:
            return "Bot"
        if "pick a number" in p:
            if not self.menu:
                raise AssertionError("menu script exhausted")
            return self.menu.pop(0)
        if "impress me" in p:
            return next(self.guesses)
        if "another round" in p:
            return "N"
        if "name of player" in p:
            return ""
        if "how many rounds" in p:
            return "1"
        if "which mode" in p:
            return "1"
        if "type reset" in p:
            return "RESET"
        return ""


def run_app(monkeypatch, script, profile=None, seed=0):
    monkeypatch.setattr(builtins, "input", script)
    monkeypatch.setattr(ui.getpass, "getpass", lambda prompt="": next(script.secrets))
    profile = profile or Profile(None)
    term = ui.Terminal(animations=False)
    term.interactive = False
    lists = load_words(resource_path("words"))
    random.seed(seed)
    App(profile, lists, term, random.Random(seed)).run()
    return profile


def idx(key):
    return str(MENU_KEYS.index(key) + 1)


@pytest.mark.parametrize("mode", ["classic", "time", "sudden", "marathon", "daily"])
def test_each_mode_runs(monkeypatch, mode, capsys):
    profile = run_app(monkeypatch, Script([idx(mode), idx("quit")]))
    assert profile.stats["played"] >= 1
    out = capsys.readouterr().out
    assert "Thanks for playing" in out


def test_versus_runs(monkeypatch, capsys):
    profile = run_app(monkeypatch, Script([idx("versus"), idx("quit")]))
    assert "versus" in profile.achievements
    assert profile.stats["played"] == 0  # versus doesn't pollute your stats


def test_info_screens_and_settings(monkeypatch, capsys):
    # settings: cycle difficulty (1), toggle sound (3), back (7)
    menu = [idx("stats"), idx("achievements"), idx("leaderboard"), idx("help"),
            idx("settings"), "1", "3", "7", idx("quit")]
    profile = run_app(monkeypatch, Script(menu))
    assert profile.settings["difficulty"] == "medium"
    assert profile.settings["sound"] is True
    assert "Thanks for playing" in capsys.readouterr().out


def test_konami_and_easter_egg(monkeypatch):
    guesses = itertools.chain(["sudo", "?", "!", "1", "ab"], itertools.cycle(string.ascii_uppercase))
    profile = run_app(monkeypatch, Script(["uuddlrlrba", idx("classic"), idx("quit")], guesses=guesses))
    assert profile.settings["rainbow"] is True
    assert {"konami", "curious"} <= set(profile.achievements)
    assert "SUDO" in profile.stats["easter_eggs"]


def test_daily_only_once(monkeypatch, capsys):
    profile = run_app(monkeypatch, Script([idx("daily"), idx("daily"), idx("quit")]))
    assert profile.stats["played"] == 1
    assert "already played" in capsys.readouterr().out


def test_ctrl_c_exits_gracefully(monkeypatch, capsys):
    def boom(prompt=""):
        raise KeyboardInterrupt

    monkeypatch.setattr(builtins, "input", boom)
    term = ui.Terminal(animations=False)
    term.interactive = False
    App(Profile(None), load_words(resource_path("words")), term).run()
    assert "Rage quit" in capsys.readouterr().out


def test_time_attack_timeout(monkeypatch, capsys):
    from motl import game

    monkeypatch.setattr(game, "TIME_LIMIT", {"easy": -1, "medium": -1, "hard": -1})
    profile = run_app(monkeypatch, Script([idx("time"), idx("quit")]))
    assert profile.stats["lost"] == 1
    assert "TIME'S UP" in capsys.readouterr().out
