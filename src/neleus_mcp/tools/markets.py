"""
Market data tools — no credentials required.

All heavy work (HTTP, parsing, TA calculations) runs inside the Rust
neleus_core extension. These functions are thin dispatch wrappers.
"""

from __future__ import annotations

from typing import Any


def _entry_to_dict(entry: Any) -> dict:
    return entry.to_dict() if hasattr(entry, "to_dict") else vars(entry)


def list_markets(
    scope: str = "perps",
    dex: str | None = None,
    search: str | None = None,
    testnet: bool = False,
) -> list[dict]:
    """
    Return all markets for a given scope.

    scope:   perps | all-perps | hip3 | spot | hip4
    dex:     DEX name for HIP-3 markets (e.g. "flx", "xyz")
    search:  optional text filter applied to market names
    testnet: must be True for hip4 scope
    """
    from neleus.market import list_markets as _list  # noqa: PLC0415

    catalog = _list(scope=scope, dex=dex, search=search, testnet=testnet)
    return [_entry_to_dict(e) for e in catalog.entries]


def analyze_market(
    symbol: str,
    scope: str = "all-perps",
    dex: str | None = None,
    timeframe: str = "1h",
    lookback_bars: int = 200,
    testnet: bool = False,
) -> dict:
    """
    Run a full technical analysis on a single market.

    Returns RSI, trend, SMA/EMA structure, Bollinger bands,
    support/resistance levels, volatility, and a directional read.
    """
    from neleus.market import analyze_market as _analyze  # noqa: PLC0415

    analysis = _analyze(
        symbol=symbol,
        scope=scope,
        dex=dex,
        timeframe=timeframe,
        lookback_bars=lookback_bars,
        testnet=testnet,
    )
    return analysis.to_dict()


def scan_markets(
    scope: str = "perps",
    dex: str | None = None,
    symbols: str | None = None,
    search: str | None = None,
    timeframe: str = "1h",
    lookback_bars: int = 200,
    max_markets: int = 8,
    limit: int = 8,
    sort_by: str = "score",
    testnet: bool = False,
) -> list[dict]:
    """
    Rank a bounded set of markets by composite TA score.

    symbols: comma-separated symbol list, overrides catalog selection
    sort_by: score | change | volatility | rsi
    """
    from neleus.market import scan_markets as _scan  # noqa: PLC0415

    symbol_list = [s.strip() for s in symbols.split(",")] if symbols else None
    scan = _scan(
        scope=scope,
        dex=dex,
        symbols=symbol_list,
        search=search,
        timeframe=timeframe,
        lookback_bars=lookback_bars,
        max_markets=max_markets,
        limit=limit,
        sort_by=sort_by,
        testnet=testnet,
    )
    return [vars(row) if not hasattr(row, "to_dict") else row.to_dict() for row in scan.rows]


def get_order_book(
    symbol: str,
    scope: str = "all-perps",
    dex: str | None = None,
    testnet: bool = False,
) -> dict:
    """
    Fetch the current L2 order book snapshot for a market.

    Returns bids, asks, best bid/ask, spread, and imbalance.
    """
    from neleus.market import resolve_market_entry  # noqa: PLC0415
    from neleus import HyperliquidClient, HyperliquidConfig  # noqa: PLC0415

    entry = resolve_market_entry(symbol, scope=scope, dex=dex, testnet=testnet)
    config = HyperliquidConfig.testnet() if testnet else HyperliquidConfig.mainnet()
    client = HyperliquidClient(config)
    book = client.fetch_l2_book(entry.request_symbol)
    if book is None:
        return {"error": f"No order book data for {symbol}"}

    bids = [{"price": lvl.price, "size": lvl.size} for lvl in book.bids]
    asks = [{"price": lvl.price, "size": lvl.size} for lvl in book.asks]
    best_bid = bids[0]["price"] if bids else None
    best_ask = asks[0]["price"] if asks else None
    spread = round(best_ask - best_bid, 6) if best_bid and best_ask else None
    mid = round((best_bid + best_ask) / 2, 6) if best_bid and best_ask else None
    total_bid_size = round(sum(b["size"] for b in bids), 4)
    total_ask_size = round(sum(a["size"] for a in asks), 4)
    imbalance = (
        round((total_bid_size - total_ask_size) / (total_bid_size + total_ask_size), 4)
        if (total_bid_size + total_ask_size) > 0
        else 0.0
    )

    return {
        "symbol": symbol,
        "bids": bids[:20],
        "asks": asks[:20],
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": spread,
        "mid": mid,
        "imbalance": imbalance,
    }
