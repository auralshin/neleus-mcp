from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    private_key: str | None
    account_address: str | None
    testnet: bool

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            private_key=os.environ.get("HYPERLIQUID_SIGNER_PRIVATE_KEY"),
            account_address=os.environ.get("HYPERLIQUID_ACCOUNT_ADDRESS"),
            testnet=os.environ.get("HYPERLIQUID_TESTNET", "false").lower() in ("1", "true", "yes"),
        )

    @property
    def has_credentials(self) -> bool:
        return bool(self.private_key)
