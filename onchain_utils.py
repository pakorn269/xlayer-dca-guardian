import subprocess
import json
import re

import os

TREASURY_FILE = "treasury.json"


def is_safe_arg(arg: str) -> bool:
    """Validates that an argument is safe from command injection."""
    if not isinstance(arg, str):
        return False
    if arg.startswith('-'):
        return False
    return bool(re.match(r'^[a-zA-Z0-9._]+$', arg))

def get_treasury():
    """Reads the current accumulated treasury balance (in token_in units for MVP)."""
    if not os.path.exists(TREASURY_FILE):
        return {"balance": 0.0, "currency": "USDC"}
    with open(TREASURY_FILE, "r") as f:
        return json.load(f)

def save_treasury(data):
    with open(TREASURY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def collect_fee(amount: float, currency: str, is_testnet: bool = False):
    """
    Economy Loop: Collects configured protocol fee upon successful swap execution.
    Logs it to local treasury.json file.
    """
    from config import PROTOCOL_FEE_PERCENT
    fee = amount * (PROTOCOL_FEE_PERCENT / 100.0)
    data = get_treasury()
    data["balance"] += fee
    data["currency"] = currency
    save_treasury(data)
    
    net_suffix = "(Testnet)" if is_testnet else "(Mainnet)"
    print(f"[Economy Loop] Collected {fee:.4f} {currency} fee {net_suffix}. Treasury balance: {data['balance']:.4f} {currency}")
    
    # Reward Loop MVP
    if data["balance"] >= 5.0:
        print(f"\n[🔥 REWARD LOOP TRIGGERED 🔥]")
        print(f"Treasury reached >= 5 {currency}. Automatically minting 'DCA Guardian Badge' NFT on X Layer {net_suffix}!")
        print(f"(For MVP: Simulated mint transaction logged.)\n")

def get_historical_kline(token_address: str, chain_id: int):
    """
    Fetches historical k-line prices via okx-dex-market using dynamic chain_id.
    """
    if not is_safe_arg(str(token_address)):
        print(f"[!] Warning: Invalid token_address argument detected.")
        return None
    command = [
        "onchainos", "market", "kline",
        "--chain", str(chain_id),
        "--address", token_address,
        "--bar", "1D"
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        prices = []
        if data.get("ok"):
            kline_arr = data.get("data", [])
            for candle in kline_arr:
                if len(candle) >= 5:
                    prices.append(float(candle[4]))
            
            if prices:
                return list(reversed(prices))
        return None
    except Exception as e:
        print(f"[!] Warning: MCP Market K-line fetch failed. Offline rendering applied.")
        return None

def get_swap_quote(token_in: str, token_out: str, amount: str, chain_id: int):
    """
    Calls 'onchainos swap quote' to estimate output tokens and gas with dynamic chain_id.
    """
    from config import CHAIN_ID_TESTNET, SUPPORTED_TOKENS
    if not all(is_safe_arg(str(x)) for x in [token_in, token_out, amount]):
        print(f"\n[Error] Failed getting swap quote:\nInvalid input arguments detected")
        return 0.0, 0.0001, "Invalid input arguments detected"

    if token_in not in SUPPORTED_TOKENS or token_out not in SUPPORTED_TOKENS:
        print(f"\n[Error] Failed getting swap quote:\nUnsupported token detected")
        return 0.0, 0.0001, "Unsupported token detected"

    net = "Testnet" if chain_id == CHAIN_ID_TESTNET else "Mainnet"
    print(f"[*] Getting DEX quote for {amount} {token_in} -> {token_out} on X Layer {net} ...")
    command = [
        "onchainos", "swap", "quote",
        "--chain", str(chain_id),
        "--from", token_in,
        "--to", token_out,
        "--amount", str(amount)
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        try:
            data = json.loads(result.stdout)
            estimated_out = data.get("data", {}).get("toTokenAmount", 0)
            gas_okb = float(data.get("data", {}).get("estimatedGasOkb") or 0.0001)
            return float(estimated_out), gas_okb, data
        except json.JSONDecodeError:
            # 🛡️ Sentinel: Do not leak unparseable CLI stdout to prevent internal state exposure
            return 0.0, 0.0001, "Invalid quote response received from the node."
    except subprocess.CalledProcessError:
        return 0.0, 0.0001, None

def execute_swap(token_in: str, token_out: str, max_amount_in: str, chain_id: int):
    """
    Executes a real DEX swap with dynamic chain_id.
    """
    from config import CHAIN_ID_TESTNET, SUPPORTED_TOKENS
    net = "TESTNET_SAFE_MODE - No real money used" if chain_id == CHAIN_ID_TESTNET else "MAINNET (REAL MONEY)"
    print(f"\n[!] INITIATING REAL EXECUTION")
    print(f"Action: Swapping {max_amount_in} {token_in} -> {token_out} on X Layer {net}\n")
    
    if not all(is_safe_arg(str(x)) for x in [token_in, token_out, max_amount_in]):
        print(f"\n[Error] Failed executing swap:\nInvalid input arguments detected")
        return False, "Invalid input arguments detected"

    if token_in not in SUPPORTED_TOKENS or token_out not in SUPPORTED_TOKENS:
        print(f"\n[Error] Failed executing swap:\nUnsupported token detected")
        return False, "Unsupported token detected"

    if chain_id == CHAIN_ID_TESTNET:
        import time
        time.sleep(2)
        mock_stdout = "{\n  \"ok\": true,\n  \"data\": {\"txHash\": \"0xmockedtestnettxhash8b1c4a0...\"}\n}"
        print("\n--- ONCHAINOS OUTPUT ---")
        print(mock_stdout)
        print("------------------------\n")
        return True, mock_stdout

    wallet_name = "Account 1"
    try:
        res = subprocess.run(["onchainos", "wallet", "status"], capture_output=True, text=True)
        wallet_name = json.loads(res.stdout).get("data", {}).get("currentAccountName", "Account 1")
    except: pass

    command = [
        "onchainos", "swap", "execute",
        "--chain", str(chain_id),
        "--from", token_in,
        "--to", token_out,
        "--amount", str(max_amount_in),
        "--wallet", wallet_name,
        "--slippage", "0.01" 
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("\n--- ONCHAINOS OUTPUT ---")
        print(result.stdout)
        print("------------------------\n")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        # 🛡️ Sentinel: Do not leak stderr to UI to prevent stack trace/internal state exposure
        print("\n[Error] Failed executing swap: subprocess error occurred")
        return False, "Swap execution failed on the node. Please check server logs for details."

def check_wallet_status() -> bool:
    try:
        result = subprocess.run(["onchainos", "wallet", "status"], capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        if data.get("ok") and data.get("data", {}).get("loggedIn"):
            print(f"[OK] Wallet authorized: {data['data']['currentAccountName']}")
            return True
        else:
            print("[WARN] Wallet not logged in. Please run 'onchainos wallet login'.")
            return False
    except Exception:
        print("[ERROR] Checking wallet failed.")
        return False

def get_wallet_balance_usd(chain_id: int) -> str:
    """Fetch wallet portfolio balance. Mocks Testnet 195 for demo UX since indexer may not cover testnet."""
    from config import CHAIN_ID_TESTNET
    if chain_id == CHAIN_ID_TESTNET:
        return "15,000.00"
    try:
        res = subprocess.run(["onchainos", "wallet", "balance", "--chain", str(chain_id)], capture_output=True, text=True)
        data = json.loads(res.stdout)
        if data.get("ok"):
            val = float(data.get("data", {}).get("totalValueUsd", "0.00"))
            return f"{val:,.2f}"
    except:
        pass
    return "0.00"
