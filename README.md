# neleus-mcp

MCP server exposing [Neleus](https://github.com/auralshin/neleus) Hyperliquid tools to Claude.

## Tools

### Market (no credentials)

| Tool | Description |
|---|---|
| `neleus_list_markets` | List markets by scope: perps, all-perps, hip3, spot, hip4 |
| `neleus_analyze_market` | TA analysis — RSI, trend, Bollinger bands, support/resistance |
| `neleus_scan_markets` | Rank markets by composite TA score |
| `neleus_get_order_book` | L2 order book snapshot with spread and imbalance |

### Docs (no credentials)

| Tool | Description |
|---|---|
| `neleus_list_docs` | List Neleus documentation pages |
| `neleus_search_docs` | Search the Neleus docs |
| `neleus_read_doc` | Read a documentation page by route |

### Trading (requires `HYPERLIQUID_SIGNER_PRIVATE_KEY`)

| Tool | Description |
|---|---|
| `neleus_place_limit_order` | Place a limit order |
| `neleus_place_market_order` | Place a market order |
| `neleus_cancel_order` | Cancel an open order by ID |
| `neleus_get_open_orders` | List open orders |
| `neleus_get_fills` | Recent fill history |

## Installation

### 1. Install uv (once)

`uvx` is required to run MCP servers without managing Python environments manually.

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# or via Homebrew
brew install uv
```

### 2. Add to Claude Code

```bash
claude mcp add neleus -- uvx neleus-mcp
```

With trading credentials:

```bash
claude mcp add neleus \
  -e HYPERLIQUID_SIGNER_PRIVATE_KEY=0x... \
  -e HYPERLIQUID_TESTNET=false \
  -- uvx neleus-mcp
```

### 2. Add to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "neleus": {
      "command": "uvx",
      "args": ["neleus-mcp"]
    }
  }
}
```

With trading credentials:

```json
{
  "mcpServers": {
    "neleus": {
      "command": "uvx",
      "args": ["neleus-mcp"],
      "env": {
        "HYPERLIQUID_SIGNER_PRIVATE_KEY": "0x...",
        "HYPERLIQUID_TESTNET": "false"
      }
    }
  }
}
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `HYPERLIQUID_SIGNER_PRIVATE_KEY` | Trading only | Wallet private key (`0x...`) |
| `HYPERLIQUID_TESTNET` | No | `true` to use testnet for all tools |
| `NELEUS_DOCS_URL` | No | Override the docs manifest URL |
| `NELEUS_DOCS_MANIFEST_PATH` | No | Use a local manifest file (offline/dev) |

## Notes

- HIP-4 outcome markets require `testnet=true`.
- Trading tools raise `PermissionError` if `HYPERLIQUID_SIGNER_PRIVATE_KEY` is not set.
- Docs are fetched from the live [Neleus docs site](https://auralshin.github.io/neleus/) and cached for 1 hour.
