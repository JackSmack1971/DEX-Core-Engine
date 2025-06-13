from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List

from web3.contract import Contract

from dex_protocols.base import BaseDEXProtocol, LiquidityInfo
from exceptions import DexError
from tokens.detect import (
    ERC20_ABI,
    TokenInspectionError,
    TokenType,
    detect_token_type,
    gas_multiplier,
    get_token_balance,
)
from web3_service import Web3Service


UNISWAP_V3_QUOTER_ABI: List[Dict[str, Any]] = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenIn", "type": "address"},
            {"internalType": "address", "name": "tokenOut", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

UNISWAP_V3_ROUTER_ABI: List[Dict[str, Any]] = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "internalType": "struct ISwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple",
            }
        ],
        "name": "exactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "function",
    }
]


class UniswapV3(BaseDEXProtocol):
    """Adapter for interacting with Uniswap V3."""

    def __init__(
        self,
        web3_service: Web3Service,
        quoter_address: str,
        router_address: str,
        fee_tier: int = 3000,
        gas_limit: int = 250000,
    ) -> None:
        super().__init__()
        self.web3_service = web3_service
        self.fee_tier = fee_tier
        self.gas_limit = gas_limit
        self.quoter: Contract = web3_service.get_contract(
            quoter_address, UNISWAP_V3_QUOTER_ABI
        )
        self.router: Contract = web3_service.get_contract(
            router_address, UNISWAP_V3_ROUTER_ABI
        )

    async def _get_quote(self, token_in: str, token_out: str, amount_in: int) -> float:
        try:
            func = self.quoter.functions.quoteExactInputSingle(
                token_in, token_out, self.fee_tier, amount_in, 0
            ).call
            amount_out = await asyncio.to_thread(func)
            return float(amount_out)
        except Exception as exc:  # noqa: BLE001
            self.logger.error("UniswapV3 quote error: %s", exc)
            raise DexError("quote failed") from exc

    async def _execute_swap(self, amount_in: int, route: List[str]) -> str:
        token_in, token_out = route[0], route[-1]
        try:
            contract = self.web3_service.get_contract(token_out, ERC20_ABI)
            try:
                token_type = await detect_token_type(contract)
            except TokenInspectionError:
                token_type = TokenType.ERC20
            multiplier = gas_multiplier(token_type)
            balance_before = await get_token_balance(
                contract, self.web3_service.account.address
            )

            params = {
                "tokenIn": token_in,
                "tokenOut": token_out,
                "fee": self.fee_tier,
                "recipient": self.web3_service.account.address,
                "deadline": int(time.time()) + 300,
                "amountIn": amount_in,
                "amountOutMinimum": 0,
                "sqrtPriceLimitX96": 0,
            }
            tx = self.router.functions.exactInputSingle(params).build_transaction(
                {
                    "from": self.web3_service.account.address,
                    "gas": int(self.gas_limit * multiplier),
                    "gasPrice": self.web3_service.web3.eth.gas_price,
                }
            )
            receipt = await self.web3_service.sign_and_send_transaction(tx)
            balance_after = await get_token_balance(
                contract, self.web3_service.account.address
            )
            if balance_after <= balance_before:
                raise DexError("token balance check failed")
            return receipt["transactionHash"].hex()
        except Exception as exc:  # noqa: BLE001
            self.logger.error("UniswapV3 swap error: %s", exc)
            raise DexError("swap failed") from exc

    async def _get_best_route(
        self, token_in: str, token_out: str, amount_in: int
    ) -> List[str]:
        return [token_in, token_out]

    async def get_liquidity_info(
        self, token_in: str, token_out: str, amount_in: int
    ) -> LiquidityInfo:
        base_quote = await self._get_quote(token_in, token_out, 1)
        large_quote = await self._get_quote(token_in, token_out, amount_in)
        expected = base_quote * amount_in
        impact = 0.0 if expected == 0 else abs(expected - large_quote) / expected * 100
        return LiquidityInfo(liquidity=float(amount_in) * 10, price_impact=impact)


__all__ = ["UniswapV3"]
