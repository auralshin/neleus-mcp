from __future__ import annotations

from typing import Any

from neleus_mcp.config import Config


def _require_credentials(config: Config) -> None:
    if not config.has_credentials:
        raise PermissionError("Trading tools require HYPERLIQUID_SIGNER_PRIVATE_KEY.")


def _result_to_dict(result: Any) -> dict:
    return result.to_dict() if hasattr(result, "to_dict") else vars(result)


def place_limit_order(
    coin: str,
    is_buy: bool,
    size: float,
    price: float,
    testnet: bool | None = None,
) -> dict:
    from neleus import HyperliquidTrader  # noqa: PLC0415

    config = Config.from_env()
    _require_credentials(config)
    use_testnet = testnet if testnet is not None else config.testnet
    trader = HyperliquidTrader(config.private_key, testnet=use_testnet)
    return _result_to_dict(trader.place_limit_order(coin, is_buy, size, price))


def place_market_order(
    coin: str,
    is_buy: bool,
    size: float,
    slippage_bps: int = 50,
    testnet: bool | None = None,
) -> dict:
    from neleus import HyperliquidTrader  # noqa: PLC0415

    config = Config.from_env()
    _require_credentials(config)
    use_testnet = testnet if testnet is not None else config.testnet
    trader = HyperliquidTrader(config.private_key, testnet=use_testnet)
    return _result_to_dict(trader.place_market_order(coin, is_buy, size, slippage_bps=slippage_bps))


def cancel_order(
    coin: str,
    order_id: int,
    testnet: bool | None = None,
) -> dict:
    from neleus import HyperliquidTrader  # noqa: PLC0415

    config = Config.from_env()
    _require_credentials(config)
    use_testnet = testnet if testnet is not None else config.testnet
    trader = HyperliquidTrader(config.private_key, testnet=use_testnet)
    return _result_to_dict(trader.cancel_order(coin, order_id))


def get_open_orders(testnet: bool | None = None) -> list[dict]:
    from neleus import HyperliquidTrader  # noqa: PLC0415

    config = Config.from_env()
    _require_credentials(config)
    use_testnet = testnet if testnet is not None else config.testnet
    trader = HyperliquidTrader(config.private_key, testnet=use_testnet)
    return [_result_to_dict(o) for o in trader.get_open_orders()]


def get_fills(limit: int = 50, testnet: bool | None = None) -> list[dict]:
    from neleus import HyperliquidTrader  # noqa: PLC0415

    config = Config.from_env()
    _require_credentials(config)
    use_testnet = testnet if testnet is not None else config.testnet
    trader = HyperliquidTrader(config.private_key, testnet=use_testnet)
    return [_result_to_dict(f) for f in trader.get_fills(limit=limit)]
