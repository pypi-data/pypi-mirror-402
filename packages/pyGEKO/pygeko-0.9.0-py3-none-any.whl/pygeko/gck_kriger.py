"""Customized Python REPL for pyGEKO-Kriger"""

import code
import os
import readline
import rlcompleter
import runpy
import sys

from pygeko.__about__ import __version__ as VERSION
from pygeko.gplot import Gplot  # noqa: F401
from pygeko.kdata import Kdata  # noqa: F401
from pygeko.kgrid import Kgrid  # noqa: F401
from pygeko.utils import get_data_path  # noqa: F401

# import pygeko

message = f"""\nWelcome to pyGEKO-Kriger {VERSION}
Generalized Covariance Kriger
    
Classes Kdata, Kgrid and Gplot imported.

Use exit() or Ctrl-D (i.e. EOF) to exit.
"""

sys.ps1 = "--> "

montebea = get_data_path("montebea.csv")
msh5000 = get_data_path("msh5000.csv")


def main():
    """
    Entry point
    """
    args = sys.argv[1:]

    # Clean base context
    context = {
        "Kdata": Kdata,
        "Kgrid": Kgrid,
        "Gplot": Gplot,
        "get_data_path": get_data_path,
        "montebea": montebea,
        "msh5000": msh5000,
        "VERSION": VERSION,
        "exit": exit,
        "quit": quit,
    }

    # Case: Help
    if "--help" in args or "-h" in args:
        print(f"pyGEKO-Kriger {VERSION} - Command Line Interface")
        print("\nUsage:")
        print("  pygeko                 Launch interactive REPL")
        print("  pygeko <script.py>     Execute a script")
        print("  pygeko -i <script.py>  Execute a script and stay in interactive mode")
        print(
            "  pygeko -m <module>     Run a library module (e.g., pygeko.examples.msh_tune)"
        )
        print("  pygeko --help          Show this message")
        return

    # Case 1: pygeko (pure REPL)
    if not args:
        start_interactive_repl(local_vars=context, banner=message)

    # Case 4: pygeko -m module
    elif args[0] == "-m" and len(args) > 1:
        module_name = args[1]
        sys.argv = args[1:]  # Ajustar para el módulo
        runpy.run_module(module_name, run_name="__main__", alter_sys=True)

    # Case 3: pygeko -i script.py
    elif args[0] == "-i" and len(args) > 1:
        script_path = args[1]
        if not os.path.exists(script_path):
            print(f"Error: File '{script_path}' not found.")
            sys.exit(1)

        # Adjust sys.argv so that the script sees its own arguments
        sys.argv = args[1:]
        script_globals = runpy.run_path(script_path, run_name="__main__")

        context.update(script_globals)
        start_interactive_repl(local_vars=context)

    # Case 2: pygeko script.py
    else:
        script_path = args[0]
        if not os.path.exists(script_path):
            print(f"Error: File '{script_path}' not found.")
            sys.exit(1)

        sys.argv = args[:]  # The script receives the complete list
        runpy.run_path(script_path, run_name="__main__")


def run_script(path: str):
    """
    Execute a .py file in the current context.

    :param path: path to the .py file
    :type path: str
    """
    """Ejecuta un archivo .py en el contexto actual."""
    if not os.path.exists(path):
        print(f"Error: File '{path}' not found.")
        sys.exit(1)
    # Run the script as if it were the __main__ script
    runpy.run_path(path, run_name="__main__")


def start_interactive_repl(local_vars: dict = None, banner: str = ""):
    """
    pyGEKO-Kriger interactive REPL


    :param local_vars: context variables dictionary , defaults to None
    :type local_vars: dict, optional
    :param banner: welcome banner, defaults to ""
    :type banner: str, optional
    """    
    # 1. Configure the history file
    history_file = os.path.expanduser("~/.pygeko_history")
    if os.path.exists(history_file):
        readline.read_history_file(history_file)

    # 2. Configure autocomplete with TAB
    # The completer needs to know the local variable dictionary
    readline.set_completer(rlcompleter.Completer(local_vars).complete)
    readline.parse_and_bind("tab: complete")

    # 3. Save history on exit
    import atexit

    atexit.register(readline.write_history_file, history_file)

    # 4. Launch the REPL
    code.interact(
        banner=banner,
        local=local_vars,
        exitmsg="\n--- Exiting pyGEKO-Kriger, Bye! ---\n",
    )


if __name__ == "__main__":
    """
    Entry point
    """
    main()
