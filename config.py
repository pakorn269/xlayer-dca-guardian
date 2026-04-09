import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Environment options: 'testnet' or 'mainnet'
ENVIRONMENT = os.getenv("ENVIRONMENT", "testnet").lower()
# Safe Mode flag: if true, forces the app into Testnet mode ignoring 'ENVIRONMENT'
REQUIRE_TESTNET = os.getenv("REQUIRE_TESTNET", "true").lower() == "true"

# Network Identifiers
CHAIN_ID_TESTNET = 195
CHAIN_ID_MAINNET = 196

# Effective Network State
if REQUIRE_TESTNET and ENVIRONMENT != "testnet":
    print("[🛡️ GUARDIAN] Safe Mode is ACTIVE (REQUIRE_TESTNET=true). Forcing execution to Testnet.")

IS_TESTNET = True if REQUIRE_TESTNET else (ENVIRONMENT == "testnet")
ACTIVE_CHAIN_ID = CHAIN_ID_TESTNET if IS_TESTNET else CHAIN_ID_MAINNET

# Protocol Settings
PROTOCOL_FEE_PERCENT = 0.1  # Fixed server-side; not user-configurable

# App Constraints
SUPPORTED_TOKENS = ["USDC", "USDT", "ETH", "OKB", "BTC", "WETH", "DAI", "LINK", "SOL", "WOKB"]
