import pytest
from onchain_utils import get_swap_quote, execute_swap
from config import CHAIN_ID_TESTNET

def test_get_swap_quote_invalid_token():
    # Provide an invalid token_in
    quote, gas, data = get_swap_quote("INVALID", "ETH", "100", CHAIN_ID_TESTNET)
    assert quote == 0.0
    assert gas == 0.0001
    assert data is None

    # Provide an invalid token_out
    quote, gas, data = get_swap_quote("USDC", "INVALID", "100", CHAIN_ID_TESTNET)
    assert quote == 0.0
    assert gas == 0.0001
    assert data is None

def test_execute_swap_invalid_token():
    # Provide an invalid token_in
    success, msg = execute_swap("INVALID", "ETH", "100", CHAIN_ID_TESTNET)
    assert success is False
    assert "Unsupported token" in msg

    # Provide an invalid token_out
    success, msg = execute_swap("USDC", "INVALID", "100", CHAIN_ID_TESTNET)
    assert success is False
    assert "Unsupported token" in msg
