"""
Live trading tools — require HYPERLIQUID_SIGNER_PRIVATE_KEY and
HYPERLIQUID_ACCOUNT_ADDRESS environment variables.

All order signing and submission runs inside the Rust HyperliquidTrader.
These wrappers only validate credentials and marshal results to plain dicts.
"""

from __future__ import annotations

from typing import Any

from neleus_mcp.config import Config


def _require_credentials(config: Config) -> None:
    if not config.has_credentials:
        raise PermissionError(
            "Trading tools require HYPERLIQUID_SIGNER_PRIVATE_KEY and "
            "HYPERLIQUID_ACCOUNT_ADDRESS environment variables."
        )


def _result_to_dict(result: Any) -> dict:
    return result.to_dict() if hasattr(result, "to_dict") else vars(result)


def place_limit_order(
    coin: str,
    is_buy: bool,
    size: float,
    price: float,
    testnet: bool | None = None,
) -> dict:
    """
    Place a limit order on Hyperliquid.

    coin:    asset name, e.g. "BTC", "ETH"
    is_buy:  True for buy/long, False for sell/short
    size:    order size in base asset units
    price:   limit price in USD
    testnet: overrides HYPERLIQUID_TESTNET env var when provided
    """
    from neleus import HyperliquidTrader  # noqa: PLC0415

    config = Config.from_env()
    _require_credentials(config)
    use_testnet = testnet if testnet is not None else config.testnet
    trader = HyperliquidTrader(config.private_key, testnet=use_testnet)
    result = trader.place_limit_order(coin, is_buy, size, price)
    return _result_to_dict(result)


def place_market_order(
    coin: str,
    is_buy: bool,
    size: float,
    slippage_bps: int = 50,
    testnet: bool | None = None,
) -> dict:
    """
    Place a market order on Hyperliquid.

    slippage_bps: maximum allowed slippage in basis points (default 50 = 0.5%)
    """
    from neleus import HyperliquidTrader  # noqa: PLC0415

    config = Config.from_env()
    _require_credentials(config)
    use_testnet = testnet if testnet is not None else config.testnet
    trader = HyperliquidTrader(config.private_key, testnet=use_testnet)
    result = trader.place_market_order(coin, is_buy, size, slippage_bps=slippage_bps)
    return _result_to_dict(result)


def cancel_order(
    coin: str,
    order_id: int,
    testnet: bool | None = None,
) -> dict:
    """Cancel an open order by its numeric order ID."""
    from neleus import HyperliquidTrader  # noqa: PLC0415

    config = Config.from_env()
    _require_credentials(config)
    use_testnet = testnet if testnet is not None else config.testnet
    trader = HyperliquidTrader(config.private_key, testnet=use_testnet)
    result = trader.cancel_order(coin, order_id)
    return _result_to_dict(result)


def get_open_orders(testnet: bool | None = None) -> list[dict]:
    """Return all open orders for the configured account."""
    from neleus import HyperliquidTrader  # noqa: PLC0415

    config = Config.from_env()
    _require_credentials(config)
    use_testnet = testnet if testnet is not None else config.testnet
    trader = HyperliquidTrader(config.private_key, testnet=use_testnet)
    return [_result_to_dict(o) for o in trader.get_open_orders()]


def get_fills(limit: int = 50, testnet: bool | None = None) -> list[dict]:
    """Return recent fill history for the configured account."""
    from neleus import HyperliquidTrader  # noqa: PLC0415

    config = Config.from_env()
    _require_credentials(config)
    use_testnet = testnet if testnet is not None else config.testnet
    trader = HyperliquidTrader(config.private_key, testnet=use_testnet)
    return [_result_to_dict(f) for f in trader.get_fills(limit=limit)]
