import pytest
import json
import os
import subprocess
from unittest.mock import patch, mock_open, MagicMock
from onchain_utils import (
    get_treasury,
    save_treasury,
    collect_fee,
    get_historical_kline,
    get_swap_quote,
    execute_swap,
    check_wallet_status,
    get_wallet_balance_usd
)

# 1. Treasury Management Tests

def test_get_treasury_file_not_exists():
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False
        result = get_treasury()
        assert result == {"balance": 0.0, "currency": "USDC"}

def test_get_treasury_file_exists():
    mock_data = {"balance": 10.5, "currency": "USDT"}
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            result = get_treasury()
            assert result == mock_data

def test_save_treasury():
    mock_data = {"balance": 15.0, "currency": "ETH"}
    m = mock_open()
    with patch("builtins.open", m):
        save_treasury(mock_data)
        m.assert_called_once_with("treasury.json", "w")
        # Check if json.dump was called with the correct data
        # Since we are mocking open, we can check what was written
        handle = m()
        written_data = "".join(call.args[0] for call in handle.write.call_args_list)
        assert json.loads(written_data) == mock_data

def test_collect_fee(capsys):
    initial_data = {"balance": 1.0, "currency": "USDC"}
    with patch("onchain_utils.get_treasury", return_value=initial_data):
        with patch("onchain_utils.save_treasury") as mock_save:
            with patch("config.PROTOCOL_FEE_PERCENT", 0.1):
                collect_fee(100.0, "USDC")
                # 100 * 0.1 / 100 = 0.1
                # New balance should be 1.0 + 0.1 = 1.1
                expected_data = {"balance": 1.1, "currency": "USDC"}
                mock_save.assert_called_once_with(expected_data)

                captured = capsys.readouterr()
                assert "Collected 0.1000 USDC fee" in captured.out
                assert "Treasury balance: 1.1000 USDC" in captured.out

def test_collect_fee_reward_trigger(capsys):
    # Initial balance 4.95, collect 0.1 fee -> 5.05 (triggers reward)
    initial_data = {"balance": 4.95, "currency": "USDC"}
    with patch("onchain_utils.get_treasury", return_value=initial_data):
        with patch("onchain_utils.save_treasury"):
            with patch("config.PROTOCOL_FEE_PERCENT", 0.1):
                collect_fee(100.0, "USDC")
                captured = capsys.readouterr()
                assert "REWARD LOOP TRIGGERED" in captured.out
                assert "DCA Guardian Badge" in captured.out

# 2. Onchain Interaction Tests

def test_get_historical_kline_success():
    get_historical_kline.cache_clear()
    mock_stdout = json.dumps({
        "ok": True,
        "data": [
            [0, 0, 0, 0, "100.0"],
            [0, 0, 0, 0, "105.0"],
            [0, 0, 0, 0, "110.0"]
        ]
    })
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_stdout)
        result = get_historical_kline("0xAddress", 196)
        # prices are at index 4, and reversed
        # [100.0, 105.0, 110.0] -> [110.0, 105.0, 100.0]
        assert result == [110.0, 105.0, 100.0]

def test_get_historical_kline_failure():
    get_historical_kline.cache_clear()
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("error")
        result = get_historical_kline("0xAddress", 196)
        assert result is None

def test_get_swap_quote_success():
    get_swap_quote.cache_clear()
    mock_stdout = json.dumps({
        "ok": True,
        "data": {
            "toTokenAmount": "500.0",
            "estimatedGasOkb": "0.0002"
        }
    })
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_stdout)
        estimated_out, gas_okb, data = get_swap_quote("USDC", "ETH", "100", 196)
        assert estimated_out == 500.0
        assert gas_okb == 0.0002
        assert data["ok"] is True

def test_get_swap_quote_error():
    get_swap_quote.cache_clear()
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        estimated_out, gas_okb, data = get_swap_quote("USDC", "ETH", "100", 196)
        assert estimated_out == 0.0
        assert gas_okb == 0.0001
        assert data is None

def test_execute_swap_testnet():
    # chain_id 195 should use mock behavior
    with patch("time.sleep"): # avoid delay in tests
        success, stdout = execute_swap("USDC", "ETH", "100", 195)
        assert success is True
        assert "txHash" in stdout
        assert "mockedtestnettxhash" in stdout

def test_execute_swap_mainnet_success():
    mock_stdout = json.dumps({"ok": True, "data": {"txHash": "0xhash"}})
    expected_stdout = json.dumps({"ok": True, "data": {"txHash": "0xhash"}}, indent=2)
    with patch("subprocess.run") as mock_run:
        # First call to check wallet status (optional depending on implementation)
        # Actually execute_swap calls wallet status first to get wallet name
        mock_run.side_effect = [
            MagicMock(stdout=json.dumps({"data": {"currentAccountName": "TestAcc"}})), # wallet status
            MagicMock(stdout=mock_stdout) # swap execute
        ]
        success, stdout = execute_swap("USDC", "ETH", "100", 196)
        assert success is True
        assert stdout == expected_stdout

def test_check_wallet_status_true():
    mock_stdout = json.dumps({"ok": True, "data": {"loggedIn": True, "currentAccountName": "TestAcc"}})
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_stdout)
        assert check_wallet_status() is True

def test_check_wallet_status_false():
    mock_stdout = json.dumps({"ok": True, "data": {"loggedIn": False}})
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_stdout)
        assert check_wallet_status() is False

def test_get_wallet_balance_usd_testnet():
    # chain_id 195
    assert get_wallet_balance_usd(195) == "15,000.00"

def test_get_wallet_balance_usd_mainnet_success():
    mock_stdout = json.dumps({"ok": True, "data": {"totalValueUsd": "1234.56"}})
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_stdout)
        assert get_wallet_balance_usd(196) == "1,234.56"
