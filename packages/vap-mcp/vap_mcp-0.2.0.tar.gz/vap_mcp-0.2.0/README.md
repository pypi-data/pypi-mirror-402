# vap-mcp

**VAP MCP Server** - Media generation tools for Claude Desktop via Model Context Protocol.

Generate AI images, videos, and music directly in Claude Desktop conversations.

## Quick Install

```bash
# Using uvx (recommended)
uvx vap-mcp

# Or using pipx
pipx install vap-mcp

# Or using pip
pip install vap-mcp
```

## Claude Desktop Configuration

Add to your Claude Desktop config (`~/.config/Claude/claude_desktop_config.json` on Linux/Mac or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "vap": {
      "command": "uvx",
      "args": ["vap-mcp"],
      "env": {
        "VAP_API_KEY": "vap_your_api_key_here"
      }
    }
  }
}
```

Get your API key at [vapagent.com](https://vapagent.com)

## Available Tools

### Image Generation
- **generate_image**: Generate AI images using Z-Image-Turbo (~$0.002 per image)

### Video Generation (Veo 3.1)
- **generate_video**: Generate AI videos with optional audio
  - 4 seconds: $2.40 (with audio) / $1.20 (without)
  - 6 seconds: $3.60 (with audio) / $1.80 (without)
  - 8 seconds: $4.80 (with audio) / $2.40 (without)

### Music Generation (Suno V5)
- **generate_music**: Generate AI music from text prompts
  - Describe mood, genre, instruments, tempo
  - 30-60 seconds: $0.50
  - 120 seconds: ~$0.70
  - 180 seconds: ~$0.90
  - 240 seconds: $1.10
  - Optional instrumental-only mode

### Task Management
- **get_task**: Check task status and retrieve results
- **list_tasks**: List recent generation tasks

### Utilities
- **check_balance**: Check your account balance
- **estimate_cost**: Estimate image generation cost
- **estimate_video_cost**: Estimate video generation cost
- **estimate_music_cost**: Estimate music generation cost

## Usage Examples

Once configured, you can ask Claude:

> "Generate an image of a sunset over mountains"

> "Create a 4-second video of ocean waves"

> "Generate a 60-second upbeat electronic track with synths"

> "Create instrumental jazz music, smooth and relaxing, 2 minutes"

> "Check my balance"

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VAP_API_KEY` | Your VAP API key (required) | - |
| `VAP_API_URL` | MCP API endpoint | `https://api.vapagent.com/mcp` |
| `VAP_API_BASE_URL` | Base API URL | `https://api.vapagent.com` |
| `VAP_DEBUG` | Enable debug logging | `false` |

## Running Standalone

```bash
# Run the MCP server directly
vap-mcp

# With debug logging
VAP_DEBUG=1 vap-mcp
```

## Links

- [Documentation](https://docs.vapagent.com)
- [API Reference](https://docs.vapagent.com/api)
- [Get API Key](https://vapagent.com)
- [GitHub](https://github.com/vapagent/vap-mcp)

## License

MIT License - see [LICENSE](LICENSE) for details.