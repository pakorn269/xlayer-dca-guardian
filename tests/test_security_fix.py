import unittest
from unittest.mock import patch, MagicMock
import os
import json
import config
from onchain_utils import collect_fee

class TestSecurityFix(unittest.TestCase):
    def setUp(self):
        self.treasury_file = "test_treasury.json"
        if os.path.exists(self.treasury_file):
            os.remove(self.treasury_file)

    def tearDown(self):
        if os.path.exists(self.treasury_file):
            os.remove(self.treasury_file)

    @patch("onchain_utils.TREASURY_FILE", "test_treasury.json")
    @patch("onchain_utils.get_treasury")
    @patch("onchain_utils.save_treasury")
    def test_collect_fee_uses_config_value(self, mock_save, mock_get):
        # Initial treasury state
        mock_get.return_value = {"balance": 0.0, "currency": "USDC"}

        amount = 1000.0
        currency = "USDC"

        # Call collect_fee. Note: fee_percent parameter is no longer accepted.
        collect_fee(amount=amount, currency=currency, is_testnet=True)

        # Expected fee calculation
        expected_fee = amount * (config.PROTOCOL_FEE_PERCENT / 100.0)

        # Verify that save_treasury was called with the correct increment
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][0]
        self.assertEqual(saved_data["balance"], expected_fee)
        self.assertEqual(saved_data["currency"], currency)

    @patch("onchain_utils.TREASURY_FILE", "test_treasury.json")
    def test_collect_fee_integration(self):
        # Real file integration test
        if os.path.exists(self.treasury_file):
            os.remove(self.treasury_file)

        amount = 500.0
        currency = "ETH"

        collect_fee(amount=amount, currency=currency, is_testnet=False)

        with open(self.treasury_file, "r") as f:
            data = json.load(f)

        expected_fee = amount * (config.PROTOCOL_FEE_PERCENT / 100.0)
        self.assertAlmostEqual(data["balance"], expected_fee)
        self.assertEqual(data["currency"], "ETH")

if __name__ == "__main__":
    unittest.main()
