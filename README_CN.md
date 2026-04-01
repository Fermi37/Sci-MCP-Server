# Sci-Hub MCP Server

一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 的服务器，让 AI 助手能够通过 Sci-Hub 搜索和下载学术论文。

不依赖 PyPI 上已损坏的 `scihub` 包，使用 `requests` + `BeautifulSoup` 直接解析 Sci-Hub 镜像页面，支持多镜像自动切换。

## 功能

- **DOI 搜索** — 通过数字对象标识符查找论文
- **标题搜索** — 通过论文标题查找（经由 CrossRef API + Sci-Hub）
- **关键词搜索** — 按研究主题发现相关论文
- **PDF 下载** — 下载论文全文 PDF，并进行基础响应校验
- **元数据获取** — 通过 DOI 获取论文元数据
- **镜像自动切换** — 依次尝试多个 Sci-Hub 镜像，使用第一个可用的

## 环境要求

- Python 3.14+
- pip

## 安装

```bash
git clone https://github.com/CyberKrypton/Sci-Hub-MCP-Server.git
cd Sci-Hub-MCP-Server
pip install -r requirements.txt
```

## 使用方式

### 独立测试

```bash
python sci_hub_search.py
```

### 作为 MCP 服务器启动

```bash
python sci_hub_server.py
```

如果使用 `uv`，可执行：

```bash
uv run python sci_hub_server.py
```

### 在 Claude Code 中配置

在 `~/.mcp.json` 中添加：

```json
{
  "mcpServers": {
    "scihub": {
      "command": "python",
      "args": ["你的路径/Sci-Hub-MCP-Server/sci_hub_server.py"]
    }
  }
}
```

**Windows 示例：**

```json
{
  "mcpServers": {
    "scihub": {
      "command": "C:\\Users\\你的用户名\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
      "args": [
        "C:\\Users\\你的用户名\\Sci-Hub-MCP-Server\\sci_hub_server.py"
      ]
    }
  }
}
```

### 在 Claude Desktop 中配置

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "scihub": {
      "command": "python",
      "args": ["你的路径/Sci-Hub-MCP-Server/sci_hub_server.py"]
    }
  }
}
```

## MCP 工具一览

| 工具名 | 说明 |
|--------|------|
| `search_scihub_by_doi` | 通过 DOI 搜索论文 |
| `search_scihub_by_title` | 通过标题搜索论文 |
| `search_scihub_by_keyword` | 通过关键词搜索论文 |
| `download_scihub_pdf` | 从 URL 下载论文 PDF |
| `get_paper_metadata` | 通过 DOI 获取论文元数据 |

## 使用示例

连接 AI 助手后，直接用自然语言即可：

```
帮我搜索 DOI 为 10.1109/TSMC.2016.2597800 的论文
```

```
查找标题为 "Attention Is All You Need" 的论文
```

```
搜索关于强化学习的最新论文
```

```
把这篇论文的 PDF 下载到 my_paper.pdf
```

## 测试

运行离线回归测试：

```bash
UV_CACHE_DIR=.uv-cache uv run pytest -q
```

运行 MCP 在线 smoke tests：

```bash
SCIHUB_LIVE_TESTS=1 UV_CACHE_DIR=.uv-cache uv run pytest -q tests/test_mcp_smoke.py
```

在线 smoke tests 会检查 MCP stdio 生命周期、`tools/list`、DOI 搜索、标题搜索和 PDF 下载。该测试需要网络访问以及可用的 Sci-Hub 镜像。

GitHub Actions 策略：

- `.github/workflows/ci.yml` 是必须通过的离线校验工作流。
- `.github/workflows/live-smoke.yml` 是用于发版检查的非阻塞在线 smoke workflow。

## 更新镜像

Sci-Hub 的镜像地址经常变化。如需更新，编辑 `sci_hub_search.py` 第 9-16 行的 `SCIHUB_MIRRORS` 列表：

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

服务器会按顺序逐个尝试，使用第一个返回有效 PDF 链接的镜像。

## 项目结构

```
Sci-Hub-MCP-Server/
  sci_hub_server.py      # MCP 服务器入口（FastMCP）
  sci_hub_search.py      # 核心搜索与下载逻辑
  requirements.txt       # Python 依赖
  README.md              # 英文文档
  README_CN.md           # 中文文档（本文件）
  LICENSE                # MIT 许可证
```

## 许可证

MIT

## 免责声明

本工具仅供学术研究用途，请遵守版权法律，合理使用。
