<p align="center">
  <a href="./README.md">English</a> | <a href="./README_CN.md">简体中文</a>
</p>

# Sci-Hub MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that enables AI assistants to search and download academic papers from Sci-Hub.

No dependency on the broken `scihub` PyPI package. Uses `requests` + `BeautifulSoup` to directly parse Sci-Hub mirror pages, with automatic mirror failover.

## Features

- **DOI Search** - Find papers by Digital Object Identifier
- **Title Search** - Find papers by title (via CrossRef API + Sci-Hub)
- **Keyword Search** - Discover papers related to a research topic
- **PDF Download** - Download full-text PDFs
- **Metadata Retrieval** - Get paper metadata by DOI
- **Auto Mirror Failover** - Tries multiple Sci-Hub mirrors automatically

## Prerequisites

- Python 3.10+
- pip

## Installation

```bash
git clone https://github.com/CyberKrypton/Sci-Hub-MCP-Server.git
cd Sci-Hub-MCP-Server
pip install -r requirements.txt
```

## Usage

### Standalone Test

```bash
python sci_hub_search.py
```

### As MCP Server

```bash
python sci_hub_server.py
```

With `uv`, use:

```bash
uv run python sci_hub_server.py
```

### Configure with Claude Code

Add to your `~/.mcp.json`:

```json
{
  "mcpServers": {
    "scihub": {
      "command": "python",
      "args": ["path/to/Sci-Hub-MCP-Server/sci_hub_server.py"]
    }
  }
}
```

**Windows example:**

```json
{
  "mcpServers": {
    "scihub": {
      "command": "C:\\Users\\YOUR_USER\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
      "args": [
        "C:\\Users\\YOUR_USER\\Sci-Hub-MCP-Server\\sci_hub_server.py"
      ]
    }
  }
}
```

### Configure with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "scihub": {
      "command": "python",
      "args": ["path/to/Sci-Hub-MCP-Server/sci_hub_server.py"]
    }
  }
}
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_scihub_by_doi` | Search for a paper using its DOI |
| `search_scihub_by_title` | Search for a paper using its title |
| `search_scihub_by_keyword` | Search for papers using keywords |
| `download_scihub_pdf` | Download a paper PDF from a URL |
| `get_paper_metadata` | Get metadata for a paper by DOI |

## Examples

Once connected to an AI assistant, you can use natural language:

```
Search for the paper with DOI 10.1109/TSMC.2016.2597800
```

```
Find the paper titled "Attention Is All You Need"
```

```
Search for recent papers about reinforcement learning
```

```
Download the PDF to my_paper.pdf
```

## Updating Mirrors

Sci-Hub mirrors change frequently. To update, edit the `SCIHUB_MIRRORS` list in `sci_hub_search.py` (line 9-16):

```python
SCIHUB_MIRRORS = [
    'https://sci-hub.hkvisa.net',
    'https://sci-hub.mksa.top',
    'https://sci-hub.ren',
    'https://sci-hub.se',
    'https://sci-hub.st',
    'https://sci-hub.ee',
]
```

The server tries each mirror in order and uses the first one that returns a valid PDF link.

## Project Structure

```
Sci-Hub-MCP-Server/
  sci_hub_server.py      # MCP server (FastMCP entry point)
  sci_hub_search.py      # Core search & download logic
  requirements.txt       # Python dependencies
  README.md              # English documentation
  README_CN.md           # Chinese documentation
  LICENSE                # MIT License
```

## License

MIT

## Disclaimer

This tool is for research purposes only. Please respect copyright laws and use responsibly.
