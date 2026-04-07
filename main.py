import argparse
import sys
import re
from simulator import DCASimulator
from onchain_utils import execute_swap, check_wallet_status, collect_fee

SUPPORTED_TOKENS = ["USDC", "USDT", "ETH", "OKB", "BTC", "WETH"]

def interactive_token_menu(prompt="Select Token"):
    print(f"\n[Interactive] {prompt}")
    for i, t in enumerate(SUPPORTED_TOKENS, 1):
        print(f"  {i}. {t}")
    while True:
        choice = input("Select number or token name (or press Enter to skip): ").strip().upper()
        if not choice:
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(SUPPORTED_TOKENS):
            return SUPPORTED_TOKENS[int(choice)-1]
        elif choice in SUPPORTED_TOKENS:
            return choice
        print("Invalid choice. Try again.")

def parse_nl_query_local(query: str, cli_token_in: str = None, cli_token_out: str = None, force_menu: bool = False):
    """
    100% Local Smart NLP Parser recognizing English and Thai tokens safely.
    Respects CLI Flags first, falls back to NLP, and offers interactive menu if triggered.
    """
    query = query.lower()
    print(f"[*] Executing Local LLM/NLP Pipeline to parse: '{query}'")
    
    # 1. Extract Amount
    amt_match = re.search(r'(\d+(?:\.\d+)?)', query)
    amount = float(amt_match.group(1)) if amt_match else 10.0
    
    # 2. Tokens: CLI Flags -> NLP Parser -> Interactive Menu
    nlp_tokens = re.findall(r'\b(usdc|usdt|okb|eth|btc|weth)\b', query)
    
    token_in = cli_token_in if cli_token_in else (nlp_tokens[0].upper() if len(nlp_tokens) > 0 else None)
    token_out = cli_token_out if cli_token_out else (nlp_tokens[1].upper() if len(nlp_tokens) > 1 else None)
    
    if force_menu:
        print("\n[!] Coin Selection Menu Triggered (No CLI token flags provided)")
        token_in = interactive_token_menu(f"Select the SOURCE token (Current: {token_in or 'None'}):") or token_in or "USDC"
        token_out = interactive_token_menu(f"Select the ASSET token to DCA (Current: {token_out or 'None'}):") or token_out or "ETH"
    elif not token_in or not token_out:
        print("\n[!] Tokens missing from NLP query. Launching Interactive Menu...")
        token_in = token_in or interactive_token_menu("Select Token In:") or "USDC"
        token_out = token_out or interactive_token_menu("Select Token Out:") or "ETH"
    
    # 3. Extract Interval
    interval_days = 7
    if re.search(r'ทุก\s*(\d+)\s*วัน|every\s*(\d+)\s*day', query):
        m = re.search(r'(?:ทุก|every)\s*(\d+)\s*(?:วัน|day)', query)
        if m: interval_days = int(m.group(1))
    elif 'week' in query or 'สัปดาห์' in query:
        interval_days = 7
    elif 'month' in query or 'เดือน' in query:
        interval_days = 30
        
    # 4. Extract Duration
    duration_days = 30
    if re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(days?|วัน)', query):
        m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:days?|วัน)', query)
        if m: duration_days = int(m.group(1))
    elif re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(week|สัปดาห์)', query):
        m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:week|สัปดาห์)', query)
        if m: duration_days = int(m.group(1)) * 7
    elif re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(month|เดือน)', query):
        m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:month|เดือน)', query)
        if m: duration_days = int(m.group(1)) * 30
    elif re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(years?|ปี)', query):
        m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:years?|ปี)', query)
        if m: duration_days = int(m.group(1)) * 365
        
    return {
        "token_in": token_in,
        "token_out": token_out,
        "amount": amount,
        "interval": interval_days,
        "duration": duration_days
    }

def main():
    parser = argparse.ArgumentParser(description="XLayer DCA Guardian - AI Agent for OKX Auto-Investing")
    parser.add_argument("--query", type=str, default="DCA 50 every 7 days for 30 days", help="Natural language DCA instructions")
    parser.add_argument("--token-in", type=str, default=None, help="Explicitly define source token (e.g. USDC)")
    parser.add_argument("--token-out", type=str, default=None, help="Explicitly define destination token (e.g. ETH)")
    parser.add_argument("--execute", action="store_true", help="Perform real swap execution if safety checks pass")
    parser.add_argument("--testnet", action="store_true", help="Run strictly on X Layer Testnet (Chain Id 195)")
    
    args = parser.parse_args()
    
    # If no token flags are provided, launch the interactive user coin selection menu!
    force_menu = (args.token_in is None and args.token_out is None)
    
    params = parse_nl_query_local(
        query=args.query, 
        cli_token_in=args.token_in, 
        cli_token_out=args.token_out,
        force_menu=force_menu
    )
    
    is_testnet = args.testnet
    chain_id = 195 if is_testnet else 196
    
    sim = DCASimulator(
        token_in=params["token_in"],
        token_out=params["token_out"],
        dca_amount=params["amount"],
        interval_days=params["interval"],
        duration_days=params["duration"],
        is_testnet=is_testnet
    )
    
    sim.run()
    
    if args.execute:
        print("[!] Execution flag passed. Running safety bounds and TEE check.")
        if not check_wallet_status():
            print("Execution aborted due to authorization. Run `onchainos wallet login` first.")
            return
            
        print(f"\n======================================")
        print(f"         REAL EXECUTION CHECK          ")
        print(f"======================================")
        network_str = "X LAYER TESTNET (Fake tokens)" if is_testnet else "X LAYER MAINNET (REAL FUNDS)"
        print(f"Selected Pair: {params['token_in']} -> {params['token_out']}")
        print(f"Action: Swap {params['amount']} {params['token_in']} -> {params['token_out']}")
        print(f"Chain: {network_str}")
        confirm = input(f"\nAre you sure you want to execute swap on {network_str} now? (y/n): ")
        if confirm.lower() == 'y':
            success, output = execute_swap(
                token_in=params["token_in"], 
                token_out=params["token_out"], 
                max_amount_in=str(params["amount"]),
                chain_id=chain_id
            )
            if success:
                collect_fee(amount=params["amount"], currency=params["token_in"], is_testnet=is_testnet)
        else:
            print("Execution manually aborted by user.")
    else:
        print("Note: Ran in SIMULATION mode. Append `--execute` to perform the actual on-chain transaction.")

if __name__ == "__main__":
    main()
