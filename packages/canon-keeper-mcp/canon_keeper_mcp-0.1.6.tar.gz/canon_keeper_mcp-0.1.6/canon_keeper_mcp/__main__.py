"""
Entry point for running as a module.

Usage:
    python -m canon_keeper_mcp           # Run MCP server
    python -m canon_keeper_mcp install   # Run installer
    python -m canon_keeper_mcp --help    # Show help
"""
import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        # Remove 'install' from argv so argparse in install.py works correctly
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from .install import main as install_main
        return install_main()
    elif len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print("""
Canon Keeper MCP Server

Usage:
    python -m canon_keeper_mcp           Run the MCP server (for VS Code)
    python -m canon_keeper_mcp install   Install and configure for a workspace
    
Install Options:
    --workspace, -w PATH    Path to workspace root (auto-detected if not specified)
    --force, -f             Force overwrite existing copilot-instructions.md
    --skip-deps             Skip installing Python dependencies

Examples:
    python -m canon_keeper_mcp install
    python -m canon_keeper_mcp install --workspace /path/to/project
    python -m canon_keeper_mcp install --force
""")
        return 0
    else:
        # Run the MCP server
        import asyncio
        from .server import main as server_main

        asyncio.run(server_main())
        return 0


if __name__ == "__main__":
    sys.exit(main())