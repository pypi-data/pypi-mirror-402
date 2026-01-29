# 💫 Delulify

**"Turns your runtime errors into emotionally supportive debugging hints."** 💅

Delulify is a Python CLI wrapper that intercepts your script's crashes. Instead of an ugly, cryptic traceback, it gives you a genuinely useful hint paired with an emotionally unhinged affirmation.

Because sometimes the stack trace hurts more than the bug itself.

---

## ✨ Features

- **🛡️ Crash Interception** – Hides the scary wall of text and shows you exactly where it broke.
- **🧠 Smart Hints** – Translates Python errors into human language.  
  *Example:* `IndexError` → "You tried to grab item 10 from a list of 3."
- **🎭 Three Vibes**
  - `gentle` – Soft, therapy-speak. *"You are valid."*
  - `roast` – Brutal honesty. *"You shadowed your own variable. Embarrassing."*
  - `chaotic` – Gen Z brainrot. *"The compiler is gaslighting you."*

---

## 📦 Installation

Clone the repository and install it in editable mode:
```bash
git clone https://github.com/YOUR_USERNAME/delulify.git
cd delulify
pip install -e .
```

---

## 🚀 Usage

Simply put `delulify` before your normal Python command.

### Basic Run (Default Gentle Mode):
```bash
delulify my_script.py
```

### Choose Your Vibe:
```bash
delulify my_script.py --mode=roast
delulify my_script.py --mode=chaotic
```

---

## 📸 Example Output

**Input:**

`buggy.py`
```python
print(10 / 0)
```

**Output:**
```
( x _ x ) Ouch! The script died.

--- SHORT TRACE ---
File "buggy.py", line 1, in <module>
  print(10 / 0)

WHAT: ZeroDivisionError
WHY: You cannot divide a number by zero. It breaks the laws of physics.
VIBE: DIVIDING BY ZERO? IN THIS ECONOMY?? 📉
```

---

## 🛠 Supported Errors

Delulify currently has unique personalities for:

- `ZeroDivisionError`
- `IndexError`
- `KeyError`
- `NameError`
- `SyntaxError`
- `IndentationError`
- `TypeError`
- `ModuleNotFoundError`
- `KeyboardInterrupt` (Ctrl + C)

---

## 🤝 Contributing

Got a funnier roast? Found a new error type?

**Open a Pull Request.** We accept all chaos.

---

## 🧠 Philosophy

Bugs are inevitable. Stack traces are hostile. Developers deserve emotional support.

**Debug responsibly. Stay delulu.** ✨