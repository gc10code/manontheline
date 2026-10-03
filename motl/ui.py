"""Terminal helpers: colors, animations, input. Everything visual lives here."""

import getpass
import random
import shutil
import sys
import time
from typing import Iterable, List, Optional

from colorama import Fore, Style

from . import art

RAINBOW = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]


class QuitGame(Exception):
    """Raised on Ctrl+C / Ctrl+D so the app can save and say goodbye."""


class Terminal:
    def __init__(self, animations: bool = True, sound: bool = False, rainbow: bool = False):
        self.animations = animations
        self.sound = sound
        self.rainbow = rainbow
        self.force_no_anim = False
        self.interactive = sys.stdin.isatty() and sys.stdout.isatty()

    # ----- basics --------------------------------------------------------
    @property
    def animate(self) -> bool:
        return self.animations and self.interactive and not self.force_no_anim

    @property
    def width(self) -> int:
        return max(40, shutil.get_terminal_size((80, 24)).columns)

    def clear(self) -> None:
        if self.interactive:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
        else:
            print()

    def sleep(self, seconds: float) -> None:
        if self.animate:
            time.sleep(seconds)

    def bell(self) -> None:
        if self.sound:
            sys.stdout.write("\a")
            sys.stdout.flush()

    def say(self, text: str = "", color: str = "") -> None:
        print(f"{color}{text}{Style.RESET_ALL}" if color else text)

    def typewrite(self, text: str, color: str = "", delay: float = 0.012) -> None:
        if not self.animate:
            self.say(text, color)
            return
        sys.stdout.write(color)
        for ch in text:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write(Style.RESET_ALL + "\n")
        sys.stdout.flush()

    def rainbowize(self, text: str, offset: int = 0) -> str:
        out, i = [], offset
        for ch in text:
            if ch.strip():
                out.append(RAINBOW[i % len(RAINBOW)] + ch)
                i += 1
            else:
                out.append(ch)
        return "".join(out) + Style.RESET_ALL

    def rule(self, color: str = Fore.CYAN, char: str = "─") -> None:
        self.say(char * min(self.width, 78), color)

    def header(self, title: str, color: str = Fore.CYAN) -> None:
        inner = min(self.width, 78) - 2
        self.say("╔" + "═" * inner + "╗", color)
        pad = inner - len(title)
        left = pad // 2
        self.say("║" + " " * left + Fore.YELLOW + Style.BRIGHT + title + Style.RESET_ALL + color + " " * (pad - left) + "║", color)
        self.say("╚" + "═" * inner + "╝", color)

    # ----- input ---------------------------------------------------------
    def ask(self, prompt: str, color: str = Fore.CYAN) -> str:
        try:
            return input(f"{color}{prompt}{Style.RESET_ALL} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise QuitGame()

    def ask_secret(self, prompt: str) -> str:
        try:
            return getpass.getpass(f"{Fore.CYAN}{prompt}{Style.RESET_ALL} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise QuitGame()

    def confirm(self, prompt: str, yes: Iterable[str]) -> bool:
        return self.ask(prompt).upper() in set(yes)

    def pause(self, prompt: str) -> None:
        self.ask(f"\n{prompt}", Style.DIM)

    def choose(self, prompt: str, options: List[str], invalid: str) -> int:
        """Show a numbered list and return the chosen 0-based index."""
        for i, label in enumerate(options, 1):
            self.say(f"  {Fore.YELLOW}{i:>2}{Style.RESET_ALL}  {label}")
        while True:
            answer = self.ask(f"\n{prompt}:")
            if answer.isdigit() and 1 <= int(answer) <= len(options):
                return int(answer) - 1
            self.say(invalid, Fore.RED)

    # ----- game widgets --------------------------------------------------
    def word_line(self, masked: List[str]) -> str:
        cells = []
        for i, c in enumerate(masked):
            if c == " ":
                cells.append("  ")
            elif c == "_":
                cells.append(Fore.WHITE + Style.DIM + "_" + Style.RESET_ALL)
            elif self.rainbow:
                cells.append(Style.BRIGHT + RAINBOW[i % len(RAINBOW)] + c + Style.RESET_ALL)
            else:
                cells.append(Style.BRIGHT + Fore.YELLOW + c + Style.RESET_ALL)
        return " ".join(cells)

    def keyboard(self, hits: Iterable[str], misses: Iterable[str]) -> str:
        hits, misses = set(hits), set(misses)
        rows = []
        for n, row in enumerate(art.KEYBOARD_ROWS):
            keys = []
            for k in row:
                if k in hits:
                    keys.append(Style.BRIGHT + Fore.GREEN + k + Style.RESET_ALL)
                elif k in misses:
                    keys.append(Fore.RED + Style.DIM + k + Style.RESET_ALL)
                else:
                    keys.append(Fore.WHITE + k + Style.RESET_ALL)
            rows.append("      " + " " * n + " ".join(keys))
        return "\n".join(rows)

    @staticmethod
    def hearts(lives: int, max_lives: int) -> str:
        return "❤️ " * max(0, lives) + "🖤 " * max(0, max_lives - lives)

    @staticmethod
    def bar(value: int, maximum: int, width: int = 24) -> str:
        if maximum <= 0:
            return ""
        filled = round(width * value / maximum)
        return "█" * filled + "░" * (width - filled)

    # ----- animations ----------------------------------------------------
    def banner(self) -> None:
        lines = art.BANNER.splitlines()
        fits = self.width >= max(len(l) for l in lines)
        if not fits:
            self.say("  MAN ON THE LINE", Fore.YELLOW + Style.BRIGHT)
            return
        for i, line in enumerate(lines):
            if self.rainbow:
                self.say(self.rainbowize(line, i))
            else:
                self.say(line, Fore.YELLOW + Style.BRIGHT if i % 2 == 0 else Fore.CYAN + Style.BRIGHT)
            self.sleep(0.06)

    def confetti(self, rows: int = 8, frames: int = 14) -> None:
        if not self.animate:
            return
        width = min(self.width, 70)
        field = [[" "] * width for _ in range(rows)]
        sys.stdout.write("\n" * rows)
        for _ in range(frames):
            field.pop()
            field.insert(0, [
                random.choice(art.CONFETTI_COLORS) + random.choice(art.CONFETTI_CHARS) + Style.RESET_ALL
                if random.random() < 0.18 else " "
                for _ in range(width)
            ])
            sys.stdout.write(f"\033[{rows}A")
            for row in field:
                sys.stdout.write("\033[2K" + "".join(row) + "\n")
            sys.stdout.flush()
            time.sleep(0.07)

    def _frames(self, frames: List[List[str]], color: str, cycles: int, delay: float) -> None:
        height = len(frames[0])
        if not self.animate:
            self.say("\n".join(frames[0]), color)
            return
        sys.stdout.write("\n" * height)
        for i in range(cycles * len(frames)):
            sys.stdout.write(f"\033[{height}A")
            for line in frames[i % len(frames)]:
                sys.stdout.write("\033[2K" + color + line + Style.RESET_ALL + "\n")
            sys.stdout.flush()
            time.sleep(delay)

    def dance(self) -> None:
        self._frames(art.FREED_FRAMES, Fore.GREEN + Style.BRIGHT, cycles=3, delay=0.18)

    def swing(self) -> None:
        frames = [art.gallows(6, dead=True, sway=s) for s in (0, 1, 0, -1)]
        self._frames(frames, Fore.RED, cycles=3, delay=0.15)

    def flash(self, text: str, color: str = Fore.YELLOW, times: int = 3) -> None:
        if not self.animate:
            self.say(text, color + Style.BRIGHT)
            return
        for i in range(times * 2):
            style = color + Style.BRIGHT if i % 2 == 0 else Style.DIM
            sys.stdout.write("\r\033[2K" + style + text + Style.RESET_ALL)
            sys.stdout.flush()
            time.sleep(0.12)
        sys.stdout.write("\r\033[2K" + color + Style.BRIGHT + text + Style.RESET_ALL + "\n")
        sys.stdout.flush()

    def countdown_text(self, seconds: Optional[float]) -> str:
        if seconds is None:
            return ""
        s = max(0, int(seconds))
        color = Fore.GREEN if s > 20 else Fore.YELLOW if s > 10 else Fore.RED + Style.BRIGHT
        return f"{color}⏱️  {s}s{Style.RESET_ALL}"
