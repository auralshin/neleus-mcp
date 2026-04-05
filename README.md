# neleus-mcp

MCP server that exposes [Neleus](https://github.com/auralshin/neleus) Hyperliquid tools to Claude. Gives Claude real-time market data and optional live trading directly from the conversation.

## Tools

### Market tools (no credentials needed)

| Tool | Description |
|---|---|
| `neleus_list_markets` | List markets by scope: perps, all-perps, hip3, spot, hip4 |
| `neleus_analyze_market` | Full TA analysis — RSI, trend, Bollinger bands, support/resistance |
| `neleus_scan_markets` | Rank a bounded set of markets by composite TA score |
| `neleus_get_order_book` | L2 order book snapshot with spread and imbalance |

### Docs tools (no credentials needed)

| Tool | Description |
|---|---|
| `neleus_list_docs` | List the local Neleus documentation pages |
| `neleus_search_docs` | Search the local Neleus docs corpus |
| `neleus_read_doc` | Read a specific Neleus documentation page by route |

### Trading tools (credentials required)

| Tool | Description |
|---|---|
| `neleus_place_limit_order` | Place a limit order |
| `neleus_place_market_order` | Place a market order |
| `neleus_cancel_order` | Cancel an open order by ID |
| `neleus_get_open_orders` | List all open orders |
| `neleus_get_fills` | Fetch recent fill history |

## Installation

Neleus requires the Rust extension built from source. Install Neleus first:

```bash
# In the neleus repo
python3 -m venv .venv
source .venv/bin/activate
pip install maturin
VIRTUAL_ENV=$PWD/.venv .venv/bin/maturin develop --release -m crates/pybridge/Cargo.toml
pip install -e python/
```

Then install neleus-mcp into the same environment:

```bash
pip install neleus-mcp
```

Or for development (from this repo):

```bash
pip install -e .
```

## Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "neleus": {
      "command": "/path/to/.venv/bin/neleus-mcp",
      "env": {
        "HYPERLIQUID_TESTNET": "false"
      }
    }
  }
}
```

For live trading, add credentials:

```json
{
  "mcpServers": {
    "neleus": {
      "command": "/path/to/.venv/bin/neleus-mcp",
      "env": {
        "HYPERLIQUID_SIGNER_PRIVATE_KEY": "0x...",
        "HYPERLIQUID_ACCOUNT_ADDRESS": "0x...",
        "HYPERLIQUID_TESTNET": "false"
      }
    }
  }
}
```

### Claude Code (project-local)

Add to `.claude/settings.json` in your project:

```json
{
  "mcpServers": {
    "neleus": {
      "command": "/path/to/.venv/bin/neleus-mcp",
      "env": {
        "NELEUS_DOCS_REPO": "/path/to/neleus"
      }
    }
  }
}
```

If `NELEUS_DOCS_REPO` is omitted, the server also tries the common local-dev layout where `neleus` and `neleus-mcp` are sibling directories.

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `HYPERLIQUID_SIGNER_PRIVATE_KEY` | Trading only | Wallet private key (`0x...`) |
| `HYPERLIQUID_ACCOUNT_ADDRESS` | No | Optional compatibility metadata for delegated-account flows |
| `HYPERLIQUID_TESTNET` | No | `true` to default all tools to testnet |
| `NELEUS_DOCS_REPO` | No | Path to the local `neleus` repository root |
| `NELEUS_DOCS_MANIFEST_PATH` | No | Path to `docs/assets/ai/page-manifest.json` |

## Usage examples

Once connected, Claude can answer questions like:

- *"What are the top 5 perp markets by TA score right now?"*
- *"Analyze BTC on the 4h timeframe."*
- *"Show me the order book for ETH-PERP."*
- *"List all HIP-3 markets on the flx DEX."*
- *"Search the Neleus docs for database config."*
- *"Read the `cli/market` docs page."*
- *"What are my open orders?"* (requires credentials)
- *"Place a limit buy of 0.001 BTC at 95000."* (requires credentials + explicit confirmation)

## Notes

- All market data is fetched via the Rust Hyperliquid adapter inside `neleus_core`.
- Docs are read locally from the Neleus MkDocs AI manifest (`docs/assets/ai/page-manifest.json`).
- HIP-4 outcome markets are testnet-only — pass `testnet=true` for that scope.
- Trading tools will raise `PermissionError` if credentials are not set.
- Claude will always ask for confirmation before placing or cancelling orders.
