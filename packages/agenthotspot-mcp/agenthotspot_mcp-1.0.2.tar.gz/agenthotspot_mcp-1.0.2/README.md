<p align="center">
  <a href="https://agenthotspot.com">
    <img src="https://agenthotspot.com/AHSLogo.png" alt="AgentHotspot Logo" width="200">
  </a>
</p>

<h1 align="center">AgentHotspot MCP Server</h1>

<p align="center">
  <strong>🔍 Search 6,000+ MCP connectors directly from your AI agent</strong>
</p>

<p align="center">
  <a href="https://agenthotspot.com"><img src="https://img.shields.io/badge/AgentHotspot-Marketplace-blue?style=for-the-badge" alt="AgentHotspot"></a>
  <a href="https://github.com/AgentHotspot/agenthotspot-mcp/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-Compatible-purple?style=for-the-badge" alt="MCP"></a>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-contributing">Contributing</a>
</p>

<p align="center">
  <a href="https://agenthotspot.com">agenthotspot.com</a>
</p>

---

## 🌟 What is AgentHotspot?

[**AgentHotspot**](https://agenthotspot.com) a marketplace for AI agent developers. It provides:

- 🔌 **6,000+ curated MCP connectors** ready to connect and integrate for agent builders
- 🚀 **One-click integration** with Claude Desktop, OpenAI Agents, n8n, and more
- 💰 **Instant Monetization tools** for MCP connector creators
- 📊 **Analytics dashboard** to track usage and performance

This MCP server allows your AI agents to **search and discover** oss connectors from the AgentHotspot marketplace.

---

## ✨ Features

- 🔍 **Search Connectors** — Query the AgentHotspot catalog with natural language
- 📦 **Lightweight** — Minimal dependencies, easy to install
- 🔧 **MCP Compatible** — Works with any MCP-compatible client

---


## 📦 Installation

### Prerequisites

- Python 3.10+
- An MCP-compatible client (Claude Desktop, OpenAI Agents SDK, custom agents, etc.)

### From Source

```bash
git clone https://github.com/AgentHotspot/agenthotspot-mcp.git
cd agenthotspot-mcp

# Install dependencies
pip install -r requirements.txt

# Install module
pip install -e .
```

---

## 🔧 Usage

### Run the Server Independently

```bash
# Run directly
python3 -m agenthotspot_mcp

# Or using the script
python3 src/agenthotspot_mcp/server.py
```

### With Claude Desktop

Add this configuration to your Claude Desktop config file:

**macOS:** `~/Library/Application\ Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "agenthotspot": {
      "command": "python3",
      "args": ["-m", "agenthotspot_mcp"]
    }
  }
}
```

### With LangChain

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def main():
    client = MultiServerMCPClient({
        "agenthotspot": {
            "transport": "stdio",
            "command": "python3",
            "args": ["-m", "agenthotspot_mcp"],
        }
    })
    tools = await client.get_tools()
    print(tools)

    # Remaining code ... 
    # (see examples/langchain_example.py for full agent example)

asyncio.run(main())
```


---

## 🗂️ Project Structure

```
agenthotspot-mcp/
├── src/
│   └── agenthotspot_mcp/
│       ├── __init__.py      # Package exports
│       ├── __main__.py      # Entry point
│       └── server.py        # MCP server implementation
├── examples/
│   ├── claude_config.json   # Claude Desktop config example
│   └── langchain_example.py # Python langchain usage example
├── pyproject.toml           # Package configuration
├── requirements.txt         # Dependencies
├── LICENSE                  # MIT License
├── CONTRIBUTING.md          # Contribution guidelines
└── README.md               # This file
```

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- 🌐 **Website:** [agenthotspot.com](https://agenthotspot.com)
- 📦 **Connectors:** [Browse 6,000+ connectors](https://agenthotspot.com/connectors)
- 🐦 **Twitter/X:** [@agenthotspot](https://x.com/agenthotspot)
- 🐙 **GitHub:** [AgentHotspot](https://github.com/AgentHotspot)
- 📧 **Support:** [support@agenthotspot.com](mailto:support@agenthotspot.com)

---

<p align="center">
  <strong>Built with ❤️ by the <a href="https://agenthotspot.com">AgentHotspot</a> team</strong>
</p>

<p align="center">
  <a href="https://agenthotspot.com">
    <img src="https://img.shields.io/badge/Discover_MCP_Connectors-AgentHotspot-blue?style=for-the-badge" alt="Discover Connectors">
  </a>
</p>

<!-- mcp-name: io.github.agenthotspot/agenthotspot-mcp -->