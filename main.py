import argparse
import re
import os
import json
from simulator import DCASimulator
from onchain_utils import execute_swap, check_wallet_status, collect_fee
from config import IS_TESTNET, ACTIVE_CHAIN_ID, SUPPORTED_TOKENS

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
    NLP Parser recognizing English and Thai tokens safely.
    Attempts to use Gemma 4 via Ollama Cloud API, falls back to Regex if unavailable.
    """
    query_lower = query.lower()
    print(f"[*] Executing NLP Pipeline to parse: '{query}'")
    
    token_in = None
    token_out = None
    amount = 10.0
    interval_days = 7
    duration_days = 30
    parser_used = "regex"  # default; overridden to "ollama" on success

    # 1. Attempt Gemma 4 via Ollama Python Client
    try:
        from ollama import chat
        print("    -> Attempting Gemma 4 via Ollama...")
        prompt = f"""
        Extract the following parameters from the DCA query into a JSON object.
        Keys: "token_in" (string, e.g. USDC), "token_out" (string, e.g. ETH), "amount" (float), "interval" (days as int), "duration" (days as int).
        If something is missing, omit it or use reasonable defaults. 
        Query: "{query}"
        Respond ONLY with a valid minified JSON object and no markdown blocks.
        """
        
        response = chat(
            model='gemma4',
            messages=[{'role': 'user', 'content': prompt}],
        )
        
        content = response.message.content.strip()
        # Clean Markdown if hallucinated
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        parsed_data = json.loads(content)
        token_in = parsed_data.get("token_in")
        token_out = parsed_data.get("token_out")
        amount = float(parsed_data.get("amount", amount))
        interval_days = int(parsed_data.get("interval", interval_days))
        duration_days = int(parsed_data.get("duration", duration_days))
        print("    -> Successfully parsed via Gemma 4!")
        parser_used = "ollama"

        # Formatting corrections
        if token_in: token_in = token_in.upper()
        if token_out: token_out = token_out.upper()

    except Exception as e:
        print(f"    -> Gemma 4 API failed ({e}). Falling back to Regex Parser...")
        parser_used = "regex"

        # Strip $ currency symbol before amount extraction
        query_stripped = re.sub(r'\$(\d+(?:\.\d+)?)', r'\1', query_lower)

        # Extract amount
        amt_match = re.search(r'(\d+(?:\.\d+)?)', query_stripped)
        amount = float(amt_match.group(1)) if amt_match else 10.0

        # Token extraction: handle "buy X with Y" word order first
        # Use query_stripped so $50 doesn't block the match; optionally skip the number
        buy_with_match = re.search(r'buy\s+(\w+)\s+with\s+(?:\d+(?:\.\d+)?\s+)?(\w+)', query_stripped)
        if buy_with_match:
            token_out = buy_with_match.group(1).upper()
            token_in = buy_with_match.group(2).upper()
        else:
            nlp_tokens = re.findall(r'\b(usdc|usdt|okb|eth|btc|weth|sol|bnb|dai|matic|link|wokb)\b', query_lower)
            token_in = nlp_tokens[0].upper() if len(nlp_tokens) > 0 else None
            token_out = nlp_tokens[1].upper() if len(nlp_tokens) > 1 else None

        # Extract interval — order matters: specific patterns before generic
        if re.search(r'\bdaily\b', query_lower):
            interval_days = 1
        elif re.search(r'\bbiweekly\b|\bevery other week\b', query_lower):
            interval_days = 14
        elif re.search(r'\bquarterly\b', query_lower):
            interval_days = 90
        elif re.search(r'every\s*(\d+)\s*weeks?', query_lower):
            m = re.search(r'every\s*(\d+)\s*weeks?', query_lower)
            if m: interval_days = int(m.group(1)) * 7
        elif re.search(r'ทุก\s*(\d+)\s*วัน|every\s*(\d+)\s*day', query_lower):
            m = re.search(r'(?:ทุก|every)\s*(\d+)\s*(?:วัน|day)', query_lower)
            if m: interval_days = int(m.group(1))
        elif 'week' in query_lower or 'สัปดาห์' in query_lower:
            interval_days = 7
        elif 'month' in query_lower or 'เดือน' in query_lower:
            interval_days = 30

        # Extract duration
        if re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(days?|วัน)', query_lower):
            m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:days?|วัน)', query_lower)
            if m: duration_days = int(m.group(1))
        elif re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(week|สัปดาห์)', query_lower):
            m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:week|สัปดาห์)', query_lower)
            if m: duration_days = int(m.group(1)) * 7
        elif re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(month|เดือน)', query_lower):
            m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:month|เดือน)', query_lower)
            if m: duration_days = int(m.group(1)) * 30
        elif re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(years?|ปี)', query_lower):
            m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:years?|ปี)', query_lower)
            if m: duration_days = int(m.group(1)) * 365
            
    # Apply CLI Overrides
    token_in = cli_token_in if cli_token_in else token_in
    token_out = cli_token_out if cli_token_out else token_out

    # Handle Missing Tokens Interactively
    if force_menu:
        print("\n[!] Coin Selection Menu Triggered (No CLI token flags provided)")
        token_in = interactive_token_menu(f"Select the SOURCE token (Current: {token_in or 'None'}):") or token_in or "USDC"
        token_out = interactive_token_menu(f"Select the ASSET token to DCA (Current: {token_out or 'None'}):") or token_out or "ETH"
    elif not token_in or not token_out:
        print("\n[!] Tokens missing from NLP query. Launching Interactive Menu...")
        token_in = token_in or interactive_token_menu("Select Token In:") or "USDC"
        token_out = token_out or interactive_token_menu("Select Token Out:") or "ETH"
    
    # Validation
    if amount <= 0:
        return {"error": "Amount must be greater than zero.", "parser": parser_used}

    if token_in and token_out and token_in.upper() == token_out.upper():
        return {"error": "Token In and Token Out cannot be the same asset.", "parser": parser_used}

    if interval_days > duration_days:
        interval_days, duration_days = duration_days, interval_days
        print(f"[*] Auto-corrected: interval and duration were transposed ({interval_days}d interval, {duration_days}d duration).")

    return {
        "token_in": token_in.upper() if token_in else "USDC",
        "token_out": token_out.upper() if token_out else "ETH",
        "amount": amount,
        "interval": interval_days,
        "duration": duration_days,
        "parser": parser_used,
    }

def main():
    parser = argparse.ArgumentParser(description="XLayer DCA Guardian - AI Agent for OKX Auto-Investing")
    parser.add_argument("--query", type=str, default="DCA 50 every 7 days for 30 days", help="Natural language DCA instructions")
    parser.add_argument("--token-in", type=str, default=None, help="Explicitly define source token (e.g. USDC)")
    parser.add_argument("--token-out", type=str, default=None, help="Explicitly define destination token (e.g. ETH)")
    parser.add_argument("--execute", action="store_true", help="Perform real swap execution if safety checks pass")
    
    args = parser.parse_args()
    
    # If no token flags are provided, launch the interactive user coin selection menu!
    force_menu = (args.token_in is None and args.token_out is None)
    
    params = parse_nl_query_local(
        query=args.query, 
        cli_token_in=args.token_in, 
        cli_token_out=args.token_out,
        force_menu=force_menu
    )
    
    is_testnet = IS_TESTNET
    chain_id = ACTIVE_CHAIN_ID
    
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
