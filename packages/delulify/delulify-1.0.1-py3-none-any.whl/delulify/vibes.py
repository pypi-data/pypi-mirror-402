# delulify/vibes.py

VIBES = {
    "ZeroDivisionError": {
        "hint": "You cannot divide a number by zero. It breaks the laws of physics and Python.",
        "quotes": {
            "gentle": "Math is hard, but you are soft. 🌸 Maybe check if your denominator is 0?",
            "roast": "Dividing by zero? Go back to 3rd grade math. 💀",
            "chaotic": "DIVIDING BY ZERO? IN THIS ECONOMY?? 📉",
        },
    },
    "IndexError": {
        "hint": "You tried to access an item in a list that doesn't exist. (e.g., asking for item 10 in a list of 3).",
        "quotes": {
            "gentle": "It’s okay to reach for the stars, but maybe stick to the length of the list for now. 🌟",
            "roast": "The list has 3 items and you asked for index 50. The math ain't mathing.",
            "chaotic": "You had the audacity to access index #DOES_NOT_EXIST. Bold. 💅",
        },
    },
    "KeyError": {
        "hint": "You tried to look up a key in a dictionary that isn't there. Check your spelling or case sensitivity!",
        "quotes": {
            "gentle": "That key isn't in the dictionary, but it's in our hearts. 💖",
            "roast": "You're looking for something that doesn't exist. Like your bug-free code.",
            "chaotic": "Dictionary says: 'New phone, who dis?' 📱",
        },
    },
    "NameError": {
        "hint": "You used a variable or function name that Python doesn't recognize. Did you make a typo?",
        "quotes": {
            "gentle": "We all forget names sometimes. Did you define it earlier? 🏷️",
            "roast": "Who is that? I don't know her. Learn to spell your variables.",
            "chaotic": "Is this variable gaslighting you? It claims it doesn't exist. 🕯️",
        },
    },
    "SyntaxError": {
        "hint": "You broke the grammar rules of Python. Check for missing colons (:), unmatched parentheses, or typos.",
        "quotes": {
            "gentle": "Words are hard! Take a deep breath and check your brackets. 🧘",
            "roast": "I literally can't run this. It's not even code. It's a cry for help.",
            "chaotic": "Bestie, the compiler is fighting for its life right now. 😭",
        },
    },
    "IndentationError": {
        "hint": "Python relies on consistent spacing. You likely mixed tabs and spaces, or your blocks aren't aligned.",
        "quotes": {
            "gentle": "Everything needs to be aligned to flow. Just like your chakras. ☁️",
            "roast": "Your code looks like a jagged staircase. Use a linter, I beg you.",
            "chaotic": "The Tab vs Space war just claimed another victim (you). ⚔️",
        },
    },
    "TypeError": {
        "hint": "You tried to combine incompatible data types (like adding a Text string to a Number).",
        "quotes": {
            "gentle": "These two types just aren't compatible. Like oil and water. 💧",
            "roast": "You can't add 'Apple' to '5'. This isn't JavaScript.",
            "chaotic": "Type Safety is a myth, but this crash is very real. 💥",
        },
    },
    "ModuleNotFoundError": {
        "hint": "You tried to import a library that isn't installed. Try running 'pip install <package_name>'.",
        "quotes": {
            "gentle": "The library is missing. Maybe it just needs an invitation? (pip install) 💌",
            "roast": "You forgot to install the package. Classic. absolute novice behavior.",
            "chaotic": "404: Library not found. Have you tried manifesting it? ✨",
        },
    },
    "KeyboardInterrupt": {
        "hint": "You stopped the program manually (Ctrl+C).",
        "quotes": {
            "gentle": "Okay, we're taking a break. Rest is productive too! ☕",
            "roast": "Rage quitting? I saw that.",
            "chaotic": "YOU KILLED ME! MOTHER!! 💀",
        },
    },
    "DEFAULT": {
        "hint": "An unknown error occurred. Check the traceback above for details.",
        "quotes": {
            "gentle": "Mistakes happen. You're still a fantastic programmer! ✨",
            "roast": "You broke it. You actually broke it completely.",
            "chaotic": "Entropy increases. The code rots. Chaos reigns. 🌀",
        },
    },
}