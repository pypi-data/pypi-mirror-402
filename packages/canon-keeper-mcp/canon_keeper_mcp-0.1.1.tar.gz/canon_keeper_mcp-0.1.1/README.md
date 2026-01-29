# Canon Keeper MCP Server

An MCP (Model Context Protocol) server that extracts durable learnings from Copilot conversations and persists them to `copilot-instructions.md`.

**No VS Code extension required!** Copilot invokes the MCP tool directly.

## Quick Install

```bash
# From any project directory
python -m canon_keeper_mcp install

# Or specify a workspace
python -m canon_keeper_mcp install --workspace /path/to/project
```

The installer will:
1. ✅ Install dependencies (`mcp`, `google-genai`)
2. ✅ Configure `.vscode/mcp.json` with the canon-keeper server
3. ✅ Create/update `.github/copilot-instructions.md` with:
   - Memory Persistence Protocol (`@History` directive)
   - Best practices template
   - Session Learnings Log table

## Features

- **Intelligent Extraction**: Uses LLM to identify technical decisions, architectural choices, workarounds, and insights
- **Deduplication**: Compares against existing learnings to avoid duplicates
- **Update Detection**: Identifies when a learning updates/supersedes an existing entry
- **Markdown Formatting**: Returns properly formatted table rows for the Session Learnings Log

## Usage

After installation, reload VS Code and use these trigger phrases in any Copilot chat:

```
User: @History save what we learned
User: save this learning  
User: remember this
User: add to memory
```

Copilot will:
1. Gather the full conversation history
2. Call the MCP tool to extract learnings
3. Deduplicate against existing entries
4. Append new learnings to your `copilot-instructions.md`
5. Report what was saved/skipped

## Manual Installation

If you prefer to install manually:

### 1. Install dependencies

```bash
pip install mcp google-genai
```

### 2. Configure MCP server

Add to `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "canon-keeper": {
      "command": "python",
      "args": ["-m", "canon_keeper_mcp"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### 3. Add directive to copilot-instructions.md

Add this to your `.github/copilot-instructions.md`:

```markdown
### Memory Persistence Protocol (@History)

**Rule:** When the user includes `@History`, `save this`, `remember this`, or `add to memory` in any message:

1. Read the current `copilot-instructions.md` file content
2. Collect the full conversation history from this session
3. Call MCP tool `canon_keeper.extract_and_save_learnings` with:
   - `conversation`: The complete conversation text
   - `current_instructions`: The full content of copilot-instructions.md
4. If `markdown_to_append` is non-empty, append it to the Session Learnings Log table
5. Report what was saved and what was skipped as duplicates

**Trigger phrases:** `@History`, `save this`, `remember this`, `add to memory`
```

### 4. Add Session Learnings Log table

```markdown
## Session Learnings Log

| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
```

## MCP Tools

### `extract_and_save_learnings`

Extracts learnings from conversation and deduplicates against existing entries.

**Input:**
- `conversation` (string): Full conversation text
- `current_instructions` (string): Current copilot-instructions.md content

**Output:**
```json
{
  "status": "success",
  "message": "Found 2 new learning(s), skipped 1 duplicate(s).",
  "new_learnings": [...],
  "duplicates_skipped": [...],
  "markdown_to_append": "| 2026-01-17 | Topic | Decision | Rationale |",
  "target_section": "Session Learnings Log"
}
```

### `check_learning_exists`

Check if a specific learning already exists.

**Input:**
- `topic` (string): Learning topic
- `decision` (string): The decision/learning
- `current_instructions` (string): Current copilot-instructions.md content

**Output:**
```json
{
  "exists": true,
  "similar_to": "Existing Topic Name",
  "reason": "Semantically equivalent to existing entry"
}
```

## LLM Providers

Supports:
- **Google GenAI** (default): Uses `gemini-2.0-flash-001`
- **OpenAI** (fallback): Uses `gpt-4o-mini`

Set appropriate API keys:
- `GOOGLE_API_KEY` for Google GenAI
- `OPENAI_API_KEY` for OpenAI
