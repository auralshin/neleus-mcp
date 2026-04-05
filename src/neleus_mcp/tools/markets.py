from __future__ import annotations

from typing import Any


def _entry_summary(entry: Any) -> dict:
    # Minimal fields for browsing. Use analyze_market for full detail on a single market.
    d = entry.to_dict() if hasattr(entry, "to_dict") else vars(entry)
    out: dict = {"name": d.get("name"), "scope": d.get("scope"), "market_type": d.get("market_type")}
    if d.get("dex"):
        out["dex"] = d["dex"]
    if d.get("max_leverage"):
        out["max_leverage"] = d["max_leverage"]
    if d.get("collateral_token"):
        out["collateral_token"] = d["collateral_token"]
    if d.get("full_name"):
        out["full_name"] = d["full_name"]
    return out


def list_markets(
    scope: str = "perps",
    dex: str | None = None,
    search: str | None = None,
    testnet: bool = False,
) -> list[dict]:
    from neleus.market import list_markets as _list  # noqa: PLC0415

    catalog = _list(scope=scope, dex=dex, search=search, testnet=testnet)
    return [_entry_summary(e) for e in catalog.entries]


_ANALYSIS_FIELDS = (
    "symbol", "timeframe", "last_price", "price_change_pct",
    "rsi", "trend", "momentum", "bias",
    "support", "resistance", "bollinger_upper", "bollinger_lower",
    "volatility_pct",
)


def analyze_market(
    symbol: str,
    scope: str = "all-perps",
    dex: str | None = None,
    timeframe: str = "1h",
    lookback_bars: int = 200,
    testnet: bool = False,
) -> dict:
    from neleus.market import analyze_market as _analyze  # noqa: PLC0415

    analysis = _analyze(
        symbol=symbol,
        scope=scope,
        dex=dex,
        timeframe=timeframe,
        lookback_bars=lookback_bars,
        testnet=testnet,
    )
    d = analysis.to_dict()
    return {k: d[k] for k in _ANALYSIS_FIELDS if k in d}


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
    rows = []
    for row in scan.rows:
        d = row.to_dict() if hasattr(row, "to_dict") else vars(row)
        # Keep only the fields Claude needs to present a ranked scan table
        rows.append({k: d[k] for k in ("symbol", "score", "rsi", "price_change_pct", "volatility_pct", "trend", "bias") if k in d})
    return rows


def get_order_book(
    symbol: str,
    scope: str = "all-perps",
    dex: str | None = None,
    depth: int = 10,
    testnet: bool = False,
) -> dict:
    from neleus.market import resolve_market_entry  # noqa: PLC0415
    from neleus import HyperliquidClient, HyperliquidConfig  # noqa: PLC0415

    entry = resolve_market_entry(symbol, scope=scope, dex=dex, testnet=testnet)
    config = HyperliquidConfig.testnet() if testnet else HyperliquidConfig.mainnet()
    client = HyperliquidClient(config)
    book = client.fetch_l2_book(entry.request_symbol)
    if book is None:
        raise ValueError(f"No order book data for {symbol}")

    bids = [{"price": lvl.price, "size": lvl.size} for lvl in book.bids]
    asks = [{"price": lvl.price, "size": lvl.size} for lvl in book.asks]
    best_bid = bids[0]["price"] if bids else None
    best_ask = asks[0]["price"] if asks else None
    spread = round(best_ask - best_bid, 6) if best_bid is not None and best_ask is not None else None
    mid = round((best_bid + best_ask) / 2, 6) if best_bid is not None and best_ask is not None else None
    total_bid_size = round(sum(b["size"] for b in bids), 4)
    total_ask_size = round(sum(a["size"] for a in asks), 4)
    imbalance = (
        round((total_bid_size - total_ask_size) / (total_bid_size + total_ask_size), 4)
        if (total_bid_size + total_ask_size) > 0
        else 0.0
    )

    return {
        "symbol": symbol,
        "bids": bids[:depth],
        "asks": asks[:depth],
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": spread,
        "mid": mid,
        "imbalance": imbalance,
    }
