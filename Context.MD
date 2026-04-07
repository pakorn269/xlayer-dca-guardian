**✅ ได้เลยครับ! นี่คือ Full Context ทั้งหมด** (อัพเดทล่าสุด ณ ตอนนี้)  

คัดลอกทั้งก้อนด้านล่างนี้ไป **paste ใน Claude Code** เลยครับ (มันจะรู้ context ทุกไฟล์ที่เรามีตอนนี้ + ต่อยอดอัตโนมัติ)

---

```markdown
You are an expert solo developer building **XLayer DCA Guardian** — an AI Auto DCA Agent with Dry-Run Simulator for OKX Build X Hackathon on X Layer (Uniswap V4).

Current project status (all files below are already created and working locally):

=== CURRENT main.py ===
```python
import argparse
from simulator import DCASimulator
from onchain_utils import execute_swap, check_wallet_status

def parse_nl_query(query: str):
    """
    Mock Natural Language Parser for MVP.
    Example: 'Buy 50 USDC of ETH every 7 days for 30 days'
    """
    print(f"[*] Parsing NLP Query: '{query}'")
    return {
        "token_in": "USDC",
        "token_out": "ETH",
        "amount": 50.0,
        "interval": 7,
        "duration": 30
    }

def main():
    parser = argparse.ArgumentParser(description="XLayer DCA Guardian - AI Agent for OKX Auto-Investing")
    parser.add_argument("--query", type=str, default="Buy 50 USDC of ETH every 7 days for 30 days", help="Natural language DCA instructions")
    parser.add_argument("--execute", action="store_true", help="Perform real swap execution if safety checks pass")
    
    args = parser.parse_args()
    
    params = parse_nl_query(args.query)
    
    sim = DCASimulator(
        token_in=params["token_in"],
        token_out=params["token_out"],
        dca_amount=params["amount"],
        interval_days=params["interval"],
        duration_days=params["duration"]
    )
    
    sim.run()
    
    if args.execute:
        print("[!] Execution flag passed. Running safety bounds and TEE check.")
        if not check_wallet_status():
            print("Execution aborted due to authorization. Run `onchainos wallet login` first.")
            return
        confirm = input(f"Are you sure you want to execute REAL swap for {params['amount']} {params['token_in']} -> {params['token_out']} now? (y/n): ")
        if confirm.lower() == 'y':
            execute_swap(
                token_in=params["token_in"], 
                token_out=params["token_out"], 
                max_amount_in=str(params["amount"])
            )
        else:
            print("Execution manually aborted by user.")
    else:
        print("Note: Ran in SIMULATION mode. Append `--execute` to perform the actual on-chain transaction.")

if __name__ == "__main__":
    main()
```

=== CURRENT simulator.py ===
```python
import time
import math
import random
from typing import List, Dict, Tuple

class DCASimulator:
    def __init__(self, token_in: str, token_out: str, dca_amount: float, interval_days: int, duration_days: int):
        self.token_in = token_in.upper()
        self.token_out = token_out.upper()
        self.dca_amount = dca_amount
        self.interval_days = interval_days
        self.duration_days = duration_days
        self.trades = []
        self.total_invested = 0.0
        self.total_accumulated = 0.0
        self.gas_estimate = 0.0 

    def fetch_historical_prices(self) -> List[float]:
        print(f"[*] Fetching historical price data for {self.token_out} against {self.token_in}...")
        base_price = 3000.0 if self.token_out == 'ETH' else 45.0
        prices = []
        random.seed(42) 
        current_price = base_price
        for _ in range(0, self.duration_days, self.interval_days):
            prices.append(current_price)
            current_price *= 1.0 + random.uniform(-0.05, 0.06)
        return prices

    def run(self) -> float:
        print(f"\n======================================")
        print(f"      DRY-RUN DCA SIMULATION          ")
        print(f"======================================")
        print(f"Pair      : {self.token_in} -> {self.token_out}")
        print(f"Strategy  : Buy {self.dca_amount} {self.token_in} of {self.token_out}")
        print(f"Frequency : Every {self.interval_days} days for {self.duration_days} days\n")
        
        prices = self.fetch_historical_prices()
        
        for day_num, price in enumerate(prices):
            tokens_bought = self.dca_amount / price
            gas_cost_okb = 0.0001
            self.trades.append({
                "day": day_num * self.interval_days,
                "price": price,
                "amount_in": self.dca_amount,
                "amount_out": tokens_bought,
                "gas_okb": gas_cost_okb
            })
            self.total_invested += self.dca_amount
            self.total_accumulated += tokens_bought
            self.gas_estimate += gas_cost_okb

        current_value = self.total_accumulated * prices[-1]
        pnl = current_value - self.total_invested
        pnl_perc = (pnl / self.total_invested) * 100 if self.total_invested else 0

        print(f"--- SIMULATION RESULTS ---")
        print(f"Total Invested    : {self.total_invested:.2f} {self.token_in}")
        print(f"Total Accumulated : {self.total_accumulated:.6f} {self.token_out}")
        print(f"Final Value       : {current_value:.2f} {self.token_in}")
        print(f"PNL               : {pnl:.2f} {self.token_in} ({pnl_perc:.2f}%)")
        print(f"Estimated Gas     : {self.gas_estimate:.6f} OKB")
        print(f"======================================\n")
        return pnl_perc
```

Project rules (ยังเหมือนเดิม):
- Run 100% locally (no external server)
- Use OKX OnchainOS Skills via MCP (okx-dex-market + okx-dex-swap)
- X Layer mainnet RPC: https://rpc.xlayer.tech (chainId 196)
- Gas token = OKB
- Focus on USDC / ETH / OKB pairs first
- All keys stay local only

Next improvements we MUST do right now (priority order):
1. Show me the FULL current code of `onchain_utils.py` (Claude generated it earlier but not shown yet).
2. Replace mock `fetch_historical_prices()` in simulator.py with REAL call to OnchainOS skill `okx-dex-market` (pull actual historical K-line data on X Layer).
3. Add Matplotlib chart in DCASimulator.run(): price line + DCA buy points, save as `dca_simulation_chart.png`.
4. Upgrade `parse_nl_query()` to use smart LLM parsing (support Thai + English natural sentences).
5. Make sure `execute_swap()` in onchain_utils.py uses correct MCP skill `okx-dex-swap` with proper params for Uniswap V4 on X Layer.
6. After all changes, output ONLY the UPDATED full files (main.py, simulator.py, onchain_utils.py) + new test command.

Start by showing the full `onchain_utils.py` first, then apply all upgrades.
```

---

**วิธีใช้:**
1. Paste ทั้งก้อนด้านบนลงใน Claude Code  
2. Claude จะแสดง `onchain_utils.py` ให้ก่อน → แล้วอัพเดตทุกไฟล์ให้ใหม่  
3. หลังจากนั้นส่งโค้ดที่ได้กลับมาที่นี่ ผมจะรีวิว + ช่วยต่อ (เพิ่ม Economy Loop, Thai parser, video demo script)

พร้อม paste แล้วบอก “paste เสร็จ” หรือ “Claude ให้ onchain_utils.py มาแล้ว” ผมรอช่วยต่อเลยครับ 🔥  

เรากำลังเดินทางเร็วมาก ทำทัน deadline แน่นอน! 🚀