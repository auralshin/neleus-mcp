from __future__ import annotations

from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from neleus_mcp.tools.docs import list_docs, read_doc, search_docs
from neleus_mcp.tools.markets import analyze_market, get_order_book, list_markets, scan_markets
from neleus_mcp.tools.trading import (
    cancel_order,
    get_fills,
    get_open_orders,
    place_limit_order,
    place_market_order,
)

MarketScope = Literal["perps", "all-perps", "hip3", "spot", "hip4"]
AnalysisScope = Literal["perps", "all-perps", "hip3", "spot"]
Timeframe = Literal["1m", "5m", "15m", "1h", "4h", "1d"]
ScanSort = Literal["score", "change", "volatility", "rsi"]

# MCP tool annotations — used by clients to decide whether to auto-approve calls.
# readOnlyHint=True means the tool does not mutate state.
# openWorldHint=True means the tool makes outbound network calls.
READ_ONLY_NETWORK = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)
READ_ONLY_LOCAL = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
WRITE_NETWORK = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)

mcp = FastMCP(
    "neleus",
    instructions=(
        "Neleus gives you real-time Hyperliquid market data and optional live trading. "
        "Market tools (list, analyze, scan, book) require no credentials. "
        "Docs tools (list_docs, search_docs, read_doc) fetch the Neleus documentation from the web. "
        "Trading tools (place, cancel, fills, open_orders) require HYPERLIQUID_SIGNER_PRIVATE_KEY. "
        "HIP-4 outcome markets are testnet-only — always pass testnet=True for that scope. "
        "Never submit a live order without the user's explicit confirmation."
    ),
)


# ---------------------------------------------------------------------------
# Market tools
# ---------------------------------------------------------------------------

@mcp.tool(annotations=READ_ONLY_NETWORK)
def neleus_list_markets(
    scope: MarketScope = "perps",
    dex: str = "",
    search: str = "",
    testnet: bool = False,
) -> list[dict]:
    """
    List Hyperliquid markets for a given scope.

    scope:   perps | all-perps | hip3 | spot | hip4
    dex:     DEX name for HIP-3 (e.g. "flx", "xyz"); empty for all other scopes
    search:  text filter on market name
    testnet: required for hip4 scope
    """
    return list_markets(scope=scope, dex=dex or None, search=search or None, testnet=testnet)


@mcp.tool(annotations=READ_ONLY_NETWORK)
def neleus_analyze_market(
    symbol: str,
    dex: str = "",
    timeframe: Timeframe = "1h",
    lookback_bars: Annotated[int, Field(ge=20, le=1000)] = 200,
    testnet: bool = False,
) -> dict:
    """
    Technical analysis on a single Hyperliquid market.

    Returns RSI, trend, Bollinger bands, support/resistance, and a directional bias.

    symbol:        e.g. "BTC", "ETH-PERP", "GAS"
    dex:           DEX name for HIP-3 markets (e.g. "flx")
    timeframe:     candle interval
    lookback_bars: candle count (min 20, max 1000)
    """
    return analyze_market(
        symbol=symbol,
        dex=dex or None,
        timeframe=timeframe,
        lookback_bars=lookback_bars,
        testnet=testnet,
    )


@mcp.tool(annotations=READ_ONLY_NETWORK)
def neleus_scan_markets(
    scope: MarketScope = "perps",
    dex: str = "",
    symbols: str = "",
    search: str = "",
    timeframe: Timeframe = "1h",
    lookback_bars: Annotated[int, Field(ge=20, le=1000)] = 200,
    max_markets: Annotated[int, Field(ge=1, le=50)] = 8,
    limit: Annotated[int, Field(ge=1, le=50)] = 8,
    sort_by: ScanSort = "score",
    testnet: bool = False,
) -> list[dict]:
    """
    Rank a bounded set of Hyperliquid markets by composite TA score.

    symbols:     comma-separated override list (skips catalog fetch)
    sort_by:     score | change | volatility | rsi
    max_markets: hard cap on markets analyzed per call
    limit:       rows returned after ranking
    """
    return scan_markets(
        scope=scope,
        dex=dex or None,
        symbols=symbols or None,
        search=search or None,
        timeframe=timeframe,
        lookback_bars=lookback_bars,
        max_markets=max_markets,
        limit=limit,
        sort_by=sort_by,
        testnet=testnet,
    )


@mcp.tool(annotations=READ_ONLY_NETWORK)
def neleus_get_order_book(
    symbol: str,
    scope: AnalysisScope = "all-perps",
    dex: str = "",
    depth: Annotated[int, Field(ge=1, le=50)] = 10,
    testnet: bool = False,
) -> dict:
    """
    L2 order book snapshot for a Hyperliquid market.

    Returns top-N bids/asks, best bid/ask, spread, mid price, and imbalance ratio.

    depth: number of price levels to return per side (default 10, max 50)
    """
    return get_order_book(symbol=symbol, scope=scope, dex=dex or None, depth=depth, testnet=testnet)


# ---------------------------------------------------------------------------
# Docs tools
# ---------------------------------------------------------------------------

@mcp.tool(annotations=READ_ONLY_LOCAL)
def neleus_list_docs() -> list[dict]:
    """List all Neleus documentation pages (fetched from auralshin.github.io/neleus)."""
    return list_docs()


@mcp.tool(annotations=READ_ONLY_LOCAL)
def neleus_search_docs(
    query: str,
    limit: Annotated[int, Field(ge=1, le=10)] = 5,
) -> list[dict]:
    """
    Search the Neleus documentation (fetched from auralshin.github.io/neleus).

    Returns matching pages with section, route, summary, and an excerpt.
    """
    return search_docs(query=query, limit=limit)


@mcp.tool(annotations=READ_ONLY_LOCAL)
def neleus_read_doc(route: str) -> dict:
    """
    Read a Neleus documentation page by route.

    Example routes: index, getting-started/installation, cli/market, configuration
    """
    return read_doc(route=route)


# ---------------------------------------------------------------------------
# Trading tools
# ---------------------------------------------------------------------------

@mcp.tool(annotations=WRITE_NETWORK)
def neleus_place_limit_order(
    coin: str,
    is_buy: bool,
    size: Annotated[float, Field(gt=0)],
    price: Annotated[float, Field(gt=0)],
    testnet: bool = False,
) -> dict:
    """
    Place a limit order on Hyperliquid. Requires HYPERLIQUID_SIGNER_PRIVATE_KEY.

    Confirm all parameters with the user before calling — orders are submitted immediately.

    coin:    asset name, e.g. "BTC", "ETH"
    is_buy:  True = buy/long, False = sell/short
    size:    order size in base asset units
    price:   limit price in USD
    """
    return place_limit_order(coin=coin, is_buy=is_buy, size=size, price=price, testnet=testnet)


@mcp.tool(annotations=WRITE_NETWORK)
def neleus_place_market_order(
    coin: str,
    is_buy: bool,
    size: Annotated[float, Field(gt=0)],
    slippage_bps: Annotated[int, Field(ge=1, le=1000)] = 50,
    testnet: bool = False,
) -> dict:
    """
    Place a market order on Hyperliquid. Requires HYPERLIQUID_SIGNER_PRIVATE_KEY.

    Executes immediately at market price. Confirm with the user first.

    slippage_bps: max allowed slippage in basis points (default 50 = 0.5%)
    """
    return place_market_order(coin=coin, is_buy=is_buy, size=size, slippage_bps=slippage_bps, testnet=testnet)


@mcp.tool(annotations=WRITE_NETWORK)
def neleus_cancel_order(
    coin: str,
    order_id: Annotated[int, Field(gt=0)],
    testnet: bool = False,
) -> dict:
    """
    Cancel an open order by ID. Requires HYPERLIQUID_SIGNER_PRIVATE_KEY.

    Use neleus_get_open_orders to retrieve order IDs.
    """
    return cancel_order(coin=coin, order_id=order_id, testnet=testnet)


@mcp.tool(annotations=READ_ONLY_NETWORK)
def neleus_get_open_orders(
    limit: Annotated[int, Field(ge=1, le=200)] = 50,
    testnet: bool = False,
) -> list[dict]:
    """Open orders for the configured account. Requires HYPERLIQUID_SIGNER_PRIVATE_KEY."""
    return get_open_orders(limit=limit, testnet=testnet)


@mcp.tool(annotations=READ_ONLY_NETWORK)
def neleus_get_fills(
    limit: Annotated[int, Field(ge=1, le=200)] = 50,
    testnet: bool = False,
) -> list[dict]:
    """Recent fills for the configured account. Requires HYPERLIQUID_SIGNER_PRIVATE_KEY."""
    return get_fills(limit=limit, testnet=testnet)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
