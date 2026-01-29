#!/usr/bin/env python3
"""
Canon Keeper MCP Server Installer

Installs the MCP server and configures copilot-instructions.md with:
- Memory Persistence Protocol (@History directive)
- Best practices template
- Session Learnings Log table

Usage:
    python -m canon_keeper_mcp.install [--workspace /path/to/workspace]
    
Or run directly:
    python install.py [--workspace /path/to/workspace]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================

MCP_SCHEMA = "http://json-schema.org/draft-07/schema#"

MCP_SERVER_CONFIG = {
    "command": "${workspaceFolder}/.venv/Scripts/python.exe",
    "args": ["-m", "canon_keeper_mcp"],
    "cwd": "${workspaceFolder}"
}

MEMORY_PROTOCOL_DIRECTIVE = '''
### Memory Persistence Protocol (@History) - CRITICAL
**Rule:** When the user includes `@History`, `save this`, `remember this`, or `add to memory` in any message:

1. **Gather Context:**
   - Read the current `copilot-instructions.md` file content
   - Collect the full conversation history from this session (all messages exchanged)

2. **Call MCP Tool:**
   - Invoke `canon_keeper.extract_and_save_learnings` with:
     - `conversation`: The complete conversation text (format each turn as "User: ... \\n Assistant: ...")
     - `current_instructions`: The full content of `.github/copilot-instructions.md`

3. **Process Response:**
   - The tool returns: `{ new_learnings: [...], duplicates_skipped: [...], markdown_to_append: "..." }`
   - If `markdown_to_append` is non-empty, append it to the Session Learnings Log table

4. **Report to User:**
   - Confirm what was saved: "✅ Saved X new learning(s)"
   - Report what was skipped: "⏭️ Skipped Y duplicate(s): [topic names]"
   - If nothing new: "No new learnings detected in this conversation."

**Trigger Phrases:** `@History`, `save this`, `remember this`, `add to memory`, `save learning`, `persist this`

**Example:**
```
User: @History save what we learned
Copilot: [reads copilot-instructions.md]
         [calls canon_keeper.extract_and_save_learnings]
         ✅ Saved 2 new learning(s):
           - MCP Memory Architecture: MCP server for learning extraction
           - Deduplication Pattern: LLM-based semantic comparison
         ⏭️ Skipped 1 duplicate: FFmpeg Stream Copy (already in log)
```
'''

BEST_PRACTICES_TEMPLATE = f'''# Copilot Instructions (Project Memory)

This file serves as persistent memory for GitHub Copilot. It is read at the start of every chat session.

## 1. Project Overview
<!-- Describe your project here -->
- **Project Name:** [Your Project]
- **Description:** [Brief description]
- **Tech Stack:** [Languages, frameworks, libraries]

## 2. Coding Standards
<!-- Define your coding conventions -->
- **Language:** [Primary language]
- **Style Guide:** [Link or description]
- **Naming Conventions:** [camelCase, snake_case, etc.]

## 3. Architecture Decisions
<!-- Document key architectural choices -->
- **Pattern:** [MVC, microservices, etc.]
- **Database:** [Type and rationale]
- **API Style:** [REST, GraphQL, etc.]

## 4. Operational Protocols
<!-- Define how Copilot should behave -->
- **Error Handling:** [Fail fast vs. graceful degradation]
- **Testing:** [Required coverage, test patterns]
- **Documentation:** [Docstring style, README requirements]

## 5. MCP Integration
<!-- MCP tools available to Copilot -->
{MEMORY_PROTOCOL_DIRECTIVE}

## 6. Session Learnings Log
This section tracks decisions and learnings that evolve over time. Copilot reads this at session start.

| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
| {datetime.now().strftime("%Y-%m-%d")} | Canon Keeper Installed | MCP-based memory persistence | Auto-extract and deduplicate learnings |

---
*This file was initialized by Canon Keeper MCP. Use `@History` to save learnings from conversations.*
'''

# ============================================================================
# Installer Functions
# ============================================================================

def find_workspace_root(start_path: Path) -> Path:
    """Find workspace root by looking for .git or .vscode folder."""
    current = start_path.resolve()
    
    while current != current.parent:
        if (current / ".git").exists() or (current / ".vscode").exists():
            return current
        current = current.parent
    
    # Fall back to start path
    return start_path.resolve()


def install_dependencies():
    """Install required Python packages."""
    print("📦 Installing dependencies...")
    
    packages = ["mcp>=1.0.0", "google-genai>=1.0.0"]
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + packages,
            check=True,
            capture_output=True,
            text=True
        )
        print("   ✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to install dependencies: {e.stderr}")
        return False


def setup_mcp_config(workspace: Path) -> bool:
    """Create or update .vscode/mcp.json with canon-keeper server."""
    print("⚙️  Configuring MCP server...")
    
    vscode_dir = workspace / ".vscode"
    mcp_file = vscode_dir / "mcp.json"
    
    # Ensure .vscode directory exists
    vscode_dir.mkdir(exist_ok=True)
    
    # Load existing config or create new
    if mcp_file.exists():
        try:
            with open(mcp_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            config = {}
    else:
        config = {}

    # Ensure base structure and schema
    if not isinstance(config, dict):
        config = {}

    if config.get("$schema") != MCP_SCHEMA:
        config["$schema"] = MCP_SCHEMA

    servers = config.get("mcpServers")
    if not isinstance(servers, dict):
        servers = {}
    config["mcpServers"] = servers

    previously_configured = "canon-keeper" in servers
    servers["canon-keeper"] = MCP_SERVER_CONFIG

    if previously_configured:
        print("   🔄 Updated Canon Keeper entry in mcp.json")
    else:
        print("   ✅ Added Canon Keeper to mcp.json")

    # Write config
    try:
        with open(mcp_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"   ❌ Failed to write mcp.json: {e}")
        return False


def setup_copilot_instructions(workspace: Path, force: bool = False) -> bool:
    """Create or update copilot-instructions.md."""
    print("📝 Setting up copilot-instructions.md...")
    
    github_dir = workspace / ".github"
    instructions_file = github_dir / "copilot-instructions.md"
    
    # Ensure .github directory exists
    github_dir.mkdir(exist_ok=True)
    
    if instructions_file.exists() and not force:
        # Check if Memory Protocol already exists
        content = instructions_file.read_text(encoding="utf-8")
        
        if "Memory Persistence Protocol" in content:
            print("   ⏭️  Memory Protocol already in copilot-instructions.md")
            return True
        
        # Check if Session Learnings Log exists
        if "Session Learnings Log" in content:
            # Add Memory Protocol before Session Learnings Log
            print("   🔄 Adding Memory Protocol to existing instructions...")
            
            # Find a good insertion point (before Session Learnings Log or at end)
            if "## Session Learnings Log" in content:
                content = content.replace(
                    "## Session Learnings Log",
                    MEMORY_PROTOCOL_DIRECTIVE + "\n\n## Session Learnings Log"
                )
            elif "### Session Learnings Log" in content:
                content = content.replace(
                    "### Session Learnings Log",
                    MEMORY_PROTOCOL_DIRECTIVE + "\n\n### Session Learnings Log"
                )
            else:
                # Append at end
                content += "\n\n" + MEMORY_PROTOCOL_DIRECTIVE
            
            instructions_file.write_text(content, encoding="utf-8")
            print("   ✅ Memory Protocol added")
            return True
        else:
            # No Session Learnings Log - ask user
            print("   ⚠️  Existing copilot-instructions.md found without Session Learnings Log")
            print("       Run with --force to replace, or manually add the Memory Protocol")
            return False
    else:
        # Create new file with best practices template
        print("   ✅ Creating copilot-instructions.md with best practices template...")
        instructions_file.write_text(BEST_PRACTICES_TEMPLATE, encoding="utf-8")
        return True


def verify_installation(workspace: Path) -> bool:
    """Verify the installation is complete."""
    print("\n🔍 Verifying installation...")
    
    checks = []
    
    # Check MCP config
    mcp_file = workspace / ".vscode" / "mcp.json"
    if mcp_file.exists():
        try:
            config = json.load(open(mcp_file, encoding="utf-8"))
            if "canon-keeper" in config.get("mcpServers", {}):
                checks.append(("MCP config", True))
            else:
                checks.append(("MCP config", False))
        except:
            checks.append(("MCP config", False))
    else:
        checks.append(("MCP config", False))
    
    # Check copilot-instructions
    instructions_file = workspace / ".github" / "copilot-instructions.md"
    if instructions_file.exists():
        content = instructions_file.read_text(encoding="utf-8")
        if "Memory Persistence Protocol" in content or "@History" in content:
            checks.append(("Memory Protocol", True))
        else:
            checks.append(("Memory Protocol", False))
        
        if "Session Learnings Log" in content:
            checks.append(("Learnings Log", True))
        else:
            checks.append(("Learnings Log", False))
    else:
        checks.append(("Memory Protocol", False))
        checks.append(("Learnings Log", False))
    
    # Check MCP server can import
    try:
        subprocess.run(
            [sys.executable, "-c", "from canon_keeper_mcp.server import server"],
            check=True,
            capture_output=True,
            cwd=str(workspace)
        )
        checks.append(("MCP Server", True))
    except:
        checks.append(("MCP Server", False))
    
    # Print results
    all_passed = True
    for name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
        if not passed:
            all_passed = False
    
    return all_passed


# ============================================================================
# Post-Installation Page
# ============================================================================

COMPLETION_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canon Keeper MCP - Installation Complete</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 40px 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .header h1 {
            font-size: 2.5rem;
            color: #4ade80;
            margin-bottom: 10px;
        }
        .header .subtitle {
            font-size: 1.2rem;
            color: #94a3b8;
        }
        .success-badge {
            display: inline-block;
            background: #166534;
            color: #4ade80;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: 600;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 25px;
            backdrop-filter: blur(10px);
        }
        .card h2 {
            color: #f59e0b;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .card h2 .icon {
            font-size: 1.5rem;
        }
        .important {
            background: linear-gradient(135deg, rgba(234, 88, 12, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%);
            border: 1px solid #f97316;
        }
        .important h2 {
            color: #fb923c;
        }
        .steps {
            list-style: none;
        }
        .steps li {
            padding: 15px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            gap: 15px;
        }
        .steps li:last-child {
            border-bottom: none;
        }
        .step-number {
            background: #3b82f6;
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            flex-shrink: 0;
        }
        .step-content h3 {
            color: #f1f5f9;
            margin-bottom: 8px;
        }
        .step-content p {
            color: #94a3b8;
            line-height: 1.6;
        }
        .kbd {
            background: #374151;
            border: 1px solid #4b5563;
            border-radius: 6px;
            padding: 4px 10px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
            color: #fbbf24;
            box-shadow: 0 2px 0 #1f2937;
        }
        .code-block {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 15px 20px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.95rem;
            color: #a5f3fc;
            margin-top: 10px;
            overflow-x: auto;
        }
        .trigger-examples {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }
        .trigger {
            background: #1e3a5f;
            border: 1px solid #3b82f6;
            border-radius: 8px;
            padding: 8px 16px;
            color: #93c5fd;
            font-family: monospace;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #64748b;
        }
        .footer a {
            color: #3b82f6;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            margin: 30px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="success-badge">✓ Installation Complete</div>
            <h1>📚 Canon Keeper MCP</h1>
            <p class="subtitle">Automatic memory persistence for GitHub Copilot</p>
        </div>

        <div class="card important">
            <h2><span class="icon">⚠️</span> Action Required: Reload VS Code</h2>
            <p style="margin-bottom: 20px; color: #fcd34d;">
                The MCP server is installed but VS Code needs to reload to activate it.
            </p>
            <ul class="steps">
                <li>
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <h3>Open Command Palette</h3>
                        <p>Press <span class="kbd">Ctrl</span> + <span class="kbd">Shift</span> + <span class="kbd">P</span> (Windows/Linux) or <span class="kbd">Cmd</span> + <span class="kbd">Shift</span> + <span class="kbd">P</span> (Mac)</p>
                    </div>
                </li>
                <li>
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <h3>Type "Developer: Reload Window"</h3>
                        <p>Select it from the dropdown and press Enter</p>
                        <div class="code-block">Developer: Reload Window</div>
                    </div>
                </li>
                <li>
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <h3>Alternative: Restart VS Code</h3>
                        <p>You can also simply close and reopen VS Code</p>
                    </div>
                </li>
            </ul>
        </div>

        <div class="card">
            <h2><span class="icon">🚀</span> How to Use</h2>
            <p style="margin-bottom: 15px;">After reloading, start any Copilot conversation and use these trigger phrases:</p>
            <div class="trigger-examples">
                <span class="trigger">@History save this</span>
                <span class="trigger">save this learning</span>
                <span class="trigger">remember this</span>
                <span class="trigger">add to memory</span>
            </div>
            <div class="divider"></div>
            <h3 style="color: #f1f5f9; margin-bottom: 10px;">Example Conversation:</h3>
            <div class="code-block">
User: We discovered that the API requires UTF-8 encoding<br><br>
User: @History save what we learned<br><br>
Copilot: ✅ Saved 1 new learning:<br>
&nbsp;&nbsp;&nbsp;- API Encoding: Requires UTF-8 encoding for all requests
            </div>
        </div>

        <div class="card">
            <h2><span class="icon">⚙️</span> What Was Configured</h2>
            <ul class="steps">
                <li>
                    <div class="step-number">✓</div>
                    <div class="step-content">
                        <h3>.vscode/mcp.json</h3>
                        <p>MCP server registration for VS Code</p>
                    </div>
                </li>
                <li>
                    <div class="step-number">✓</div>
                    <div class="step-content">
                        <h3>.github/copilot-instructions.md</h3>
                        <p>Memory Persistence Protocol directive added</p>
                    </div>
                </li>
                <li>
                    <div class="step-number">✓</div>
                    <div class="step-content">
                        <h3>Session Learnings Log</h3>
                        <p>Table for storing dated learnings</p>
                    </div>
                </li>
            </ul>
        </div>

        <div class="footer">
            <p>Canon Keeper MCP • <a href="https://github.com/langchain-ai/deepagents-quickstarts">GitHub Repository</a></p>
            <p style="margin-top: 10px;">You can close this page now.</p>
        </div>
    </div>
</body>
</html>
'''


def show_completion_page():
    """Create and open the completion page in the default browser."""
    # Create temp HTML file
    temp_dir = tempfile.gettempdir()
    html_path = Path(temp_dir) / "canon_keeper_install_complete.html"
    
    html_path.write_text(COMPLETION_HTML, encoding="utf-8")
    
    # Try to open in VS Code's Simple Browser first, fallback to system browser
    try:
        # Try VS Code command line
        result = subprocess.run(
            ["code", "--goto", str(html_path)],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            raise Exception("VS Code command failed")
    except:
        # Fallback to system browser
        try:
            webbrowser.open(f"file://{html_path}")
        except:
            print(f"\n📄 Completion page saved to: {html_path}")
            print("   Open it in your browser to see reload instructions.")


def print_usage_instructions():
    """Print post-installation usage instructions."""
    print("\n" + "="*60)
    print("🎉 Canon Keeper MCP installed successfully!")
    print("="*60)
    print("""
NEXT STEPS:
1. Reload VS Code to activate the MCP server
2. In any Copilot chat, use these trigger phrases:
   - "@History save what we learned"
   - "save this learning"
   - "remember this"
   - "add to memory"

HOW IT WORKS:
- You have a conversation with Copilot
- When you want to save learnings, say "@History"
- Copilot calls the MCP tool to extract learnings
- New learnings are added to Session Learnings Log
- Duplicates are automatically skipped

ENVIRONMENT VARIABLES (optional):
- GOOGLE_API_KEY: For Google GenAI (default LLM)
- OPENAI_API_KEY: For OpenAI fallback
""")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Install Canon Keeper MCP server for Copilot memory persistence"
    )
    parser.add_argument(
        "--workspace", "-w",
        type=Path,
        default=None,
        help="Path to workspace root (auto-detected if not specified)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force overwrite existing copilot-instructions.md"
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip installing Python dependencies"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open completion page in browser"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("📚 Canon Keeper MCP Server Installer")
    print("="*60 + "\n")
    
    # Determine workspace
    if args.workspace:
        workspace = args.workspace.resolve()
    else:
        # Try to find workspace from current directory or script location
        workspace = find_workspace_root(Path.cwd())
    
    print(f"📂 Workspace: {workspace}\n")
    
    # Install dependencies
    if not args.skip_deps:
        if not install_dependencies():
            print("\n⚠️  Dependency installation failed, continuing anyway...")
    
    # Setup MCP config
    setup_mcp_config(workspace)
    
    # Setup copilot-instructions
    setup_copilot_instructions(workspace, force=args.force)
    
    # Verify
    if verify_installation(workspace):
        print_usage_instructions()
        
        # Show completion page with reload instructions
        if not args.no_browser:
            print("\n🌐 Opening completion page with reload instructions...")
            show_completion_page()
        
        return 0
    else:
        print("\n⚠️  Installation incomplete. Please check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
