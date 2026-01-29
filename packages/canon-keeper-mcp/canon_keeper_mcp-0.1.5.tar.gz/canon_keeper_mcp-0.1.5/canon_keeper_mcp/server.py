"""
Canon Keeper MCP Server

Extracts durable learnings from Copilot conversations and deduplicates
against existing entries in copilot-instructions.md.

Usage:
    python -m canon_keeper_mcp.server
"""

import json
import os
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Try to import Google GenAI, fallback to OpenAI
GENAI_CLIENT: Any | None = None
GENAI_TYPES: Any | None = None
OPENAI_CLIENT: Any | None = None
LLM_PROVIDER: str | None = None

try:
    from google import genai as _genai_module
    from google.genai import types as _genai_types

    GENAI_CLIENT = _genai_module
    GENAI_TYPES = _genai_types
    LLM_PROVIDER = "google"
except ImportError:
    try:
        import openai as _openai_module

        OPENAI_CLIENT = _openai_module
        LLM_PROVIDER = "openai"
    except ImportError:
        LLM_PROVIDER = None

server = Server("canon-keeper")

# ============================================================================
# LLM Extraction Logic
# ============================================================================

EXTRACTION_PROMPT = """You are a learning extraction system. Analyze the following conversation and extract DURABLE learnings that should be remembered for future sessions.

A durable learning is:
- A technical decision or architectural choice (e.g., "Use FFmpeg stream copy for lossless merge")
- A discovered limitation or workaround (e.g., "ChatContext.history only includes current participant")
- A configuration or setup requirement (e.g., "Set PYTHONIOENCODING=utf-8 on Windows")
- A debugging insight (e.g., "tool_choice='any' forces tool execution")

NOT a durable learning:
- Temporary tasks or TODOs
- Conversation pleasantries
- Questions without answers
- Code that was written (the code itself is the artifact)

For each learning, provide:
1. topic: Short topic name (3-5 words)
2. decision: The actual learning/decision (1 sentence)
3. rationale: Why this matters (brief)

Respond in JSON format:
{
    "learnings": [
        {
            "topic": "Topic Name",
            "decision": "The key decision or learning",
            "rationale": "Why this is important"
        }
    ]
}

If no durable learnings are found, return: {"learnings": []}

CONVERSATION:
"""

DEDUPLICATION_PROMPT = """You are a deduplication system. Compare the NEW learning against EXISTING learnings and determine if it's a duplicate.

A learning is a DUPLICATE if:
- It covers the same topic AND same decision (even if worded differently)
- It's a subset of an existing learning
- It's semantically equivalent to an existing entry

A learning is NOT a duplicate if:
- It's about a different topic
- It adds new information not in existing entries
- It contradicts or updates an existing entry (mark as "update" not "duplicate")

EXISTING LEARNINGS:
{existing}

NEW LEARNING:
Topic: {topic}
Decision: {decision}
Rationale: {rationale}

Respond in JSON:
{{
    "is_duplicate": true/false,
    "is_update": true/false,
    "duplicate_of": "topic name if duplicate, null otherwise",
    "reason": "brief explanation"
}}
"""


def call_llm(prompt: str) -> str:
    """Call the configured LLM provider."""
    if LLM_PROVIDER == "google":
        if GENAI_CLIENT is None or GENAI_TYPES is None:
            raise RuntimeError("Google GenAI client not available. Install google-genai.")

        client = GENAI_CLIENT.Client()
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=prompt,
            config=GENAI_TYPES.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        if response.text is None:
            raise RuntimeError("LLM response missing text content.")
        return response.text
    elif LLM_PROVIDER == "openai":
        if OPENAI_CLIENT is None:
            raise RuntimeError("OpenAI client not available. Install openai.")

        client = OPENAI_CLIENT.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        if not response.choices:
            raise RuntimeError("OpenAI response missing choices.")

        message = response.choices[0].message
        if message.content is None:
            raise RuntimeError("OpenAI response missing message content.")

        return message.content
    else:
        raise RuntimeError("No LLM provider available. Install google-genai or openai.")


def extract_learnings_from_conversation(conversation: str) -> list[dict]:
    """Extract learnings from conversation text using LLM."""
    prompt = EXTRACTION_PROMPT + conversation
    response = call_llm(prompt)
    
    try:
        data = json.loads(response)
        return data.get("learnings", [])
    except json.JSONDecodeError:
        return []


def parse_existing_learnings(instructions_content: str) -> list[dict]:
    """Parse the Session Learnings Log table from copilot-instructions.md."""
    learnings = []
    
    # Find the Session Learnings Log section
    lines = instructions_content.split('\n')
    in_table = False
    
    for line in lines:
        # Look for table rows (start with |, have multiple | separators)
        if '|' in line and not line.strip().startswith('|--'):
            parts = [p.strip() for p in line.split('|')]
            # Filter empty parts and check if it's a data row (not header)
            parts = [p for p in parts if p]
            
            if len(parts) >= 4 and parts[0] not in ['Date', '------']:
                # Skip header row
                if 'Date' in parts[0] or '---' in parts[0]:
                    continue
                    
                learnings.append({
                    "date": parts[0] if len(parts) > 0 else "",
                    "topic": parts[1] if len(parts) > 1 else "",
                    "decision": parts[2] if len(parts) > 2 else "",
                    "rationale": parts[3] if len(parts) > 3 else ""
                })
    
    return learnings


def check_duplicate(new_learning: dict, existing_learnings: list[dict]) -> dict:
    """Check if a learning is a duplicate of existing entries."""
    if not existing_learnings:
        return {"is_duplicate": False, "is_update": False, "duplicate_of": None, "reason": "No existing learnings"}
    
    # Format existing learnings for the prompt
    existing_text = "\n".join([
        f"- [{l['date']}] {l['topic']}: {l['decision']} ({l['rationale']})"
        for l in existing_learnings
    ])
    
    prompt = DEDUPLICATION_PROMPT.format(
        existing=existing_text,
        topic=new_learning.get("topic", ""),
        decision=new_learning.get("decision", ""),
        rationale=new_learning.get("rationale", "")
    )
    
    response = call_llm(prompt)
    
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"is_duplicate": False, "is_update": False, "duplicate_of": None, "reason": "Parse error"}


def format_learning_as_table_row(learning: dict) -> str:
    """Format a learning as a markdown table row."""
    date = datetime.now().strftime("%Y-%m-%d")
    topic = learning.get("topic", "Unknown")
    decision = learning.get("decision", "")
    rationale = learning.get("rationale", "")
    return f"| {date} | {topic} | {decision} | {rationale} |"


# ============================================================================
# MCP Tool Definitions
# ============================================================================


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="extract_and_save_learnings",
            description="""Extract durable learnings from a Copilot conversation and prepare them for saving to copilot-instructions.md.
            
            This tool:
            1. Analyzes the conversation for technical decisions, architectural choices, workarounds, and insights
            2. Compares against existing learnings in copilot-instructions.md to avoid duplicates
            3. Returns only NEW learnings formatted as markdown table rows
            
            The caller (Copilot) should then append the returned markdown to Section 7 (Session Learnings Log) of copilot-instructions.md.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation": {
                        "type": "string",
                        "description": "The full conversation text to analyze for learnings"
                    },
                    "current_instructions": {
                        "type": "string",
                        "description": "The current content of copilot-instructions.md (for deduplication)"
                    }
                },
                "required": ["conversation", "current_instructions"]
            }
        ),
        Tool(
            name="check_learning_exists",
            description="Check if a specific learning already exists in copilot-instructions.md",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic of the learning to check"
                    },
                    "decision": {
                        "type": "string",
                        "description": "The decision/learning to check"
                    },
                    "current_instructions": {
                        "type": "string",
                        "description": "The current content of copilot-instructions.md"
                    }
                },
                "required": ["topic", "decision", "current_instructions"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "extract_and_save_learnings":
        conversation = arguments.get("conversation", "")
        current_instructions = arguments.get("current_instructions", "")
        
        # Step 1: Extract learnings from conversation
        extracted = extract_learnings_from_conversation(conversation)
        
        if not extracted:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "no_learnings",
                    "message": "No durable learnings found in this conversation.",
                    "new_learnings": [],
                    "duplicates_skipped": [],
                    "markdown_to_append": ""
                })
            )]
        
        # Step 2: Parse existing learnings
        existing = parse_existing_learnings(current_instructions)
        
        # Step 3: Deduplicate
        new_learnings = []
        duplicates_skipped = []
        updates_needed = []
        
        for learning in extracted:
            result = check_duplicate(learning, existing)
            
            if result.get("is_duplicate"):
                duplicates_skipped.append({
                    **learning,
                    "duplicate_of": result.get("duplicate_of"),
                    "reason": result.get("reason")
                })
            elif result.get("is_update"):
                updates_needed.append({
                    **learning,
                    "updates": result.get("duplicate_of"),
                    "reason": result.get("reason")
                })
                # Still add updates as new entries
                new_learnings.append(learning)
            else:
                new_learnings.append(learning)
        
        # Step 4: Format as markdown
        markdown_rows = [format_learning_as_table_row(l) for l in new_learnings]
        markdown_to_append = "\n".join(markdown_rows)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "message": f"Found {len(new_learnings)} new learning(s), skipped {len(duplicates_skipped)} duplicate(s).",
                "new_learnings": new_learnings,
                "duplicates_skipped": duplicates_skipped,
                "updates_needed": updates_needed,
                "markdown_to_append": markdown_to_append,
                "target_section": "Section 7 - Session Learnings Log",
                "instruction": "Append the markdown_to_append content to the Session Learnings Log table in copilot-instructions.md"
            })
        )]
    
    elif name == "check_learning_exists":
        topic = arguments.get("topic", "")
        decision = arguments.get("decision", "")
        current_instructions = arguments.get("current_instructions", "")
        
        existing = parse_existing_learnings(current_instructions)
        result = check_duplicate(
            {"topic": topic, "decision": decision, "rationale": ""},
            existing
        )
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "exists": result.get("is_duplicate", False),
                "similar_to": result.get("duplicate_of"),
                "reason": result.get("reason")
            })
        )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"})
        )]


# ============================================================================
# Main Entry Point
# ============================================================================


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    
    asyncio.run(main())