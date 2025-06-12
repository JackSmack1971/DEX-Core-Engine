# DEX-Core-Engine
## Python DEX Trading Bot

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A modular and production-ready framework for a simple Ethereum trading bot that operates exclusively on Decentralized Exchanges (DEXs). This project is built with a strong emphasis on Python best practices, security, and extensibility.

The default strategy implements a simple arbitrage mechanism, monitoring prices between two Uniswap V2-compatible DEXs (e.g., Uniswap and Sushiswap) and identifying profitable trading opportunities.

***

## 🚀 Key Features

* **Modular Architecture**: 
The code is logically separated into components for configuration, blockchain interaction, DEX handling, and trading strategy. 
This follows the **Single Responsibility Principle**, making the codebase easy to understand, test, and maintain.
* **Arbitrage Strategy**: A simple, functional arbitrage strategy that monitors a token pair (WETH/DAI by default) across two DEXs.
* **Secure by Design**: Manages sensitive data like private keys and RPC URLs through environment variables, preventing credentials from being hardcoded in source code.
* **Robust Error Handling**: Implements specific exception handling for network issues and failed transactions, ensuring the bot operates reliably.
* **Extensible Framework**: The decoupled design allows developers to easily implement and plug in new, more complex trading strategies without modifying the core boilerplate.
* **Adherence to Best Practices**: Built from the ground up following industry-standard Python best practices, including PEP 8 compliance, comprehensive typing, and clear documentation.

## 🏗️ Project Architecture

The bot is designed with a clean separation of concerns, ensuring that each part of the application has a distinct and focused purpose.

  /├── .env # Local environment configuration (private)
   ├── config.py # Loads and validates configuration from .env
   ├── web3_service.py # Service layer for all web3.py blockchain interactions
   ├── dex_handler.py # Abstraction for interacting with DEX router contracts
   ├── strategy.py # Contains the trading logic (e.g., ArbitrageStrategy)
   ├── main.py # Main entry point for the application
   └── requirements.txt # Project dependencies


1. **`config.py`**: Loads all required parameters (keys, addresses, thresholds) from the `.env` file. 

2. **`web3_service.py`**: A service class that encapsulates all `web3.py` logic. It handles node connections, transaction signing, and sending. 

3. **`dex_handler.py`**: Provides a high-level interface for DEX interactions, such as querying token prices and executing swaps. 

4. **`strategy.py`**: Implements the actual trading logic. It uses the `DEXHandler` to get market data and act on it. 

5. **`main.py`**: The application's entry point. It initializes all objects and starts the strategy's main loop. 

## 🛠️ Tech Stack * 
**Python 3.9+** * 
**[web3.py](https://github.com/ethereum/web3.py)**: The primary library for interacting with the Ethereum blockchain. * 
**[python-dotenv](https://github.com/theskumar/python-dotenv)**: For managing environment variables. 

## ⚙️ Installation & Setup 
Follow these steps to get your trading bot up and running. 

### 1. Prerequisites 
* Python 3.9 or newer. 
* An Ethereum wallet with a small amount of ETH for gas fees. 
* An RPC URL from a node provider like [Infura](https://infura.io/) or [Alchemy](https://www.alchemy.com/). 

### 2. Clone the Repository 

```
git clone <repository-url>
cd python-dex-trading-bot
```

3. Install Dependencies
Create a virtual environment to manage project dependencies in isolation.

# Create and activate a virtual environment
```
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```
# Install required packages
```
pip install -r requirements.txt
```
The required dependencies are listed in `requirements.txt`.
4. Configure Environment Variables
   
Create a .env file in the project's root directory. You can copy the .env.example file if it exists, or create one from scratch.

🔒 IMPORTANT SECURITY NOTICE The PRIVATE_KEY grants full control over your wallet.
• Never share this key or commit the .env file to version control.
• It is highly recommended to use a new, dedicated "hot wallet" for this bot with a limited amount of funds.
Your .env file should look like this:
```
# Ethereum Node RPC URL from a provider like Infura or Alchemy RPC_URL="YOUR_RPC_URL_HERE" 
# Wallet credentials 
# WARNING: This is your private key. Keep it secret, keep it safe. PRIVATE_KEY="YOUR_WALLET_PRIVATE_KEY_HERE" WALLET_ADDRESS="YOUR_WALLET_PUBLIC_ADDRESS_HERE"
```

▶️ Usage
To run the bot, execute the main.py script from the root of the project directory:

python main.py

The bot will initialize and begin polling the configured DEXs for trading opportunities. The console will display the current prices and whether a profitable opportunity has been found.
Example Output:
```
Initializing Ethereum Trading Bot... 
Connected to Ethereum node. 
Wallet: 0x... 
DEX handlers initialized. 
--- Starting Arbitrage Trading Bot --- 
Monitoring WETH / DAI pair. 
DEX 1 Router: 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D 
DEX 2 Router: 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F ---------------------------------------- 
Price DEX1: 3450.12 DAI | Price DEX2: 3451.50 DAI | Margin: 1.38 DAI 
No profitable opportunity found. Standing by. Waiting for 10 seconds...
```

🧩 How to Extend the Bot
The modular design makes it easy to add new strategies. To create your own:
• Create a new class in strategy.py (e.g., MovingAverageStrategy).
• Ensure it has a run() method that contains the main logic loop.
• In main.py, instantiate your new strategy class instead of ArbitrageStrategy.
This design promotes low coupling between the strategy logic and the underlying blockchain services.

⚠️ Disclaimer
This project is for educational purposes only and is not financial advice. Trading cryptocurrencies involves significant risk, including the potential for complete loss of funds. The author is not responsible for any financial losses incurred from the use of this software. Always do your own research and use this bot at your own risk.
