import traceback
from types import TracebackType
from typing import Type, Optional
from .vibes import VIBES

GRAY = "\033[90m"
RED = "\033[91m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

def print_exception_with_vibes(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback: Optional[TracebackType],
    mode: str
) -> None:
    """
    Prints a custom, aesthetic trace based on the intercepted exception.
    """
    

    if exc_traceback:
        tb_lines = traceback.format_tb(exc_traceback)
        short_tb = ''.join(tb_lines[-2:]) # Only show last 2 steps
    else:
        short_tb = "  (No traceback available)"

    error_name = exc_type.__name__

    error_data = VIBES.get(error_name, VIBES["DEFAULT"])
    
    hint = error_data["hint"]
    quote = error_data["quotes"].get(mode, error_data["quotes"]["gentle"])

    print(f"\n{RED}( x _ x ) Ouch! The script died.{RESET}")
    
    print(f"\n{GRAY}--- SHORT TRACE ---{RESET}")
    print(f"{YELLOW}{short_tb.strip()}{RESET}")
    print(f"{GRAY}-------------------{RESET}\n")

    print(f"{RED}WHAT: {error_name}{RESET}")
    print(f"{CYAN}WHY:  {hint}{RESET}")
    print(f"{MAGENTA}VIBE: {quote}{RESET}\n")