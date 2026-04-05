"""
Neleus MCP Server

Exposes Hyperliquid market data and trading operations as MCP tools
that Claude can call directly. All heavy work runs in the Rust neleus_core
extension — this file only registers tools and marshals results.

Market tools require no credentials.
Trading tools require HYPERLIQUID_SIGNER_PRIVATE_KEY and
HYPERLIQUID_ACCOUNT_ADDRESS environment variables.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from neleus_mcp.tools.markets import (
    analyze_market,
    get_order_book,
    list_markets,
    scan_markets,
)
from neleus_mcp.tools.trading import (
    cancel_order,
    get_fills,
    get_open_orders,
    place_limit_order,
    place_market_order,
)

mcp = FastMCP(
    "neleus",
    instructions=(
        "Neleus gives you real-time Hyperliquid market data and optional live trading. "
        "Market tools (list, analyze, scan, book) work without credentials. "
        "Trading tools (place, cancel, fills, open_orders) require "
        "HYPERLIQUID_SIGNER_PRIVATE_KEY and HYPERLIQUID_ACCOUNT_ADDRESS. "
        "HIP-4 outcome markets are testnet-only — always pass testnet=True for that scope. "
        "Never submit a live order without the user's explicit confirmation."
    ),
)


# ---------------------------------------------------------------------------
# Market tools
# ---------------------------------------------------------------------------

@mcp.tool()
def neleus_list_markets(
    scope: str = "perps",
    dex: str = "",
    search: str = "",
    testnet: bool = False,
) -> list[dict]:
    """
    List Hyperliquid markets for a given scope.

    scope:   perps | all-perps | hip3 | spot | hip4
    dex:     DEX name for HIP-3 (e.g. "flx", "xyz"); leave blank for others
    search:  optional text filter on market name
    testnet: required for hip4 scope
    """
    return list_markets(
        scope=scope,
        dex=dex or None,
        search=search or None,
        testnet=testnet,
    )


@mcp.tool()
def neleus_analyze_market(
    symbol: str,
    scope: str = "all-perps",
    dex: str = "",
    timeframe: str = "1h",
    lookback_bars: int = 200,
    testnet: bool = False,
) -> dict:
    """
    Run a full technical analysis on a single Hyperliquid market.

    Returns RSI, trend, SMA/EMA, Bollinger bands, support/resistance,
    volatility, and a directional bias read.

    symbol:        e.g. "BTC", "ETH-PERP", "GAS"
    scope:         perps | all-perps | hip3 | spot
    dex:           HIP-3 dex name when scope=hip3
    timeframe:     1m | 5m | 15m | 1h | 4h | 1d
    lookback_bars: number of candles to fetch (min 20)
    """
    return analyze_market(
        symbol=symbol,
        scope=scope,
        dex=dex or None,
        timeframe=timeframe,
        lookback_bars=lookback_bars,
        testnet=testnet,
    )


@mcp.tool()
def neleus_scan_markets(
    scope: str = "perps",
    dex: str = "",
    symbols: str = "",
    search: str = "",
    timeframe: str = "1h",
    lookback_bars: int = 200,
    max_markets: int = 8,
    limit: int = 8,
    sort_by: str = "score",
    testnet: bool = False,
) -> list[dict]:
    """
    Rank a bounded set of Hyperliquid markets by composite TA score.

    symbols:     comma-separated list, overrides catalog selection
    sort_by:     score | change | volatility | rsi
    max_markets: cap on how many markets are analyzed
    limit:       how many ranked rows to return
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


@mcp.tool()
def neleus_get_order_book(
    symbol: str,
    scope: str = "all-perps",
    dex: str = "",
    testnet: bool = False,
) -> dict:
    """
    Fetch the current L2 order book snapshot for a Hyperliquid market.

    Returns top 20 bids and asks, best bid/ask, spread, mid price,
    and order book imbalance ratio.
    """
    return get_order_book(
        symbol=symbol,
        scope=scope,
        dex=dex or None,
        testnet=testnet,
    )


# ---------------------------------------------------------------------------
# Trading tools
# ---------------------------------------------------------------------------

@mcp.tool()
def neleus_place_limit_order(
    coin: str,
    is_buy: bool,
    size: float,
    price: float,
    testnet: bool = False,
) -> dict:
    """
    Place a limit order on Hyperliquid.

    Requires HYPERLIQUID_SIGNER_PRIVATE_KEY and HYPERLIQUID_ACCOUNT_ADDRESS.
    Always confirm order parameters with the user before calling this tool.

    coin:    asset name, e.g. "BTC", "ETH"
    is_buy:  True for buy/long, False for sell/short
    size:    order size in base asset units
    price:   limit price in USD
    testnet: use testnet (recommended for testing)
    """
    return place_limit_order(coin=coin, is_buy=is_buy, size=size, price=price, testnet=testnet)


@mcp.tool()
def neleus_place_market_order(
    coin: str,
    is_buy: bool,
    size: float,
    slippage_bps: int = 50,
    testnet: bool = False,
) -> dict:
    """
    Place a market order on Hyperliquid.

    Requires HYPERLIQUID_SIGNER_PRIVATE_KEY and HYPERLIQUID_ACCOUNT_ADDRESS.
    Always confirm with the user before calling. Market orders execute immediately.

    slippage_bps: max allowed slippage in basis points (default 50 = 0.5%)
    """
    return place_market_order(
        coin=coin,
        is_buy=is_buy,
        size=size,
        slippage_bps=slippage_bps,
        testnet=testnet,
    )


@mcp.tool()
def neleus_cancel_order(
    coin: str,
    order_id: int,
    testnet: bool = False,
) -> dict:
    """
    Cancel an open order by numeric order ID.

    Requires HYPERLIQUID_SIGNER_PRIVATE_KEY and HYPERLIQUID_ACCOUNT_ADDRESS.
    Use neleus_get_open_orders to find the order_id first.
    """
    return cancel_order(coin=coin, order_id=order_id, testnet=testnet)


@mcp.tool()
def neleus_get_open_orders(testnet: bool = False) -> list[dict]:
    """
    Return all currently open orders for the configured Hyperliquid account.

    Requires HYPERLIQUID_SIGNER_PRIVATE_KEY and HYPERLIQUID_ACCOUNT_ADDRESS.
    """
    return get_open_orders(testnet=testnet)


@mcp.tool()
def neleus_get_fills(limit: int = 50, testnet: bool = False) -> list[dict]:
    """
    Return recent fill history for the configured Hyperliquid account.

    Requires HYPERLIQUID_SIGNER_PRIVATE_KEY and HYPERLIQUID_ACCOUNT_ADDRESS.
    limit: number of fills to return (max 200)
    """
    return get_fills(limit=limit, testnet=testnet)


# ---------------------------------------------------------------------------

def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
