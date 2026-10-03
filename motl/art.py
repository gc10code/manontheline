"""ASCII art and the original stage-by-stage commentary."""

from colorama import Fore, Style

BANNER = r"""
 __  __               ___          _____ _              _     _
|  \/  | __ _ _ __   / _ \ _ __   |_   _| |__   ___    | |   (_)_ __   ___
| |\/| |/ _` | '_ \ | | | | '_ \    | | | '_ \ / _ \   | |   | | '_ \ / _ \
| |  | | (_| | | | || |_| | | | |   | | | | | |  __/   | |___| | | | |  __/
|_|  |_|\__,_|_| |_| \___/|_| |_|   |_| |_| |_|\___|   |_____|_|_| |_|\___|
""".strip("\n")

# Body parts per number of mistakes (0..6). Each frame is 7 lines tall.
_GALLOWS = [
    "  +---+  ",
    "  |   |  ",
    "  {h}   |  ",
    " {la}{b}{ra}  |  ",
    " {ll} {rl}  |  ",
    "      |  ",
    "========= ",
]

STAGE_COLORS = [Fore.MAGENTA, Fore.CYAN, Fore.BLUE, Fore.YELLOW, Fore.GREEN, Fore.RED, Fore.RED]

# The original commentary, two lines per stage.
STAGE_QUOTES = [
    ("Wow, not even a single mistake yet? Miraculous!", "Let's see how long that lasts! 😏"),
    ("Oops, first mistake!", "Guess we're warming up for the disaster. 😊"),
    ("Oh look, a body!", "Someone's making progress... in the wrong direction. 🤔"),
    ("A single arm, so generous!", "Maybe I'll wave goodbye to your chances. 👋"),
    ("Two arms! Wow, you're building me faster than IKEA furniture!", "Feeling proud yet? 🤗"),
    ("One leg... impressive balance!", "But let's face it, I'm doomed anyway. 💃"),
    ("And there it is, the masterpiece of your failure.", "Game Over! You really excelled at losing. 😱"),
]


def stage_index(mistakes: int, max_lives: int) -> int:
    """Map mistakes to one of the 7 frames, whatever the number of lives."""
    if max_lives <= 0:
        return 6
    if mistakes >= max_lives:
        return 6
    return min(6, round(mistakes * 6 / max_lives))


def gallows(stage: int, dead: bool = False, sway: int = 0) -> list:
    parts = {
        "h": ("X" if dead else "O") if stage >= 1 else " ",
        "b": "|" if stage >= 2 else " ",
        "la": "/" if stage >= 3 else " ",
        "ra": "\\" if stage >= 4 else " ",
        "ll": "/" if stage >= 5 else " ",
        "rl": "\\" if stage >= 6 else " ",
    }
    lines = [row.format(**parts) for row in _GALLOWS]
    if sway:
        # Shift the hanging body (rows 2-4) to fake a swing.
        for i in (2, 3, 4):
            row = lines[i]
            body, post = row[:6], row[6:]
            body = (body[1:] + " ") if sway < 0 else (" " + body[:-1])
            lines[i] = body + post
    return lines


def stage_block(stage: int, dead: bool = False) -> str:
    color = STAGE_COLORS[stage]
    quote = STAGE_QUOTES[stage]
    lines = gallows(stage, dead=dead)
    out = []
    for i, line in enumerate(lines):
        extra = ""
        if i == 1:
            extra = "   " + quote[0]
        elif i == 2:
            extra = "   " + quote[1]
        out.append(f"{color}{line}{extra}{Style.RESET_ALL}")
    return "\n".join(out)


FREED_FRAMES = [
    [
        "  +---+          ",
        "  |   |          ",
        "      |    \\O/   ",
        "      |     |    ",
        "      |    / \\   ",
        "      |          ",
        "=========        ",
    ],
    [
        "  +---+          ",
        "  |   |          ",
        "      |     O    ",
        "      |    /|\\   ",
        "      |    / \\   ",
        "      |          ",
        "=========        ",
    ],
    [
        "  +---+          ",
        "  |   |          ",
        "      |    _O_   ",
        "      |     |    ",
        "      |    / >   ",
        "      |          ",
        "=========        ",
    ],
]

CONFETTI_CHARS = "*+.o•✦❋"
CONFETTI_COLORS = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA, Fore.BLUE]

KEYBOARD_ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]

TROPHY = r"""
   ___________
  '._==_==_=_.'
  .-\:      /-.
 | (|:.     |) |
  '-|:.     |-'
    \::.    /
     '::. .'
       ) (
     _.' '._
    '-------'
""".strip("\n")

SKULL = r"""
     _____
    /     \
   | () () |
    \  ^  /
     |||||
     |||||
""".strip("\n")
