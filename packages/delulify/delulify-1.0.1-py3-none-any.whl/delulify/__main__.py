import sys
import os
import runpy
from .interceptor import setup_exception_hookfrom .ui import print_header 

def main() -> None:
    """
    Main entry point for the `delulify` CLI.
    Checks arguments, sets up the runtime, and executes the target script.
    """
    
    # 1. Check if user provided args
    if len(sys.argv) < 2:
        print(
            "\n( o ‿ o ) Usage: delulify <script.py> [--mode=gentle|roast|chaotic]\n"
            "          Example: delulify my_script.py --mode=roast\n"
        )
        sys.exit(0)

    mode = "gentle"
    script_args = []
    
    for arg in sys.argv[1:]:
        if arg.startswith("--mode="):
            mode = arg.split("=", 1)[1]
        else:
            script_args.append(arg)

    if not script_args:
        print("Error: Please provide a script filename to run.")
        sys.exit(1)

    script_filename = script_args[0]
    
    if not os.path.exists(script_filename):
        print(f"Error: The file '{script_filename}' was not found.")
        sys.exit(1)

    print(f"( o ‿ o ) Delulify is watching... [Mode: {mode}]")
    print("-" * 50)

    setup_exception_hook(mode)

    sys.argv = script_args 

    try:
        runpy.run_path(script_filename, run_name="__main__")
    except KeyboardInterrupt:
        print("\n( - _ - ) Bye!")
        sys.exit(0)
    except Exception:

        sys.excepthook(*sys.exc_info())

if __name__ == "__main__":
    main()