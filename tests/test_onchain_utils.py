import pytest
from unittest.mock import patch
from onchain_utils import collect_fee

@patch('onchain_utils.save_treasury')
@patch('onchain_utils.get_treasury')
def test_collect_fee_basic(mock_get_treasury, mock_save_treasury):
    # Setup mock data
    mock_get_treasury.return_value = {"balance": 10.0, "currency": "USDC"}

    # Call the function
    collect_fee(amount=100.0, currency="USDC", fee_percent=0.1)

    # Verify the fee calculation and state update
    # fee should be 100 * (0.1 / 100) = 0.1
    # new balance should be 10.0 + 0.1 = 10.1
    expected_data = {"balance": 10.1, "currency": "USDC"}

    # Assert save_treasury was called with expected data
    mock_save_treasury.assert_called_once_with(expected_data)

@patch('onchain_utils.save_treasury')
@patch('onchain_utils.get_treasury')
def test_collect_fee_testnet(mock_get_treasury, mock_save_treasury, capfd):
    mock_get_treasury.return_value = {"balance": 0.0, "currency": "USDC"}

    collect_fee(amount=200.0, currency="USDT", fee_percent=0.5, is_testnet=True)

    # fee: 200 * (0.5 / 100) = 1.0
    expected_data = {"balance": 1.0, "currency": "USDT"}
    mock_save_treasury.assert_called_once_with(expected_data)

    # check that it printed Testnet
    out, err = capfd.readouterr()
    assert "(Testnet)" in out
    assert "Collected 1.0000 USDT" in out

@patch('onchain_utils.save_treasury')
@patch('onchain_utils.get_treasury')
def test_collect_fee_mainnet(mock_get_treasury, mock_save_treasury, capfd):
    mock_get_treasury.return_value = {"balance": 0.0, "currency": "USDC"}

    collect_fee(amount=500.0, currency="DAI", fee_percent=1.0, is_testnet=False)

    # fee: 500 * (1.0 / 100) = 5.0
    expected_data = {"balance": 5.0, "currency": "DAI"}
    mock_save_treasury.assert_called_once_with(expected_data)

    # check that it printed Mainnet
    out, err = capfd.readouterr()
    assert "(Mainnet)" in out
    assert "Collected 5.0000 DAI" in out

@patch('onchain_utils.save_treasury')
@patch('onchain_utils.get_treasury')
def test_collect_fee_reward_trigger(mock_get_treasury, mock_save_treasury, capfd):
    # Setup state so that new balance is exactly 5.0
    mock_get_treasury.return_value = {"balance": 4.5, "currency": "USDC"}

    collect_fee(amount=50.0, currency="USDC", fee_percent=1.0) # fee = 0.5

    out, err = capfd.readouterr()
    assert "REWARD LOOP TRIGGERED" in out
