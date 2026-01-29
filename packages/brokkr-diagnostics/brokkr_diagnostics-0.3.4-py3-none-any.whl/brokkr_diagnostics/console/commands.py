"""Command definitions and execution"""

import asyncio
import os
from termcolor import cprint

from brokkr_diagnostics.nvidia import (
    run_driver_diagnostics,
    run_gpu_hardware_diagnostics,
    run_cuda_diagnostics,
    run_gpu_reset,
)
from brokkr_diagnostics.pcie import run_lspci_diagnostics
from brokkr_diagnostics.kernel import (
    run_nvidia_services_diagnostics,
    run_kernel_logs_diagnostics,
    run_proc_diagnostics,
)

from brokkr_diagnostics.infiniband import run_ib_diagnostics
from brokkr_diagnostics.confidential_compute import toggle_cc_mode
from brokkr_diagnostics.runner import run_diagnostics
from .ui import print_help


# Command registry - add/remove commands here
COMMANDS = {
    "driver": {
        "func": run_driver_diagnostics,
        "async": True,
        "description": "NVIDIA driver version & installation checks",
    },
    "gpu": {
        "func": run_gpu_hardware_diagnostics,
        "async": True,
        "description": "GPU hardware state & identification",
    },
    "lspci": {
        "func": run_lspci_diagnostics,
        "async": True,
        "description": "PCIe bus topology & link status",
        "aliases": ["pcie"],
    },
    "services": {
        "func": run_nvidia_services_diagnostics,
        "async": True,
        "description": "SystemD service status",
    },
    "kernel": {
        "func": run_kernel_logs_diagnostics,
        "async": True,
        "description": "Kernel messages & error detection",
        "aliases": ["logs"],
    },
    "system": {
        "func": run_proc_diagnostics,
        "async": True,
        "description": "System information (/proc files, NUMA)",
        "aliases": ["proc"],
    },
    "ib": {
        "func": run_ib_diagnostics,
        "async": True,
        "description": "InfiniBand diagnostics",
    },
    "cuda": {
        "func": run_cuda_diagnostics,
        "async": True,
        "description": "CUDA diagnostics",
        "aliases": ["cuda-tests"],
    },
    "reset": {
        "func": run_gpu_reset,
        "async": True,
        "description": "Reset all GPUs",
        "requires_root": True,
    },
    "help": {
        "func": print_help,
        "async": False,
        "description": "Show help message",
        "aliases": ["h", "?"],
    },
    "clear": {
        "func": lambda: os.system('clear'),
        "async": False,
        "description": "Clear screen",
    },
    "json": {
        "func": run_diagnostics,
        "async": True,
        "description": "Run all diagnostics and output JSON",
    },
}


def run_all_diagnostics():
    """Run all diagnostic modules"""
    cprint("\n" + "=" * 80, "cyan")
    cprint("RUNNING ALL DIAGNOSTICS", "cyan", attrs=["bold"])
    cprint("=" * 80 + "\n", "cyan")
    
    diagnostics = [
        ("Driver Version & Installation", run_driver_diagnostics),
        ("PCIe Bus & Hardware", run_lspci_diagnostics),
        ("GPU Hardware State", run_gpu_hardware_diagnostics),
        ("System Information", run_proc_diagnostics),
        ("NVIDIA Services", run_nvidia_services_diagnostics),
        ("Kernel Messages", run_kernel_logs_diagnostics),
        ("InfiniBand", run_ib_diagnostics),
        ("CUDA", run_cuda_diagnostics),
    ]
    
    for name, func in diagnostics:
        cprint(f"\n{'=' * 80}", "cyan")
        cprint(f"Running: {name}", "yellow", attrs=["bold"])
        cprint("=" * 80, "cyan")
        try:
            asyncio.run(func())
        except Exception as e:
            cprint(f"\nERROR running {name}: {e}", "red", attrs=["bold"])
        cprint("\n", "white")


def handle_cc_command(mode: str) -> int:
    """Handle CC mode toggle command"""
    if os.geteuid() != 0:
        cprint("Error: cc command requires root", "red")
        return 1
    
    mode = mode.lower()
    if mode in ["on", "off"]:
        toggle_cc_mode(mode)
        return 0
    else:
        cprint(f"Invalid CC mode: '{mode}'. Valid modes: on, off", "red")
        return 1


def resolve_command(cmd: str) -> str | None:
    """Resolve command name including aliases"""
    if cmd in COMMANDS:
        return cmd
    
    for name, config in COMMANDS.items():
        if cmd in config.get("aliases", []):
            return name
    
    return None


def run_command(cmd: str, file: str = "/tmp/diagnostics.json") -> int:
    """Run a single command non-interactively"""
    cmd = cmd.strip().lower()
    
    # Handle CC command specially (has argument)
    if cmd.startswith("cc "):
        parts = cmd.split()
        if len(parts) == 2:
            return handle_cc_command(parts[1])
        else:
            cprint("Usage: cc <mode>", "red")
            return 1
    
    # Handle "all" specially
    if cmd == "all":
        run_all_diagnostics()
        return 0
    
    # Handle "json" specially - saves to file
    if cmd == "json":
        asyncio.run(run_diagnostics())
        return 0
    
    # Resolve command
    resolved = resolve_command(cmd)
    if not resolved:
        cprint(f"Unknown command: '{cmd}'", "red")
        return 1
    
    config = COMMANDS[resolved]
    
    # Check root requirement
    if config.get("requires_root") and os.geteuid() != 0:
        cprint(f"Error: '{cmd}' requires root", "red")
        return 1
    
    # Execute
    try:
        if config["async"]:
            asyncio.run(config["func"]())
        else:
            config["func"]()
        return 0
    except Exception as e:
        cprint(f"Error running '{cmd}': {e}", "red")
        return 1
