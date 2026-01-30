"""
MBM Package Entry Point

This allows running MBM as a module:
    python -m mbm

This always works regardless of PATH configuration.
"""

from mbm.cli.main import main

if __name__ == "__main__":
    main()
