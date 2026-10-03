"""All user-facing text. Lists mean 'pick one at random'."""

import random
from typing import Any

STRINGS = {
    # ----- title / menu -----------------------------------------------------
    "tagline": 'The "Epic" Word Game You Didn\'t Ask For!',
    "credit": "Created by: gc10code (Blame him if you hate it)",
    "version": "Version {version} - Now with 300% More Sarcasm!",
    "ask_name": "Who dares to play? Enter your name",
    "default_name": "Anonymous Loser",
    "welcome_back": "Oh no, {name} is back. Rank: {rank}",
    "menu_title": "MAIN MENU",
    "menu": {
        "classic": "Classic          — the original suffering",
        "time": "Time Attack      — suffer, but faster",
        "sudden": "Sudden Death     — one mistake and you're done (x3 points)",
        "marathon": "Marathon         — lives carry over, how far can you go?",
        "daily": "Daily Challenge  — same word for everyone, once a day",
        "versus": "Versus           — ruin a friendship, 2 players",
        "stats": "Statistics       — numbers that prove you're mediocre",
        "achievements": "Achievements     — trophies for participation",
        "leaderboard": "Hall of Fame     — local high scores",
        "settings": "Settings",
        "help": "How to Play",
        "quit": "Quit             — the smartest move so far",
    },
    "menu_prompt": "Pick a number",
    "menu_invalid": "That's not on the menu. Reading is hard, I know.",
    "konami": "🌈 KONAMI CODE! Rainbow mode {state}. +30 lives? No. Just colors.",
    "on": "ON",
    "off": "OFF",
    "press_enter": "Press ENTER to continue...",
    "select_difficulty": "Choose a difficulty, not that it'll make you better. (ENTER = default)",
    "difficulty_names": {"easy": "Easy", "medium": "Medium", "hard": "Hard"},
    "no_words": "No words found for '{diff}'. Even the dictionary gave up on you.",
    "mode_names": {
        "classic": "Classic",
        "time": "Time Attack",
        "sudden": "Sudden Death",
        "marathon": "Marathon",
        "daily": "Daily Challenge",
        "versus": "Versus",
    },
    # ----- in-game HUD ------------------------------------------------------
    "word": "The Unreachable Word",
    "guessed_letters": "Your Gallery of Shame",
    "remaining_attempts": "Attempts Until I Can Laugh at Your Loss",
    "score": "Score",
    "streak": "Streak",
    "combo": "Combo",
    "time_left": "Time left",
    "hints_left": "Hints",
    "word_n": "Word #{n}",
    "controls": "[letter] guess  ·  [whole word] go for glory  ·  ! hint  ·  ? help  ·  :q give up",
    "enter_guess": "Go on, impress me with your *brilliant* guess",
    "single_letter": "Wow, slow down there, Einstein. ONE letter, not a full dissertation. 🙄",
    "valid_letter": "Seriously? Letters only. Not hieroglyphs, Morse code, or whatever that was.",
    "already_guessed": "You really enjoy making the same mistake twice, huh?",
    "good_guess": [
        "Shockingly correct. Is it beginner's luck?",
        "A blind squirrel finds a nut sometimes. ✨",
        "Don't get too cocky, that was a fluke.",
        "Oh, a correct guess? I must be dreaming.",
        "Correct. Mark the calendar. 📆",
        "Fine. That one's in there. Happy now?",
    ],
    "wrong_guess": [
        "Wow. Just… wow. Try harder. No, really.",
        "It's wrong, but thanks for the entertainment.",
        "A failure so spectacular, it deserves a trophy. 🏆",
        "Nope. The rope thanks you for your cooperation. 🪢",
        "Incorrect. I'd say 'nice try' but I don't lie.",
    ],
    "encouragement": [
        "Sure, keep guessing! The comedy show is free. 🎭",
        "You're giving it your best shot… which is sad, really.",
        "Victory is so close! Just kidding, it's miles away. 🏆",
    ],
    "combo_msg": "🔥 COMBO x{n}! Points x{mult}",
    "multi_hit": "{n} of them! Greedy. +{points}",
    "hit_points": "+{points}",
    "confirm_word": "Guessing the whole word '{guess}'. Wrong costs {n} lives. Sure? (Y/N)",
    "word_right": "WHAT. You actually knew it?! 🤯",
    "word_wrong": "Bold. Wrong, but bold. -{n} lives. 💸",
    "hint_given": "Fine, here's a freebie: '{letter}'. -{cost} points for your pride. 🕯️",
    "no_hint": "No hints left. You're on your own, champ.",
    "confirm_surrender": "Give up? The man will hang and it's on you. (Y/N)",
    "time_up": "⏰ TIME'S UP! Even the clock got bored of you.",
    "help_text": (
        "Type one letter to guess it. Type the WHOLE word (same length) to go for glory: "
        "right = bonus points, wrong = -2 lives.\n"
        "  !  = hint (reveals a letter, costs points, max 2 per word)\n"
        "  ?  = this help      :q = give up\n"
        "Consecutive correct letters build a COMBO multiplier (up to x3)."
    ),
    # ----- end of round -----------------------------------------------------
    "you_lost": "Game Over! The word was",
    "you_won": "You won? Did the universe glitch?",
    "breakdown": {
        "letters": "Letters",
        "win": "Survival bonus",
        "time": "Speed bonus",
        "lives": "Remaining lives bonus",
        "flawless": "Flawless bonus",
        "multiplier": "Multiplier",
        "total": "Round total",
    },
    "session_score": "📈 Session score: {score} | Streak: {streak}🔥",
    "play_again": "Feeling masochistic enough for another round? (Y/N)",
    "thanks": "Thanks for playing! You've been… well, let's not lie. Mediocre at best.",
    "final_score": "🏆 Final Score: {score} | Best Streak this session: {streak}🔥",
    "new_record": "🎖️  NEW HALL OF FAME ENTRY: #{rank} in {mode}! Frame it.",
    "achievement_unlocked": "🏅 ACHIEVEMENT UNLOCKED",
    "marathon_life": "❤️ +1 life for surviving. Don't waste it.",
    "marathon_over": "🏁 Marathon over! You survived {n} words.",
    "time_attack_info": "⏱️  You have {secs} seconds per word. Tick tock.",
    "sudden_info": "💀 One life. One mistake. No pressure.",
    # ----- daily ------------------------------------------------------------
    "daily_intro": "📅 Daily Challenge for {date}. Everyone gets the same word. One shot.",
    "daily_done": "You already played today's challenge. Patience is a virtue (look it up).",
    "daily_next": "Next challenge in {h}h {m}m.",
    "daily_share": "Copy & brag:",
    "daily_streak": "Daily streak: {n} 🔥",
    # ----- versus -----------------------------------------------------------
    "versus_intro": "🤝 VERSUS: one picks the word, the other guesses. Then swap. Friendships may end.",
    "versus_player": "Name of player {n}",
    "versus_rounds": "How many rounds each? (1-10)",
    "versus_secret": "{setter}, type the secret word (hidden, {guesser} look away!)",
    "versus_secret_invalid": "Letters and spaces only, at least 2 letters. Try again, mastermind.",
    "versus_secret_again": "Type it again to confirm",
    "versus_secret_mismatch": "They don't match. Can't even agree with yourself?",
    "versus_your_turn": "{name}, your turn to guess! The word was chosen by {setter}.",
    "versus_score": "Scoreboard",
    "versus_winner": "🏆 {name} wins! {loser}, you may now sulk.",
    "versus_tie": "🤝 A tie. Equally mediocre. How touching.",
    # ----- stats / achievements / leaderboard -------------------------------
    "stats_title": "STATISTICS OF SHAME",
    "stats": {
        "rank": "Rank",
        "played": "Games played",
        "won": "Won",
        "lost": "Lost",
        "win_rate": "Win rate",
        "best_streak": "Best streak",
        "current_streak": "Current streak",
        "total_score": "Total points",
        "best_session": "Best session",
        "fastest_win": "Fastest win",
        "max_combo": "Best combo",
        "hints_used": "Hints begged",
        "word_guesses_right": "Whole-word guesses",
        "time_played": "Time wasted",
        "fav_letter": "Favorite letter",
        "marathon_best": "Longest marathon",
        "daily_streak": "Daily streak",
        "histogram": "Mistakes on winning games",
    },
    "never": "never",
    "achievements_title": "ACHIEVEMENTS",
    "locked": "???",
    "unlocked_count": "{n}/{total} unlocked",
    "leaderboard_title": "HALL OF FAME",
    "leaderboard_empty": "Empty. Like your trophy cabinet.",
    "leaderboard_pick": "Which mode? (ENTER = all)",
    "all_modes": "All",
    # ----- settings ---------------------------------------------------------
    "settings_title": "SETTINGS",
    "settings": {
        "difficulty": "Default difficulty",
        "animations": "Animations",
        "sound": "Sound (terminal bell)",
        "rainbow": "Rainbow mode",
        "name": "Player name",
        "reset": "Reset all stats",
        "back": "Back",
    },
    "reset_confirm": "Type RESET to erase stats, achievements and scores forever",
    "reset_done": "Wiped. A fresh start for a familiar failure.",
    "reset_cancel": "Cancelled. Your shame is preserved.",
    "save_failed": "⚠️  Couldn't save your progress (disk said no).",
    "save_broken": "⚠️  Your save file was corrupted and has been moved aside as save.json.broken. Starting fresh.",
    # ----- misc -------------------------------------------------------------
    "how_to_play": [
        "Guess the hidden word one letter at a time before the man is fully drawn.",
        "Each wrong letter adds a body part. 6 mistakes and it's over.",
        "Type the whole word to solve it instantly (wrong = -2 lives).",
        "'!' gives a hint for points, '?' shows controls, ':q' surrenders.",
        "Correct letters in a row build a combo multiplier up to x3.",
        "Harder difficulty = bigger multiplier (x1 / x1.5 / x2).",
        "Add your own words: put easy.txt / medium.txt / hard.txt in {folder}",
        "There are secret commands. No, I won't tell you.",
    ],
    "goodbye_interrupt": "Rage quit detected. Coward. 👋",
    "easter": {
        "XYZZY": "Nothing happens.",
        "SUDO": "Nice try. This incident will be reported. 🚨",
        "IDDQD": "God mode is disabled in this universe. -1 dignity.",
        "HESOYAM": "Wrong game, but I respect the hustle. 💸",
        "42": "Yes, that's the answer. But what was the question? 🌌",
        "HELP": "Nobody can help you now. (Try '?')",
        "PLEASE": "Begging won't work. ...OK, it worked once. Not this time.",
        "HANGMAN": "Hey! I prefer 'Man On The Line'. Show some respect.",
    },
    "ranks": [
        (0, "Clueless Rookie"),
        (1000, "Lucky Guesser"),
        (5000, "Word Botherer"),
        (15000, "Letter Lord"),
        (40000, "Vocabulary Overlord"),
        (100000, "The Hangman's Nightmare"),
    ],
    "yes": ("Y", "YES"),
}


def t(key: str, **fmt: Any) -> Any:
    """Look up a string; lists of strings pick a random entry; str values get .format(**fmt)."""
    value = STRINGS[key]
    if isinstance(value, list) and value and isinstance(value[0], str):
        value = random.choice(value)
    if isinstance(value, str) and fmt:
        value = value.format(**fmt)
    return value


def raw(key: str) -> Any:
    """Look up a value without random picking or formatting."""
    return STRINGS[key]


def rank_for(total_score: int) -> str:
    title = STRINGS["ranks"][0][1]
    for threshold, name in STRINGS["ranks"]:
        if total_score >= threshold:
            title = name
    return title
