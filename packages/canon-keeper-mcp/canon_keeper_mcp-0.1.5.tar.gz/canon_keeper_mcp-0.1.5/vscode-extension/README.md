# Canon Keeper MCP Helper

This VS Code extension auto-registers the canon-keeper MCP server for each workspace, then prompts to reload.

## What it does
- On activation, ensures `.vscode/mcp.json` exists for every workspace folder.
- Adds/updates the `canon-keeper` entry:
  - command: `${workspaceFolder}/.venv/Scripts/python.exe`
  - args: `-m`, `canon_keeper_mcp`
  - cwd: `${workspaceFolder}`
- Prompts to reload the window so Copilot picks up the MCP server.

## Usage
Install the extension, open your workspace, and accept the reload prompt.
