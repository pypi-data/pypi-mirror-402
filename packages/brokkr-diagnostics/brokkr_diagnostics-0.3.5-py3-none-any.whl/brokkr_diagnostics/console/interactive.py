"""Interactive REPL mode"""

import os
from termcolor import cprint
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

from .commands import COMMANDS, run_command, handle_cc_command, run_all_diagnostics
from .ui import print_banner, print_help


def get_all_commands() -> list:
    """Get list of all commands including aliases"""
    commands = []
    for name, config in COMMANDS.items():
        commands.append(name)
        commands.extend(config.get("aliases", []))
    
    # Add special commands
    commands.extend(['all', 'cc on', 'cc off', 'quit', 'exit', 'q'])
    return commands


def run_interactive():
    """Run interactive REPL mode"""
    print_banner()
    print_help()
    
    commands = get_all_commands()
    completer = WordCompleter(commands, ignore_case=True, sentence=True)
    
    style = Style.from_dict({
        'prompt': '#00aa00 bold',
    })
    
    session = PromptSession(
        completer=completer,
        style=style,
        complete_while_typing=True,
    )
    
    while True:
        try:
            choice = session.prompt(
                HTML('<prompt>brokkr-diagnostics> </prompt>')
            ).strip().lower()
            
            if not choice:
                continue
            
            # Quit commands
            if choice in ["quit", "exit", "q"]:
                cprint("\nExiting Brokkr Host Manager Diagnostics...", "red")
                break
            
            # CC command with argument
            if choice.startswith("cc "):
                if os.geteuid() != 0:
                    cprint("\nPlease run as root", "red")
                    continue
                parts = choice.split()
                if len(parts) == 2:
                    handle_cc_command(parts[1])
                else:
                    cprint("\nUsage: cc <mode>", "red")
                    cprint("Example: cc on", "yellow")
                continue
            
            # All diagnostics
            if choice == "all":
                run_all_diagnostics()
                continue
            
            # Run command
            run_command(choice)
            
        except KeyboardInterrupt:
            cprint("\n\nExiting Brokkr Host Manager Diagnostics...", "red")
            break
        except EOFError:
            cprint("\n\nExiting Brokkr Host Manager Diagnostics...", "red")
            break
