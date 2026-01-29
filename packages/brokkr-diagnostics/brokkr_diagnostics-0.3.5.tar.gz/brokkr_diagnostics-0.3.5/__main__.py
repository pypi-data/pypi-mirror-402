"""
Entry point for brokkr-diagnostics binary
"""

import argparse
from brokkr_diagnostics.console import run_command, run_interactive





EPILOG = """
Commands:
  driver      NVIDIA driver version & installation checks
  gpu         GPU hardware state & identification
  lspci       PCIe bus topology & link status
  services    SystemD service status
  kernel      Kernel messages & error detection
  system      System information (/proc files, NUMA)
  ib          InfiniBand diagnostics
  cuda        CUDA diagnostics
  all         Run all diagnostics
  json        Run all diagnostics and output JSON
  reset       Reset all GPUs
  cc on       Enable Confidential Compute mode (requires root)
  cc off      Disable Confidential Compute mode (requires root)

Examples:
  brokkr-diagnostics --run json
  brokkr-diagnostics --run "cc off"
  brokkr-diagnostics --run all
  brokkr-diagnostics --run driver
"""


def main():
    parser = argparse.ArgumentParser(
        description="NVIDIA GPU Diagnostics Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG
    )
    parser.add_argument(
        "--run", "-r",
        metavar="COMMAND",
        help="Run a command non-interactively and exit"
    )
    
    args = parser.parse_args()
    
    if args.run:
        exit(run_command(args.run))
    else:
        run_interactive()



if __name__ == "__main__":
    main()

