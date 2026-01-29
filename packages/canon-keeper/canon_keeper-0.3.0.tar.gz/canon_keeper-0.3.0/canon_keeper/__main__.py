"""
Entry point for running as a module.

Usage:
    python -m canon_keeper install       # Run installer
    python -m canon_keeper --help        # Show help
"""
import sys


def main():
    # Always run installer (that's all this package does now)
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
    
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print("""
Canon Keeper - Copilot Memory Persistence

Usage:
    python -m canon_keeper install       Install/configure for a workspace
    python -m canon_keeper               Same as 'install'
    
Options:
    --workspace, -w PATH    Path to workspace root (auto-detected if not specified)
    --force, -f             Force overwrite existing copilot-instructions.md

Examples:
    python -m canon_keeper install
    python -m canon_keeper install --workspace /path/to/project
    python -m canon_keeper --force
""")
        return 0
    
    from .install import main as install_main
    return install_main()


if __name__ == "__main__":
    sys.exit(main())