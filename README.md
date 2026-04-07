# 🛡️ XLayer DCA Guardian

An autonomous, AI-powered Dollar-Cost Averaging (DCA) agent built for the **OKX Build X Hackathon (Agent Track - X Layer Arena)**. 

**📺 [Watch our 2-Minute Video Pitch & Demo here!](https://www.loom.com/share/68982a26d4f847e1b49f268021808970)**

XLayer DCA Guardian is a secure, local-first Python application that utilizes Natural Language Processing (NLP) to set up advanced DCA strategies on the X Layer network. It features full X-Layer Testnet & Mainnet execution capabilities, a dynamic TEE (Trusted Execution Environment) wallet integration via OKX OnchainOS, and a gamified "Economy Loop" for protocol fee accumulation.

## 🌟 Key Features
- **🧠 Local NLP Strategy Parsing**: Effortlessly convert natural language (e.g., "DCA 50 USDC to BTC every 30 days for 1 year") into executable On-Chain parameters using an offline heuristic AI parser.
- **🛡️ Secure TEE Wallet Execution**: Leverages `okx-onchainos` locally to sign transactions via a secure enclave, entirely abstracted from manual private key handling.
- **🔄 Gamified Economy Loop**: Automatically collects a configurable percentage-based Treasury Fee upon successful swaps, accumulating value into a local smart treasury (`treasury.json`).
- **💼 Multi-Asset Portfolio Split**: Build advanced portfolio distributions (e.g. allocating chunks across BTC, ETH, and BNB equally) and compare returns against custom benchmarks.
- **📊 Dry-Run Simulator**: Simulates your exact parameters against historical market data on X Layer, rendering accurate PNL charts and CSV reports.

## 🛠️ Tech Stack
- Frontend: Streamlit (Python)
- Backend Logic: Python 3.x
- Crypto Execution: OKX Onchain OS (`onchainos` CLI)
- AI Parser: Python NLTK / Regex Engine
- Charting & Metrics: Pandas, Matplotlib

## 🚀 Quick Start
### Prerequisites
- Python 3.8+
- OKX OnchainOS CLI installed (`onchainos`)
- A registered TEE Wallet via `onchainos wallet login`

### Installation
1. Clone this repository
2. Install necessary dependencies via pip.
   ```bash
   pip install streamlit pandas matplotlib
   ```
3. Run the Streamlit Application:
   ```bash
   streamlit run app.py
   ```
4. Configure your TEE wallet within the app's sidebar to instantly load your Mainnet & Testnet portfolios!

## 🏆 Hackathon Alignment
Built specifically for the **X Layer Arena** (Full-Stack Agentic Apps). This project demonstrates a production-tier consumer web3 application entirely driven by abstract agentic infrastructure.
