import pytest
from unittest.mock import MagicMock

from tokens import detect


class MockContract:
    def __init__(self, funcs):
        self._funcs = funcs

    def get_function_by_name(self, name):
        if name in self._funcs:
            return object()
        raise ValueError()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "funcs,expected",
    [
        ({"granularity"}, detect.TokenType.ERC777),
        ({"rebase"}, detect.TokenType.REBASING),
        ({"fee"}, detect.TokenType.FEE_ON_TRANSFER),
        (set(), detect.TokenType.ERC20),
    ],
)
async def test_detect_token_type(funcs, expected):
    contract = MockContract(funcs)
    assert await detect.detect_token_type(contract) is expected
