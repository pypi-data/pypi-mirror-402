"""
VAP MCP Server - Media generation tools for Claude Desktop.

This module implements an MCP server using the official MCP SDK,
providing image and video generation tools via the VAP API.

Directive: #384 (MCP Standalone Distribution)
"""

import os
import sys
import logging
import asyncio
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

API_URL = os.getenv("VAP_API_URL", os.getenv("VAPE_API_URL", "https://api.vapagent.com/mcp")).strip()
API_BASE_URL = os.getenv("VAP_API_BASE_URL", os.getenv("VAPE_API_BASE_URL", "https://api.vapagent.com")).strip()
API_KEY = os.getenv("VAP_API_KEY", os.getenv("VAPE_API_KEY", "")).strip()

# Video pricing (Veo 3.1)
VIDEO_COSTS_WITH_AUDIO = {4: 2.40, 6: 3.60, 8: 4.80}
VIDEO_COSTS_NO_AUDIO = {4: 1.20, 6: 1.80, 8: 2.40}

# Music pricing (Suno V5)
MUSIC_COST_BASE = 0.50  # $0.50 base
MUSIC_COST_MAX = 1.10   # $1.10 max for extended

# Logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("VAP_DEBUG", os.getenv("VAPE_DEBUG")) else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# MCP SERVER
# ═══════════════════════════════════════════════════════════════════════════

server = Server("vap-mcp")


def get_headers() -> dict:
    """Get HTTP headers with authentication."""
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


async def make_mcp_request(endpoint: str, payload: dict | None = None) -> dict:
    """Make HTTP request to VAP MCP API."""
    url = f"{API_URL}{endpoint}"
    logger.debug(f"MCP Request: POST {url}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload or {}, headers=get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"MCP request error: {e}")
            return {"error": str(e)}


async def make_v3_request(endpoint: str, payload: dict | None = None, method: str = "POST") -> dict:
    """Make HTTP request to VAP V3 API."""
    url = f"{API_BASE_URL}{endpoint}"
    logger.debug(f"V3 Request: {method} {url}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=get_headers())
            else:
                response = await client.post(url, json=payload or {}, headers=get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"V3 request error: {e}")
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

TOOLS = [
    Tool(
        name="generate_image",
        description="Generate an AI image from a text prompt using Z-Image-Turbo. Cost: ~$0.002 per image.",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description of the image to generate"
                },
                "aspect_ratio": {
                    "type": "string",
                    "description": "Aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4)",
                    "default": "1:1"
                },
                "style": {
                    "type": "string",
                    "description": "Style preset (realistic, anime, artistic, etc.)",
                    "default": "realistic"
                }
            },
            "required": ["prompt"]
        }
    ),
    Tool(
        name="generate_video",
        description="Generate an AI video from a text prompt using Veo 3.1. Supports 4, 6, or 8 second videos with optional audio.",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description of the video to generate"
                },
                "duration": {
                    "type": "integer",
                    "description": "Video duration in seconds (4, 6, or 8)",
                    "default": 8,
                    "enum": [4, 6, 8]
                },
                "aspect_ratio": {
                    "type": "string",
                    "description": "Aspect ratio (16:9 or 9:16)",
                    "default": "16:9",
                    "enum": ["16:9", "9:16"]
                },
                "generate_audio": {
                    "type": "boolean",
                    "description": "Include AI-generated audio",
                    "default": True
                },
                "resolution": {
                    "type": "string",
                    "description": "Video resolution (720p or 1080p)",
                    "default": "720p",
                    "enum": ["720p", "1080p"]
                },
                "negative_prompt": {
                    "type": "string",
                    "description": "What to avoid in the video"
                }
            },
            "required": ["prompt"]
        }
    ),
    Tool(
        name="get_task",
        description="Check the status of a generation task and get the result URL when complete.",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The task ID returned from generate_image or generate_video"
                }
            },
            "required": ["task_id"]
        }
    ),
    Tool(
        name="list_tasks",
        description="List recent generation tasks.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of tasks to return",
                    "default": 10
                }
            }
        }
    ),
    Tool(
        name="check_balance",
        description="Check your VAP account balance.",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="estimate_cost",
        description="Estimate the cost of an image generation request.",
        inputSchema={
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Number of images to generate",
                    "default": 1
                }
            }
        }
    ),
    Tool(
        name="estimate_video_cost",
        description="Estimate the cost of a video generation request.",
        inputSchema={
            "type": "object",
            "properties": {
                "duration": {
                    "type": "integer",
                    "description": "Video duration in seconds (4, 6, or 8)",
                    "default": 8,
                    "enum": [4, 6, 8]
                },
                "generate_audio": {
                    "type": "boolean",
                    "description": "Include AI-generated audio",
                    "default": True
                }
            }
        }
    ),
    Tool(
        name="generate_music",
        description="Generate AI music from a text prompt using Suno V5. Describe mood, genre, instruments. Cost: $0.50-$1.10 per track.",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description of the music to generate (mood, genre, instruments, tempo)"
                },
                "duration": {
                    "type": "integer",
                    "description": "Music duration in seconds (30-240)",
                    "default": 60
                },
                "instrumental": {
                    "type": "boolean",
                    "description": "Generate instrumental only (no vocals)",
                    "default": False
                }
            },
            "required": ["prompt"]
        }
    ),
    Tool(
        name="estimate_music_cost",
        description="Estimate the cost of a music generation request using Suno V5.",
        inputSchema={
            "type": "object",
            "properties": {
                "duration": {
                    "type": "integer",
                    "description": "Music duration in seconds (30-240)",
                    "default": 60
                }
            }
        }
    )
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return available tools."""
    return TOOLS


# ═══════════════════════════════════════════════════════════════════════════
# TOOL HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

async def handle_generate_image(arguments: dict) -> str:
    """Handle generate_image tool call."""
    prompt = arguments.get("prompt", "")
    if not prompt:
        return "Error: prompt is required"
    
    response = await make_mcp_request("/tools/call", {
        "name": "generate_image",
        "arguments": arguments
    })
    
    if "error" in response:
        return f"Error: {response['error']}"
    
    # Extract content from MCP response
    content = response.get("content", [])
    if content and isinstance(content, list):
        return content[0].get("text", str(response))
    return str(response)


async def handle_generate_video(arguments: dict) -> str:
    """Handle generate_video tool call (Veo 3.1)."""
    prompt = arguments.get("prompt", "")
    if not prompt:
        return "Error: prompt is required"
    
    duration = arguments.get("duration", 8)
    if duration not in (4, 6, 8):
        duration = 8
    
    aspect_ratio = arguments.get("aspect_ratio", "16:9")
    if aspect_ratio not in ("16:9", "9:16"):
        aspect_ratio = "16:9"
    
    generate_audio = arguments.get("generate_audio", True)
    resolution = arguments.get("resolution", "720p")
    if resolution not in ("720p", "1080p"):
        resolution = "720p"
    
    params = {
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "generate_audio": generate_audio,
        "resolution": resolution
    }
    if arguments.get("negative_prompt"):
        params["negative_prompt"] = arguments["negative_prompt"]
    
    response = await make_v3_request("/v3/tasks", {
        "type": "video",
        "params": params
    })
    
    if "error" in response:
        return f"Error: {response['error']}"
    
    task_id = response.get("task_id", "unknown")
    cost_table = VIDEO_COSTS_WITH_AUDIO if generate_audio else VIDEO_COSTS_NO_AUDIO
    estimated_cost = response.get("estimated_cost", cost_table.get(duration, 4.80))
    
    return f"""Video generation task created (Veo 3.1)!

Task ID: {task_id}
Duration: {duration} seconds
Aspect Ratio: {aspect_ratio}
Resolution: {resolution}
Audio: {'Yes' if generate_audio else 'No'}
Estimated Cost: ${estimated_cost}

Use get_task with this task_id to check status and get the video URL when complete."""


async def handle_get_task(arguments: dict) -> str:
    """Handle get_task tool call."""
    task_id = arguments.get("task_id", "")
    if not task_id:
        return "Error: task_id is required"
    
    response = await make_v3_request(f"/v3/tasks/{task_id}", method="GET")
    
    if "error" in response:
        return f"Error: {response['error']}"
    
    status = response.get("status", "unknown")
    task_type = response.get("type", "unknown")
    estimated_cost = response.get("estimated_cost", "N/A")
    actual_cost = response.get("actual_cost")
    error_message = response.get("error_message")
    result = response.get("result", {}) or {}
    
    video_url = result.get("video_url") or result.get("output_url")
    image_url = result.get("image_url") or result.get("output_url")
    audio_url = result.get("audio_url") or result.get("music_url")
    
    lines = [
        f"Task: {task_id}",
        f"Type: {task_type}",
        f"Status: {status}",
        f"Estimated Cost: ${estimated_cost}",
    ]
    
    if actual_cost:
        lines.append(f"Actual Cost: ${actual_cost}")
    
    if status == "completed":
        if video_url:
            lines.append(f"\n🎬 Video URL: {video_url}")
        elif audio_url:
            lines.append(f"\n🎵 Audio URL: {audio_url}")
        elif image_url:
            lines.append(f"\n🖼️ Image URL: {image_url}")
    elif status == "failed" and error_message:
        lines.append(f"\n❌ Error: {error_message}")
    elif status in ("pending", "queued", "executing"):
        lines.append(f"\n⏳ Task is still {status}. Check again shortly.")
    
    return "\n".join(lines)


async def handle_list_tasks(arguments: dict) -> str:
    """Handle list_tasks tool call."""
    response = await make_mcp_request("/tools/call", {
        "name": "list_tasks",
        "arguments": arguments
    })
    
    if "error" in response:
        return f"Error: {response['error']}"
    
    content = response.get("content", [])
    if content and isinstance(content, list):
        return content[0].get("text", str(response))
    return str(response)


async def handle_check_balance(arguments: dict) -> str:
    """Handle check_balance tool call."""
    response = await make_mcp_request("/tools/call", {
        "name": "check_balance",
        "arguments": {}
    })
    
    if "error" in response:
        return f"Error: {response['error']}"
    
    content = response.get("content", [])
    if content and isinstance(content, list):
        return content[0].get("text", str(response))
    return str(response)


async def handle_estimate_cost(arguments: dict) -> str:
    """Handle estimate_cost tool call."""
    count = arguments.get("count", 1)
    cost_per_image = 0.002
    total = cost_per_image * count
    
    return f"""Image Generation Cost Estimate:

Count: {count} image(s)
Cost per image: ${cost_per_image:.3f}
Total: ${total:.3f}

Note: Using Z-Image-Turbo model."""


async def handle_estimate_video_cost(arguments: dict) -> str:
    """Handle estimate_video_cost tool call."""
    duration = arguments.get("duration", 8)
    if duration not in (4, 6, 8):
        duration = 8
    
    generate_audio = arguments.get("generate_audio", True)
    cost_table = VIDEO_COSTS_WITH_AUDIO if generate_audio else VIDEO_COSTS_NO_AUDIO
    cost = cost_table.get(duration, 4.80)
    
    return f"""Video Generation Cost Estimate (Veo 3.1):

Duration: {duration} seconds
Audio: {'Yes' if generate_audio else 'No'}
Cost: ${cost:.2f}

Pricing with audio:
- 4 seconds: $2.40
- 6 seconds: $3.60
- 8 seconds: $4.80

Pricing without audio:
- 4 seconds: $1.20
- 6 seconds: $1.80
- 8 seconds: $2.40"""


async def handle_generate_music(arguments: dict) -> str:
    """Handle generate_music tool call (Suno V5)."""
    prompt = arguments.get("prompt", "")
    if not prompt:
        return "Error: prompt is required"
    
    duration = arguments.get("duration", 60)
    # Clamp duration to valid range
    if duration < 30:
        duration = 30
    elif duration > 240:
        duration = 240
    
    instrumental = arguments.get("instrumental", False)
    
    params = {
        "prompt": prompt,
        "duration": duration,
        "instrumental": instrumental
    }
    
    response = await make_v3_request("/v3/tasks", {
        "type": "music",
        "params": params
    })
    
    if "error" in response:
        return f"Error: {response['error']}"
    
    task_id = response.get("task_id", "unknown")
    # Estimate cost based on duration
    if duration <= 60:
        estimated_cost = MUSIC_COST_BASE
    else:
        # Linear interpolation: 60s=$0.50, 240s=$1.10
        cost_range = MUSIC_COST_MAX - MUSIC_COST_BASE
        duration_range = 240 - 60
        estimated_cost = MUSIC_COST_BASE + (cost_range * (duration - 60) / duration_range)
    
    estimated_cost = response.get("estimated_cost", round(estimated_cost, 2))
    
    return f"""Music generation task created (Suno V5)!

Task ID: {task_id}
Duration: {duration} seconds
Instrumental: {'Yes' if instrumental else 'No (with vocals)'}
Estimated Cost: ${estimated_cost}

Use get_task with this task_id to check status and get the audio URL when complete."""


async def handle_estimate_music_cost(arguments: dict) -> str:
    """Handle estimate_music_cost tool call."""
    duration = arguments.get("duration", 60)
    
    # Clamp duration to valid range
    if duration < 30:
        duration = 30
    elif duration > 240:
        duration = 240
    
    # Calculate cost based on duration
    if duration <= 60:
        cost = MUSIC_COST_BASE
    else:
        # Linear interpolation: 60s=$0.50, 240s=$1.10
        cost_range = MUSIC_COST_MAX - MUSIC_COST_BASE
        duration_range = 240 - 60
        cost = MUSIC_COST_BASE + (cost_range * (duration - 60) / duration_range)
    
    return f"""Music Generation Cost Estimate (Suno V5):

Duration: {duration} seconds
Cost: ${cost:.2f}

Pricing:
- 30-60 seconds: $0.50
- 120 seconds: ~$0.70
- 180 seconds: ~$0.90
- 240 seconds: $1.10

Note: Suno V5 generates high-quality music with optional vocals."""


# Tool handler dispatch
TOOL_HANDLERS = {
    "generate_image": handle_generate_image,
    "generate_video": handle_generate_video,
    "generate_music": handle_generate_music,
    "get_task": handle_get_task,
    "list_tasks": handle_list_tasks,
    "check_balance": handle_check_balance,
    "estimate_cost": handle_estimate_cost,
    "estimate_video_cost": handle_estimate_video_cost,
    "estimate_music_cost": handle_estimate_music_cost,
}


@server.call_tool()
async def call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool call: {name}")
    
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    try:
        result = await handler(arguments or {})
        return [TextContent(type="text", text=result)]
    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

async def run_server():
    """Run the MCP server with stdio transport."""
    logger.info("VAP MCP Server starting...")
    logger.info(f"API URL: {API_URL}")
    logger.info(f"API Key: {'configured' if API_KEY else 'NOT SET'}")
    
    if not API_KEY:
        logger.warning("VAP_API_KEY not set! Set via environment variable.")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()