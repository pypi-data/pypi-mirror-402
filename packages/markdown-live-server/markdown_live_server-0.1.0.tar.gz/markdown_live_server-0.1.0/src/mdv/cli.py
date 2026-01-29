#!/usr/bin/env python3
"""CLI entry point for mdv"""

import sys
import subprocess
import os


def main():
    """Main entry point for the mdv command."""
    # CLI mode: if a file is passed, render to terminal with ANSI formatting
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        # Check if first arg is a file (not a flag like -p or -a)
        if not filepath.startswith('-') and os.path.isfile(filepath):
            result = subprocess.run(
                ["pandoc", "-t", "ansi", "--wrap=auto", filepath]
            )
            sys.exit(result.returncode)

    # Server mode: pass all arguments to the server
    from mdv.server import main as server_main
    server_main()


if __name__ == "__main__":
    main()
