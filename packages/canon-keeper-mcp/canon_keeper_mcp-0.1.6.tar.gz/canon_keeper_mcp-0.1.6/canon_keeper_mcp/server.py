"""
Canon Keeper MCP Server

Provides tools for Copilot to persist learnings to copilot-instructions.md.
No API key required - Copilot does the extraction, this tool handles formatting and deduplication.

Usage:
    python -m canon_keeper_mcp.server
"""

import json
import re
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("canon-keeper")

# ============================================================================
# Parsing and Deduplication Logic (no LLM needed)
# ============================================================================

def parse_existing_learnings(instructions_content: str) -> list[dict]:
    """Parse the Session Learnings Log table from copilot-instructions.md."""
    learnings = []
    
    lines = instructions_content.split('\n')
    
    for line in lines:
        # Look for table rows (start with |, have multiple | separators)
        if '|' in line and not line.strip().startswith('|--') and '---' not in line:
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            
            if len(parts) >= 4:
                # Skip header row
                if parts[0] == 'Date' or parts[1] == 'Topic':
                    continue
                    
                learnings.append({
                    "date": parts[0],
                    "topic": parts[1],
                    "decision": parts[2],
                    "rationale": parts[3] if len(parts) > 3 else ""
                })
    
    return learnings


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Lowercase, remove extra whitespace, remove punctuation
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text


def is_similar(text1: str, text2: str, threshold: float = 0.7) -> bool:
    """Check if two texts are similar using word overlap."""
    words1 = set(normalize_text(text1).split())
    words2 = set(normalize_text(text2).split())
    
    if not words1 or not words2:
        return False
    
    intersection = words1 & words2
    union = words1 | words2
    
    jaccard = len(intersection) / len(union) if union else 0
    return jaccard >= threshold


def check_duplicate_simple(topic: str, decision: str, existing_learnings: list[dict]) -> dict:
    """Check if a learning is a duplicate using simple string matching."""
    for existing in existing_learnings:
        # Check topic similarity
        if is_similar(topic, existing.get("topic", ""), threshold=0.6):
            # Check decision similarity
            if is_similar(decision, existing.get("decision", ""), threshold=0.5):
                return {
                    "is_duplicate": True,
                    "duplicate_of": existing.get("topic"),
                    "reason": f"Similar to existing: {existing.get('topic')}"
                }
    
    return {
        "is_duplicate": False,
        "duplicate_of": None,
        "reason": "No similar existing learning found"
    }


def format_learning_as_table_row(learning: dict) -> str:
    """Format a learning as a markdown table row."""
    date = learning.get("date", datetime.now().strftime("%Y-%m-%d"))
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
            description="""Save learnings to copilot-instructions.md. 

IMPORTANT: YOU (Copilot) must extract the learnings first, then pass them to this tool.

This tool:
1. Takes learnings YOU have already extracted from the conversation
2. Checks for duplicates against existing entries
3. Returns formatted markdown table rows to append

Input format - pass an array of learnings:
{
    "learnings": [
        {"topic": "Short Topic", "decision": "What was decided", "rationale": "Why"}
    ],
    "current_instructions": "content of copilot-instructions.md"
}

A durable learning is:
- A technical decision or architectural choice
- A discovered limitation or workaround  
- A configuration or setup requirement
- A debugging insight

NOT a durable learning:
- Temporary tasks or TODOs
- Conversation pleasantries
- Questions without answers""",
            inputSchema={
                "type": "object",
                "properties": {
                    "learnings": {
                        "type": "array",
                        "description": "Array of learnings YOU extracted. Each has: topic, decision, rationale",
                        "items": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string", "description": "Short topic name (3-5 words)"},
                                "decision": {"type": "string", "description": "The key decision or learning"},
                                "rationale": {"type": "string", "description": "Why this matters"}
                            },
                            "required": ["topic", "decision"]
                        }
                    },
                    "current_instructions": {
                        "type": "string",
                        "description": "The current content of copilot-instructions.md (for deduplication)"
                    }
                },
                "required": ["learnings", "current_instructions"]
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
        learnings = arguments.get("learnings", [])
        current_instructions = arguments.get("current_instructions", "")
        
        if not learnings:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "no_learnings",
                    "message": "No learnings provided. You need to extract learnings from the conversation first.",
                    "new_learnings": [],
                    "duplicates_skipped": [],
                    "markdown_to_append": ""
                })
            )]
        
        # Parse existing learnings
        existing = parse_existing_learnings(current_instructions)
        
        # Deduplicate
        new_learnings = []
        duplicates_skipped = []
        
        for learning in learnings:
            topic = learning.get("topic", "")
            decision = learning.get("decision", "")
            
            result = check_duplicate_simple(topic, decision, existing)
            
            if result.get("is_duplicate"):
                duplicates_skipped.append({
                    **learning,
                    "duplicate_of": result.get("duplicate_of"),
                    "reason": result.get("reason")
                })
            else:
                new_learnings.append(learning)
        
        # Format as markdown
        markdown_rows = [format_learning_as_table_row(l) for l in new_learnings]
        markdown_to_append = "\n".join(markdown_rows)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "message": f"Found {len(new_learnings)} new learning(s), skipped {len(duplicates_skipped)} duplicate(s).",
                "new_learnings": new_learnings,
                "duplicates_skipped": duplicates_skipped,
                "markdown_to_append": markdown_to_append,
                "target_section": "Session Learnings Log",
                "instruction": "Append the markdown_to_append content to the Session Learnings Log table in copilot-instructions.md"
            })
        )]
    
    elif name == "check_learning_exists":
        topic = arguments.get("topic", "")
        decision = arguments.get("decision", "")
        current_instructions = arguments.get("current_instructions", "")
        
        existing = parse_existing_learnings(current_instructions)
        result = check_duplicate_simple(topic, decision, existing)
        
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
