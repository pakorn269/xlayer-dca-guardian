import time
import math
import random
import os
import matplotlib.pyplot as plt
from typing import List, Dict

# Expanded Official X Layer Master Addresses
TOKEN_ADDRESSES = {
    "ETH": "0x5A77f1443D16ee5761d310e38b62f77f726bC71c",
    "WETH": "0x5A77f1443D16ee5761d310e38b62f77f726bC71c",
    "USDC": "0x74b7F16337b8972027F6196A17a631aC6dE26d22",
    "USDT": "0x779Ded0c9e1022225f8E0630b35a9b54bE713736",
    "OKB": "0xe538905cf8410324e03A5A23C1c177a474D59b2b",
    "BTC": "0x1a4b46696b2bb4794eb3d4c26f1c55f9170fa4c5", # WBTC (Bridged layer indicator)
    "DAI": "0xc5015b9d9161dca7e18e32f6f25c4ad850731fd4", # Dai Stablecoin (verified)
    "LINK": "0x8af9711b44695a5a081f25ab9903ddb73acf8fa9", # ChainLink Token (verified)
    "SOL": "0x505000008de8748dbd4422ff4687a4fc9beba15b",  # OKX Wrapped SOL / xSOL (verified)
    "WOKB": "0x3ea3a4038fba5757a9a68de920b44698d7326a59", # Wrapped OKB - Hot Token (verified)
}

class DCASimulator:
    def __init__(self, token_in: str, token_out: str, dca_amount: float, interval_days: int, duration_days: int, is_testnet: bool = False):
        self.token_in = token_in.upper()
        self.token_out = token_out.upper()
        self.dca_amount = dca_amount
        self.interval_days = interval_days
        self.duration_days = duration_days
        self.is_testnet = is_testnet
        from config import CHAIN_ID_TESTNET, CHAIN_ID_MAINNET
        self.chain_id = CHAIN_ID_TESTNET if is_testnet else CHAIN_ID_MAINNET
        self.trades = []
        self.total_invested = 0.0
        self.total_accumulated = 0.0
        self.gas_estimate = 0.0
        self.prices = []           # exposed for Portfolio Split chart
        self.avg_cost_final = 0.0  # exposed after run()

    def fetch_historical_prices(self) -> List[float]:
        from onchain_utils import get_historical_kline, get_swap_quote
        
        addr = TOKEN_ADDRESSES.get(self.token_out)
        interval_prices = []
        total_steps = self.duration_days // self.interval_days + 1
        
        estimated_out, _, _ = get_swap_quote(self.token_in, self.token_out, str(self.dca_amount), self.chain_id)
        live_price = (self.dca_amount / estimated_out) if estimated_out > 0 else (3000.0 if self.token_out in ['ETH', 'WETH'] else (60000.0 if self.token_out == 'BTC' else 45.0))
        
        if addr:
            real_prices = get_historical_kline(addr, self.chain_id)
            if real_prices and len(real_prices) >= total_steps:
                print(f"[+] Real market data successfully retrieved!")
                for i in range(0, len(real_prices), self.interval_days):
                    interval_prices.append(real_prices[i])
                    if len(interval_prices) == total_steps:
                        break
                interval_prices[-1] = live_price
                return interval_prices
                
        print(f"[-] Generating structural mock data from live anchor (Anchor: {live_price:.2f})")
        random.seed(42) 
        current_price = live_price * 0.95 
        for i in range(total_steps):
            interval_prices.append(current_price)
            current_price *= 1.0 + random.uniform(-0.06, 0.07)
        return interval_prices
        
    def render_chart(self, prices: List[float]):
        """Render a Matplotlib line chart summarizing the strategy."""
        days = [i * self.interval_days for i in range(len(prices))]

        plt.figure(figsize=(10, 5))
        plt.plot(days, prices, color='royalblue', label=f'{self.token_out} Price', linewidth=2)
        plt.scatter(days, prices, color='limegreen', s=50, label='DCA Purchase Point', zorder=5)

        if self.avg_cost_final > 0:
            plt.axhline(
                y=self.avg_cost_final,
                color='orange',
                linestyle='-',
                linewidth=1.5,
                label=f'Avg Cost Basis ({self.avg_cost_final:.4f})'
            )
        if prices:
            plt.axhline(
                y=prices[-1],
                color='gray',
                linestyle='--',
                linewidth=1.5,
                label=f'Current Price ({prices[-1]:.4f})'
            )

        net_str = "Testnet" if self.is_testnet else "Mainnet"
        plt.title(f"XLayer ({net_str}) Auto-DCA Simulator: {self.token_in} to {self.token_out}\nEvery {self.interval_days} Days")
        plt.xlabel("Days")
        plt.ylabel(f"Price ({self.token_in})")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()

        out_path = "dca_simulation_chart.png"
        plt.savefig(out_path, dpi=120)
        plt.close()
        print(f"\n📈 Visual Chart Generated: {os.path.abspath(out_path)}")

    def run(self) -> float:
        from onchain_utils import get_swap_quote, get_treasury

        # Guard: same token in and out is a no-op
        if self.token_in == self.token_out:
            print(f"[WARN] token_in and token_out are both {self.token_in}. Aborting simulation.")
            return 0.0

        print(f"\n======================================")
        print(f"      DRY-RUN DCA SIMULATION          ")
        print(f"======================================")
        if self.is_testnet:
            print(f"[!] RUNNING ON X LAYER TESTNET (195) - Simulated Environment")
        else:
            print(f"[!] RUNNING ON X LAYER MAINNET (196) - Live Environment")

        print(f"👉 Selected Pair: {self.token_in} -> {self.token_out}")
        print(f"Strategy  : Buy {self.dca_amount} {self.token_in} of {self.token_out}")
        print(f"Frequency : Every {self.interval_days} days for {self.duration_days} days\n")

        prices = self.fetch_historical_prices()
        self.prices = prices  # exposed for Portfolio Split chart
        _, est_gas, _ = get_swap_quote(self.token_in, self.token_out, self.dca_amount, self.chain_id)

        for day_num, price in enumerate(prices):
            tokens_bought = self.dca_amount / price
            gas_cost_okb = est_gas

            self.total_invested += self.dca_amount
            self.total_accumulated += tokens_bought
            avg_cost = self.total_invested / self.total_accumulated  # running ACB

            self.trades.append({
                "day": day_num * self.interval_days,
                "price": price,
                "amount_in": self.dca_amount,
                "amount_out": tokens_bought,
                "gas_okb": gas_cost_okb,
                "avg_cost": avg_cost,
            })

            self.gas_estimate += gas_cost_okb

        self.avg_cost_final = self.total_invested / self.total_accumulated if self.total_accumulated else 0.0

        current_value = self.total_accumulated * prices[-1]
        pnl = current_value - self.total_invested
        pnl_perc = (pnl / self.total_invested) * 100 if self.total_invested else 0
        
        treasury = get_treasury()

        self.render_chart(prices)

        print(f"\n--- SIMULATION RESULTS ---")
        print(f"Total Invested    : {self.total_invested:.2f} {self.token_in}")
        print(f"Total Accumulated : {self.total_accumulated:.6f} {self.token_out}")
        print(f"Final Value       : {current_value:.2f} {self.token_in}")
        print(f"PNL               : {pnl:.2f} {self.token_in} ({pnl_perc:.2f}%)")
        print(f"Estimated Gas     : {self.gas_estimate:.6f} OKB")
        print(f"Treasury Balance  : {treasury['balance']:.4f} {treasury['currency']}")
        print(f"======================================\n")
        
        return pnl_perc

    def get_trades_csv(self) -> str:
        """Returns the trades list as a CSV string."""
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["day", "price", "amount_in", "amount_out", "gas_okb", "avg_cost"])
        writer.writeheader()
        for trade in self.trades:
            writer.writerow(trade)
        return output.getvalue()
        
    def save_history(self, pnl_perc: float):
        import json
        from datetime import datetime
        history_file = "simulation_history.json"
        data = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
            except: pass
        
        data.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "token_in": self.token_in,
            "token_out": self.token_out,
            "amount": self.dca_amount,
            "interval": self.interval_days,
            "duration": self.duration_days,
            "net": "Testnet" if self.is_testnet else "Mainnet",
            "pnl_perc": round(pnl_perc, 2)
        })
        with open(history_file, 'w') as f:
            json.dump(data, f, indent=4)
