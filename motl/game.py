"""The application: menus, game modes and screens."""

import datetime as dt
import random
from typing import Dict, List, Optional

from colorama import Fore, Style

from . import __version__, art
from .achievements import ACHIEVEMENTS, evaluate_round
from .engine import (
    FREE_CHARS,
    HINT_COST,
    LETTERS,
    MAX_HINTS,
    WRONG_WORD_PENALTY,
    Outcome,
    Round,
    is_playable,
    normalize_word,
)
from .text import rank_for, raw, t
from .paths import custom_words_dir
from .storage import Profile
from .ui import QuitGame, Terminal
from .words import DIFFICULTIES, WordLists, WordPicker, daily_word

MENU_KEYS = [
    "classic", "time", "sudden", "marathon", "daily", "versus",
    "stats", "achievements", "leaderboard", "settings", "help", "quit",
]
PLAY_MODES = ("classic", "time", "sudden", "marathon")
RANKED_MODES = ("classic", "time", "sudden", "marathon", "daily")

MODE_LIVES = {"classic": 6, "time": 6, "sudden": 1, "marathon": 6, "daily": 6, "versus": 6}
MODE_MULTIPLIER = {"classic": 1.0, "time": 1.5, "sudden": 3.0, "marathon": 1.0, "daily": 1.0, "versus": 1.0}
TIME_LIMIT = {"easy": 60, "medium": 75, "hard": 90}
MARATHON_MAX_LIVES = 6

KONAMI = {"UUDDLRLRBA", "UUDDLRLRAB", "↑↑↓↓←→←→BA"}


class App:
    def __init__(self, profile: Profile, lists: WordLists, term: Terminal, rng: Optional[random.Random] = None):
        self.profile = profile
        self.lists = lists
        self.term = term
        self.rng = rng or random.Random()
        self.picker = WordPicker(lists, self.rng)

    # ----- helpers -------------------------------------------------------
    def t(self, key: str, **fmt):
        return t(key, **fmt)

    def raw(self, key: str):
        return raw(key)

    def save(self) -> None:
        if not self.profile.save() and self.profile.path:
            self.term.say(self.t("save_failed"), Fore.RED)

    def pause(self) -> None:
        self.term.pause(self.t("press_enter"))

    def mode_name(self, mode: str) -> str:
        return self.raw("mode_names").get(mode, mode)

    def diff_name(self, diff: str) -> str:
        return self.raw("difficulty_names").get(diff, diff)

    def apply_settings(self) -> None:
        s = self.profile.settings
        self.term.animations = s["animations"]
        self.term.sound = s["sound"]
        self.term.rainbow = s["rainbow"]

    # ----- entry ---------------------------------------------------------
    def run(self, start_mode: Optional[str] = None) -> None:
        self.apply_settings()
        try:
            self.title_screen(first=True)
            if start_mode:
                self.dispatch(start_mode)
            while True:
                choice = self.main_menu()
                if choice == "quit":
                    break
                self.dispatch(choice)
            self.term.say("\n" + self.t("thanks"), Fore.MAGENTA)
        except QuitGame:
            self.term.say("\n" + self.t("goodbye_interrupt"), Fore.MAGENTA)
        finally:
            self.save()

    def dispatch(self, choice: str) -> None:
        handlers = {
            "daily": self.play_daily,
            "versus": self.play_versus,
            "stats": self.show_stats,
            "achievements": self.show_achievements,
            "leaderboard": self.show_leaderboard,
            "settings": self.show_settings,
            "help": self.show_help,
        }
        if choice in PLAY_MODES:
            self.play_session(choice)
        elif choice in handlers:
            handlers[choice]()

    # ----- title & menu --------------------------------------------------
    def title_screen(self, first: bool = False) -> None:
        term = self.term
        term.clear()
        term.banner()
        term.say()
        term.say(f"🎮 {self.t('tagline')} 🎮", Fore.MAGENTA + Style.BRIGHT)
        term.say(self.t("credit"), Fore.GREEN)
        term.say(self.t("version", version=__version__), Fore.GREEN)
        term.say()
        if first and self.profile.load_error:
            term.say(self.t("save_broken"), Fore.RED)
        if first and not self.profile.name:
            name = term.ask(self.t("ask_name") + ":")
            self.profile.name = name or self.t("default_name")
            self.save()
        rank = rank_for(self.profile.stats["total_score"])
        term.say(self.t("welcome_back", name=self.profile.name, rank=rank), Fore.YELLOW)

    def main_menu(self) -> str:
        term = self.term
        self.title_screen()
        term.say()
        term.header(self.t("menu_title"))
        labels = self.raw("menu")
        for i, key in enumerate(MENU_KEYS, 1):
            term.say(f"  {Fore.YELLOW}{i:>2}{Style.RESET_ALL}  {labels[key]}")
        while True:
            answer = term.ask(f"\n{self.t('menu_prompt')}:")
            compact = answer.upper().replace(" ", "")
            if compact in KONAMI:
                self.toggle_rainbow()
                return "noop"
            if answer.isdigit() and 1 <= int(answer) <= len(MENU_KEYS):
                return MENU_KEYS[int(answer) - 1]
            term.say(self.t("menu_invalid"), Fore.RED)

    def toggle_rainbow(self) -> None:
        s = self.profile.settings
        s["rainbow"] = not s["rainbow"]
        self.apply_settings()
        state = self.t("on") if s["rainbow"] else self.t("off")
        self.term.flash(self.term.rainbowize(self.t("konami", state=state)), "")
        self.announce_achievements(["konami"] if self.profile.unlock("konami") else [])
        self.save()
        self.pause()

    def pick_difficulty(self) -> str:
        default = self.profile.settings["difficulty"]
        names = [self.diff_name(d) + ("  ←" if d == default else "") for d in DIFFICULTIES]
        self.term.say(f"\n{self.t('select_difficulty')}", Fore.CYAN)
        for i, label in enumerate(names, 1):
            self.term.say(f"  {Fore.YELLOW}{i}{Style.RESET_ALL}  {label}")
        mapping = {str(i): d for i, d in enumerate(DIFFICULTIES, 1)}
        for d in DIFFICULTIES:
            mapping[d] = d
            mapping[self.diff_name(d).lower()] = d
        while True:
            answer = self.term.ask(">").lower()
            if not answer:
                return default
            if answer in mapping:
                return mapping[answer]
            self.term.say("🚫 1 / 2 / 3", Fore.RED)

    # ----- rendering -----------------------------------------------------
    def render(self, rnd: Round, mode: str, info: Dict, messages: List[str], time_left: Optional[float]) -> None:
        term = self.term
        term.clear()
        top = [f"🎮 {self.mode_name(mode)}", self.diff_name(rnd.difficulty)]
        if info.get("word_no"):
            top.append(self.t("word_n", n=info["word_no"]))
        if info.get("subtitle"):
            top.append(info["subtitle"])
        term.say("  ·  ".join(top), Fore.MAGENTA + Style.BRIGHT)
        term.rule(Style.DIM)

        stage = 6 if rnd.lost else art.stage_index(rnd.mistakes, rnd.max_lives)
        term.say(art.stage_block(stage, dead=rnd.lost))

        if rnd.lost:
            reveal = []
            for c in rnd.word:
                if c in rnd.guessed or c in FREE_CHARS:
                    reveal.append(Style.BRIGHT + Fore.YELLOW + c + Style.RESET_ALL if c != " " else " ")
                else:
                    reveal.append(Style.BRIGHT + Fore.RED + c + Style.RESET_ALL)
            word_line = " ".join(reveal)
        else:
            word_line = term.word_line(rnd.masked())
        term.say(f"\n{Fore.CYAN}✨ {self.t('word')}:{Style.RESET_ALL}  {word_line}\n")

        hits = rnd.guessed & rnd.letters_needed
        term.say(term.keyboard(hits, rnd.wrong))
        shame = " ".join(rnd.wrong) or "—"
        term.say(f"\n{Fore.CYAN}📝 {self.t('guessed_letters')}: {Fore.RED}{shame}{Style.RESET_ALL}")
        term.say(f"{Fore.CYAN}💝 {self.t('remaining_attempts')}: {Style.RESET_ALL}{term.hearts(rnd.lives, rnd.max_lives)}")

        hud = [
            f"🏆 {self.t('score')}: {info.get('score', 0) + rnd.score}",
            f"🔥 {self.t('streak')}: {info.get('streak', 0)}",
        ]
        if rnd.combo >= 2:
            hud.append(f"⚡ {self.t('combo')}: x{rnd.combo_multiplier():g}")
        hud.append(f"💡 {self.t('hints_left')}: {MAX_HINTS - rnd.hints_used}")
        term.say("\n" + " | ".join(hud), Fore.MAGENTA)
        if time_left is not None and not rnd.over:
            term.say(f"{self.t('time_left')}: {term.countdown_text(time_left)}")
        if not rnd.over:
            term.say(self.t("controls"), Style.DIM)
        for msg in messages:
            term.say(msg)

    # ----- one round -----------------------------------------------------
    def play_round(self, rnd: Round, mode: str, info: Dict, time_limit: Optional[int] = None) -> None:
        """Interactive loop until the round is over. Leaves the final state on screen."""
        term = self.term
        messages: List[str] = []
        if mode == "time" and time_limit:
            messages.append(f"{Fore.YELLOW}{self.t('time_attack_info', secs=time_limit)}{Style.RESET_ALL}")
        if mode == "sudden":
            messages.append(f"{Fore.RED}{self.t('sudden_info')}{Style.RESET_ALL}")
        word_letters = "".join(c for c in rnd.word if c in LETTERS)
        letters_in_word = len(word_letters)

        while True:
            time_left = (time_limit - rnd.elapsed) if time_limit else None
            if time_left is not None and time_left <= 0 and not rnd.over:
                rnd.time_out()
                messages.append(f"{Fore.RED}{Style.BRIGHT}{self.t('time_up')}{Style.RESET_ALL}")
            self.render(rnd, mode, info, messages, time_left)
            messages = []
            if rnd.over:
                return

            answer = term.ask(f"\n👉 {self.t('enter_guess')}:")
            if time_limit and rnd.elapsed > time_limit:
                continue  # too slow: the top of the loop declares the timeout
            upper = answer.upper().strip()
            letters_only = normalize_word(upper).replace(" ", "")

            if not upper:
                continue
            if upper == "?":
                messages.append(f"{Fore.CYAN}{self.t('help_text')}{Style.RESET_ALL}")
                continue
            if upper == "!":
                letter = rnd.hint(self.rng)
                if letter:
                    messages.append(f"{Fore.YELLOW}{self.t('hint_given', letter=letter, cost=HINT_COST)}{Style.RESET_ALL}")
                else:
                    messages.append(f"{Fore.RED}{self.t('no_hint')}{Style.RESET_ALL}")
                continue
            if upper in (":Q", ":QUIT", "/QUIT", ":Q!"):
                if term.confirm(self.t("confirm_surrender"), self.raw("yes")):
                    rnd.surrender()
                continue

            eggs = self.raw("easter")
            if upper in eggs and letters_only != word_letters:
                messages.append(f"{Fore.MAGENTA}🥚 {eggs[upper]}{Style.RESET_ALL}")
                found = self.profile.stats["easter_eggs"]
                if upper not in found:
                    found.append(upper)
                self.announce_achievements(["curious"] if self.profile.unlock("curious") else [], inline=messages)
                continue

            if len(letters_only) == 1:
                messages.extend(self.letter_feedback(rnd, letters_only))
                continue

            clean = normalize_word(upper)
            if len(letters_only) == letters_in_word and all(c in LETTERS or c in FREE_CHARS for c in clean):
                prompt = self.t("confirm_word", guess=clean, n=WRONG_WORD_PENALTY)
                if term.confirm(prompt, self.raw("yes")):
                    if rnd.guess_word(clean):
                        messages.append(f"{Fore.GREEN}{Style.BRIGHT}{self.t('word_right')}{Style.RESET_ALL}")
                    else:
                        messages.append(f"{Fore.RED}{self.t('word_wrong', n=WRONG_WORD_PENALTY)}{Style.RESET_ALL}")
                continue

            if all(c in LETTERS for c in letters_only):
                messages.append(f"{Fore.RED}{self.t('single_letter')}{Style.RESET_ALL}")
            else:
                messages.append(f"{Fore.RED}{self.t('valid_letter')}{Style.RESET_ALL}")

    def letter_feedback(self, rnd: Round, letter: str) -> List[str]:
        res = rnd.guess_letter(letter)
        if res.outcome == Outcome.INVALID:
            return [f"{Fore.RED}{self.t('valid_letter')}{Style.RESET_ALL}"]
        if res.outcome == Outcome.REPEAT:
            return [f"{Fore.YELLOW}{self.t('already_guessed')}{Style.RESET_ALL}"]
        if res.outcome == Outcome.HIT:
            out = [f"{Fore.GREEN}{self.t('good_guess')}  {Style.BRIGHT}{self.t('hit_points', points=res.points)}{Style.RESET_ALL}"]
            if res.occurrences >= 3:
                out.append(f"{Fore.GREEN}{self.t('multi_hit', n=res.occurrences, points=res.points)}{Style.RESET_ALL}")
            if res.combo >= 2:
                out.append(f"{Fore.YELLOW}{Style.BRIGHT}{self.t('combo_msg', n=res.combo, mult=f'{rnd.combo_multiplier():g}')}{Style.RESET_ALL}")
            return out
        out = [f"{Fore.RED}{self.t('wrong_guess')}{Style.RESET_ALL}"]
        if 0 < rnd.lives <= 3:
            out.append(f"{Fore.CYAN}{self.t('encouragement')}{Style.RESET_ALL}")
        return out

    def round_outro(self, rnd: Round, mode_mult: float) -> int:
        """Celebrate or mourn. Returns the points awarded."""
        term = self.term
        breakdown = rnd.final_breakdown(mode_mult)
        if rnd.won:
            term.bell()
            term.confetti()
            term.dance()
            term.flash(f"🎉 {self.t('you_won')} — {rnd.word}", Fore.GREEN)
            labels = self.raw("breakdown")
            for key in ("letters", "win", "time", "lives", "flawless"):
                if breakdown.get(key):
                    term.say(f"   {labels[key]:<24} {Fore.GREEN}+{breakdown[key]}{Style.RESET_ALL}")
            if breakdown.get("multiplier", 1) != 1:
                term.say(f"   {labels['multiplier']:<24} {Fore.YELLOW}x{breakdown['multiplier']:g}{Style.RESET_ALL}")
            term.say(f"   {labels['total']:<24} {Fore.YELLOW}{Style.BRIGHT}{breakdown['total']}{Style.RESET_ALL}")
        else:
            term.bell()
            term.swing()
            term.say(f"\n💔 {self.t('you_lost')}: {Fore.YELLOW}{rnd.word}{Style.RESET_ALL}", Fore.RED)
        return breakdown["total"]

    def announce_achievements(self, ids: List[str], inline: Optional[List[str]] = None) -> None:
        for ach_id in ids:
            emoji, name, desc = ACHIEVEMENTS[ach_id]
            text = f"{self.t('achievement_unlocked')}: {emoji} {name} — {desc}"
            if inline is not None:
                inline.append(f"{Fore.YELLOW}{Style.BRIGHT}{text}{Style.RESET_ALL}")
            else:
                self.term.bell()
                self.term.flash(text, Fore.YELLOW)

    # ----- modes ---------------------------------------------------------
    def play_session(self, mode: str) -> None:
        term = self.term
        diff = self.pick_difficulty()
        if not self.picker.has_words(diff):
            term.say(self.t("no_words", diff=diff), Fore.RED)
            self.pause()
            return

        score = streak = best_streak = words_survived = 0
        lives = MODE_LIVES[mode]
        mult = MODE_MULTIPLIER[mode]
        time_limit = TIME_LIMIT[diff] if mode == "time" else None

        while True:
            word = self.picker.pick(diff)
            max_lives = MARATHON_MAX_LIVES if mode == "marathon" else MODE_LIVES[mode]
            rnd = Round(word, max_lives=max_lives, lives=lives if mode == "marathon" else None, difficulty=diff)
            info = {"score": score, "streak": streak}
            if mode == "marathon":
                info["word_no"] = words_survived + 1
            self.play_round(rnd, mode, info, time_limit)

            points = self.round_outro(rnd, mult)
            score += points
            if rnd.won:
                streak += 1
                best_streak = max(best_streak, streak)
                words_survived += 1
            else:
                streak = 0
            self.profile.record_round(rnd, points)
            if mode == "marathon":
                stats = self.profile.stats
                stats["marathon_best"] = max(stats["marathon_best"], words_survived)
            self.announce_achievements(evaluate_round(rnd, mode, self.profile, marathon_words=words_survived))
            self.save()
            term.say(self.t("session_score", score=score, streak=streak), Fore.CYAN)

            if mode == "marathon":
                if not rnd.won:
                    term.say(self.t("marathon_over", n=words_survived), Fore.MAGENTA + Style.BRIGHT)
                    break
                lives = min(MARATHON_MAX_LIVES, rnd.lives + 1)
                if rnd.lives < MARATHON_MAX_LIVES:
                    term.say(self.t("marathon_life"), Fore.GREEN)
                self.pause()
                continue
            if not term.confirm(f"\n{self.t('play_again')}", self.raw("yes")):
                break

        rank = self.profile.add_leaderboard(score, mode, diff)
        self.save()
        term.say(f"\n{self.t('final_score', score=score, streak=best_streak)}", Fore.MAGENTA + Style.BRIGHT)
        if rank:
            term.flash(self.t("new_record", rank=rank, mode=self.mode_name(mode)), Fore.YELLOW)
        self.pause()

    def play_daily(self) -> None:
        term = self.term
        today = dt.date.today()
        term.clear()
        term.header(self.mode_name("daily"))
        previous = self.profile.daily_result(today)
        if previous:
            term.say(self.t("daily_done"), Fore.YELLOW)
            self.show_daily_share(today, previous)
            self.show_daily_countdown()
            self.pause()
            return
        try:
            word = daily_word(self.lists, today)
        except LookupError:
            term.say(self.t("no_words", diff="daily"), Fore.RED)
            self.pause()
            return
        term.say(self.t("daily_intro", date=today.isoformat()), Fore.CYAN)
        self.pause()
        rnd = Round(word, max_lives=MODE_LIVES["daily"], difficulty="medium")
        # Book the attempt up front: quitting halfway must not grant a retry.
        self.profile.record_daily(today, rnd)
        self.save()
        self.play_round(rnd, "daily", {"score": 0, "streak": self.profile.daily_streak(today)})
        points = self.round_outro(rnd, MODE_MULTIPLIER["daily"])
        self.profile.record_daily(today, rnd)
        self.profile.record_round(rnd, points)
        self.announce_achievements(evaluate_round(rnd, "daily", self.profile))
        self.profile.add_leaderboard(points, "daily", "medium")
        self.save()
        self.show_daily_share(today, self.profile.daily_result(today))
        self.show_daily_countdown()
        self.pause()

    def show_daily_share(self, day: dt.date, result: dict) -> None:
        grid = "".join("🟩" if c == "1" else "🟥" for c in result.get("history", ""))
        verdict = "✅" if result.get("won") else "💀"
        hints = " " + "💡" * result.get("hints", 0) if result.get("hints") else ""
        line = (
            f"Man On The Line {day.isoformat()} {verdict} "
            f"{result.get('mistakes', 0)}/{result.get('max_lives', 6)} · {result.get('seconds', 0)}s"
        )
        self.term.say(f"\n{self.t('daily_share')}", Fore.CYAN)
        self.term.say(f"  {line}\n  {grid}{hints}", Style.BRIGHT)
        self.term.say(self.t("daily_streak", n=self.profile.daily_streak(day)), Fore.YELLOW)

    def show_daily_countdown(self) -> None:
        now = dt.datetime.now()
        midnight = dt.datetime.combine(now.date() + dt.timedelta(days=1), dt.time())
        mins = int((midnight - now).total_seconds() // 60)
        self.term.say(self.t("daily_next", h=mins // 60, m=mins % 60), Style.DIM)

    def ask_secret_word(self, setter: str, guesser: str) -> str:
        term = self.term
        while True:
            first = normalize_word(term.ask_secret(self.t("versus_secret", setter=setter, guesser=guesser) + ":"))
            if not is_playable(first):
                term.say(self.t("versus_secret_invalid"), Fore.RED)
                continue
            second = normalize_word(term.ask_secret(self.t("versus_secret_again") + ":"))
            if first != second:
                term.say(self.t("versus_secret_mismatch"), Fore.RED)
                continue
            return first

    def play_versus(self) -> None:
        term = self.term
        term.clear()
        term.header(self.mode_name("versus"))
        term.say(self.t("versus_intro"), Fore.CYAN)
        names = []
        for n in (1, 2):
            default = self.profile.name if n == 1 else f"Player {n}"
            name = term.ask(f"{self.t('versus_player', n=n)} [{default}]:")[:20] or default
            names.append(name)
        if names[0] == names[1]:
            names[1] += " (2)"
        rounds = 0
        while not 1 <= rounds <= 10:
            answer = term.ask(f"{self.t('versus_rounds')} [3]:") or "3"
            rounds = int(answer) if answer.isdigit() else 0

        scores = {name: 0 for name in names}
        for r in range(rounds):
            for guesser_idx in (1, 0):
                guesser, setter = names[guesser_idx], names[1 - guesser_idx]
                term.clear()
                term.header(f"{self.mode_name('versus')} — {r + 1}/{rounds}")
                secret = self.ask_secret_word(setter, guesser)
                term.clear()
                term.say(self.t("versus_your_turn", name=guesser, setter=setter), Fore.YELLOW + Style.BRIGHT)
                self.pause()
                rnd = Round(secret, max_lives=MODE_LIVES["versus"], difficulty="medium")
                info = {"score": scores[guesser], "streak": 0, "subtitle": f"🎯 {guesser}"}
                self.play_round(rnd, "versus", info)
                scores[guesser] += self.round_outro(rnd, MODE_MULTIPLIER["versus"])
                term.say(f"\n{self.t('versus_score')}:", Fore.CYAN)
                for name in names:
                    term.say(f"   {name:<20} {scores[name]}", Fore.YELLOW)
                self.pause()

        term.clear()
        term.header(self.t("versus_score"))
        for name in sorted(names, key=lambda n: -scores[n]):
            term.say(f"   {name:<20} {scores[name]}", Fore.YELLOW)
        a, b = names
        if scores[a] == scores[b]:
            term.say("\n" + self.t("versus_tie"), Fore.CYAN)
        else:
            winner, loser = (a, b) if scores[a] > scores[b] else (b, a)
            term.confetti()
            term.say("\n" + art.TROPHY, Fore.YELLOW)
            term.say(self.t("versus_winner", name=winner, loser=loser), Fore.GREEN + Style.BRIGHT)
        self.announce_achievements(["versus"] if self.profile.unlock("versus") else [])
        self.save()
        self.pause()

    # ----- info screens --------------------------------------------------
    def show_stats(self) -> None:
        term = self.term
        s = self.profile.stats
        labels = self.raw("stats")
        term.clear()
        term.header(self.t("stats_title"))
        played = s["played"]
        win_rate = f"{100 * s['won'] / played:.1f}%" if played else "—"
        fastest = f"{s['fastest_win']:.1f}s" if s["fastest_win"] is not None else self.t("never")
        minutes = int(s["time_played"] // 60)
        fav = max(s["letters_typed"].items(), key=lambda kv: kv[1])[0] if s["letters_typed"] else "—"
        rows = [
            ("rank", rank_for(s["total_score"])),
            ("played", played),
            ("won", s["won"]),
            ("lost", s["lost"]),
            ("win_rate", win_rate),
            ("current_streak", s["current_streak"]),
            ("best_streak", s["best_streak"]),
            ("total_score", s["total_score"]),
            ("best_session", s["best_session"]),
            ("fastest_win", fastest),
            ("max_combo", s["max_combo"]),
            ("marathon_best", s["marathon_best"]),
            ("daily_streak", self.profile.daily_streak(dt.date.today())),
            ("word_guesses_right", s["word_guesses_right"]),
            ("hints_used", s["hints_used"]),
            ("fav_letter", fav),
            ("time_played", f"{minutes // 60}h {minutes % 60}m"),
        ]
        for key, value in rows:
            term.say(f"  {labels[key]:<28} {Fore.YELLOW}{value}{Style.RESET_ALL}")
        hist = s["mistakes_on_win"]
        top = max(hist) if any(hist) else 0
        term.say(f"\n  {labels['histogram']}:", Fore.CYAN)
        for i, count in enumerate(hist):
            label = f"{i}+" if i == len(hist) - 1 else str(i)
            term.say(f"   {label:>2} {Fore.GREEN}{term.bar(count, top)}{Style.RESET_ALL} {count}")
        self.pause()

    def show_achievements(self) -> None:
        term = self.term
        term.clear()
        term.header(self.t("achievements_title"))
        unlocked = self.profile.achievements
        secret = {"curious", "konami"}
        for ach_id in ACHIEVEMENTS:
            emoji, name, desc = ACHIEVEMENTS[ach_id]
            if ach_id in unlocked:
                date = unlocked[ach_id][:10]
                term.say(f"  {emoji}  {Fore.YELLOW}{Style.BRIGHT}{name}{Style.RESET_ALL} — {desc} {Style.DIM}({date}){Style.RESET_ALL}")
            elif ach_id in secret:
                term.say(f"  🔒  {Style.DIM}{self.t('locked')} — {self.t('locked')}{Style.RESET_ALL}")
            else:
                term.say(f"  🔒  {Style.DIM}{name} — {desc}{Style.RESET_ALL}")
        count = len([a for a in unlocked if a in ACHIEVEMENTS])
        term.say(f"\n  {self.t('unlocked_count', n=count, total=len(ACHIEVEMENTS))}", Fore.CYAN)
        term.say(f"  {term.bar(count, len(ACHIEVEMENTS), 30)}", Fore.GREEN)
        self.pause()

    def show_leaderboard(self) -> None:
        term = self.term
        term.clear()
        term.header(self.t("leaderboard_title"))
        options = [self.t("all_modes")] + [self.mode_name(m) for m in RANKED_MODES]
        for i, label in enumerate(options):
            term.say(f"  {Fore.YELLOW}{i}{Style.RESET_ALL}  {label}")
        answer = term.ask(f"\n{self.t('leaderboard_pick')}:")
        mode = None
        if answer.isdigit() and 1 <= int(answer) <= len(RANKED_MODES):
            mode = RANKED_MODES[int(answer) - 1]
        entries = self.profile.top(mode, 10)
        term.clear()
        term.header(f"{self.t('leaderboard_title')} — {self.mode_name(mode) if mode else self.t('all_modes')}")
        if not entries:
            term.say(f"\n  {self.t('leaderboard_empty')}", Style.DIM)
        medals = ["🥇", "🥈", "🥉"]
        for i, e in enumerate(entries):
            medal = medals[i] if i < 3 else f"{i + 1:>2}."
            term.say(
                f"  {medal} {Fore.YELLOW}{e.get('name', '?')[:16]:<16}{Style.RESET_ALL} "
                f"{Style.BRIGHT}{e.get('score', 0):>7}{Style.RESET_ALL}  "
                f"{Fore.CYAN}{self.mode_name(e.get('mode', ''))[:16]:<16}{Style.RESET_ALL} "
                f"{self.diff_name(e.get('difficulty', ''))[:9]:<9} "
                f"{Style.DIM}{e.get('date', '')}{Style.RESET_ALL}"
            )
        self.pause()

    def show_settings(self) -> None:
        term = self.term
        while True:
            s = self.profile.settings
            labels = self.raw("settings")
            term.clear()
            term.header(self.t("settings_title"))
            onoff = lambda v: f"{Fore.GREEN}{self.t('on')}" if v else f"{Fore.RED}{self.t('off')}"  # noqa: E731
            items = [
                ("difficulty", f"{Fore.YELLOW}{self.diff_name(s['difficulty'])}"),
                ("animations", onoff(s["animations"])),
                ("sound", onoff(s["sound"])),
                ("rainbow", onoff(s["rainbow"])),
                ("name", f"{Fore.YELLOW}{self.profile.name}"),
                ("reset", ""),
                ("back", ""),
            ]
            options = [f"{labels[k]:<30} {v}{Style.RESET_ALL}" for k, v in items]
            key = items[term.choose(self.t("menu_prompt"), options, self.t("menu_invalid"))][0]
            if key == "back":
                break
            if key == "difficulty":
                s["difficulty"] = DIFFICULTIES[(DIFFICULTIES.index(s["difficulty"]) + 1) % len(DIFFICULTIES)] \
                    if s["difficulty"] in DIFFICULTIES else "easy"
            elif key in ("animations", "sound", "rainbow"):
                s[key] = not s[key]
            elif key == "name":
                name = term.ask(self.t("ask_name") + ":")
                if name:
                    self.profile.name = name
            elif key == "reset":
                if term.ask(self.t("reset_confirm") + ":") == "RESET":
                    self.profile.reset()
                    term.say(self.t("reset_done"), Fore.GREEN)
                else:
                    term.say(self.t("reset_cancel"), Fore.YELLOW)
                self.pause()
            self.apply_settings()
            self.save()

    def show_help(self) -> None:
        term = self.term
        term.clear()
        term.header(self.raw("menu")["help"].split("—")[0].strip())
        for line in self.raw("how_to_play"):
            term.say("  • " + line.format(folder=custom_words_dir()), Fore.CYAN)
        term.say("\n" + self.t("help_text"), Style.DIM)
        self.pause()
