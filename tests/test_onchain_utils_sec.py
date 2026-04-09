from onchain_utils import is_safe_arg, execute_swap
from config import CHAIN_ID_MAINNET

def test_is_safe_arg():
    # Valid arguments
    assert is_safe_arg("USDC") is True
    assert is_safe_arg("0x1234") is True
    assert is_safe_arg("100.5") is True

    # Invalid arguments (potential injections)
    assert is_safe_arg("-flag") is False
    assert is_safe_arg("--chain") is False
    assert is_safe_arg("rm -rf") is False
    assert is_safe_arg("token; ls") is False
    assert is_safe_arg("token|grep") is False
    assert is_safe_arg("$(whoami)") is False
    assert is_safe_arg("`whoami`") is False

def test_execute_swap_validation_blocks_injection():
    # Simulate a mainnet execution (where real logic runs, since testnet 195 has mocked early returns)
    token_in = "USDC"
    token_out = "ETH"
    max_amount_in = "-50" # invalid amount

    success, msg = execute_swap(token_in, token_out, max_amount_in, CHAIN_ID_MAINNET)
    assert success is False
    assert "Invalid input arguments detected" in msg

    success, msg = execute_swap("-flag", token_out, "50", CHAIN_ID_MAINNET)
    assert success is False
    assert "Invalid input arguments detected" in msg

    success, msg = execute_swap("USDC", "$(whoami)", "50", CHAIN_ID_MAINNET)
    assert success is False
    assert "Invalid input arguments detected" in msg

def test_execute_swap_validation_blocks_unsupported_tokens():
    # Attempt to swap using a token not in SUPPORTED_TOKENS list
    token_in = "DOGE"
    token_out = "ETH"
    max_amount_in = "50"

    success, msg = execute_swap(token_in, token_out, max_amount_in, CHAIN_ID_MAINNET)
    assert success is False
    assert "Unsupported token detected" in msg

    success, msg = execute_swap("USDC", "PEPE", "50", CHAIN_ID_MAINNET)
    assert success is False
    assert "Unsupported token detected" in msg
