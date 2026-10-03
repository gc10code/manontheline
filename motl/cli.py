"""Command line entry point."""

import argparse
import random
import sys
from typing import List, Optional

import colorama

from . import __version__
from .game import App, PLAY_MODES
from .paths import custom_words_dir, resource_path, save_path
from .storage import Profile
from .ui import Terminal
from .words import DIFFICULTIES, load_words


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="manontheline",
        description="Man On The Line - the sarcastic hangman game.",
    )
    parser.add_argument("--difficulty", choices=DIFFICULTIES, help="default difficulty")
    parser.add_argument(
        "--mode",
        choices=list(PLAY_MODES) + ["daily", "versus"],
        help="jump straight into a game mode",
    )
    parser.add_argument("--words", metavar="DIR", help="extra folder with easy.txt / medium.txt / hard.txt word lists")
    parser.add_argument("--no-anim", action="store_true", help="disable animations")
    parser.add_argument("--no-save", action="store_true", help="don't read or write the save file")
    parser.add_argument("--seed", type=int, help="random seed (for reproducible games)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def setup_console() -> None:
    # Emojis and box drawing need UTF-8; Windows consoles default to a legacy code page.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    fix = getattr(colorama, "just_fix_windows_console", None)
    if fix:
        fix()
    else:
        colorama.init()


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    setup_console()

    profile = Profile(None if args.no_save else save_path())
    if args.difficulty:
        profile.settings["difficulty"] = args.difficulty

    lists = load_words(resource_path("words"), custom_words_dir(), args.words or "")
    if not any(lists.values()):
        print("No word lists found. Put easy.txt / medium.txt / hard.txt in the 'words' folder.", file=sys.stderr)
        return 1

    if args.seed is not None:
        random.seed(args.seed)
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    term = Terminal()
    term.force_no_anim = args.no_anim
    App(profile, lists, term, rng).run(start_mode=args.mode)
    return 0
