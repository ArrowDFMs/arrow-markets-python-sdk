from tokenize import Double
from typing import TypedDict
from web3 import Web3

import json

# Provider
w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/avalanche_fuji'))

# Default version
DEFAULT_VERSION = "v4"

# Import contract JSONs
import os.path
ERC20ABIFile = open(os.path.dirname(__file__) + '/abis/IERC20Metadata.json', 'r', encoding='utf8')
IArrowRouterABIFile = open(os.path.dirname(__file__) + '/abis/v4/IArrowRouter.json', 'r', encoding='utf8')
IArrowEventsABIFile = open(os.path.dirname(__file__) + '/abis/v4/IArrowEvents.json', 'r', encoding='utf8')
IArrowRegistryABIFile = open(os.path.dirname(__file__) + '/abis/v4/IArrowRegistry.json', 'r', encoding='utf8')
ArrowOptionChainProxyCompetitionABIFile = open(os.path.dirname(__file__) + '/build/competition/ArrowOptionChainProxy.json', 'r', encoding='utf8')
ArrowOptionChainProxyV3ABIFile = open(os.path.dirname(__file__) + '/build/v3/ArrowOptionChainProxy.json', 'r', encoding='utf8')
ArrowOptionChainProxyV4ABIFile = open(os.path.dirname(__file__) + '/build/v4/ArrowOptionChainProxy.json', 'r', encoding='utf8')

# Load contract JSONs
ERC20ABI = json.load(ERC20ABIFile)
IArrowRouterABI = json.load(IArrowRouterABIFile)
IArrowEventsABI = json.load(IArrowEventsABIFile)
IArrowRegistryABI = json.load(IArrowRegistryABIFile)
ArrowOptionChainProxyV3ABI = json.load(ArrowOptionChainProxyV3ABIFile)
ArrowOptionChainProxyV4ABI = json.load(ArrowOptionChainProxyV4ABIFile)
ArrowOptionChainProxyCompetitionABI = json.load(ArrowOptionChainProxyCompetitionABIFile)

# Bytecode
bytecodeHashes = {
    "ArrowOptionChainProxy": {
        "v3": Web3.solidityKeccak(["bytes"], [ArrowOptionChainProxyV3ABI["bytecode"]]),
        "v4": Web3.solidityKeccak(["bytes"], [ArrowOptionChainProxyV4ABI["bytecode"]]),
        "competition": Web3.solidityKeccak(["bytes"], [ArrowOptionChainProxyCompetitionABI["bytecode"]])
    }
}

addresses = {
    "fuji": {
        "router": {
            "v3": "0x31122CeF9891Ef661C99352266FA0FF0079a0e06",
            "v4": "0xa6EA0E47501627a964e11E31D2BD7D40452dff6F",
            "competition": "0x33D1a0529D0C23f183fF1de346BDcA029dB0046E"
        }
    }
}

urls = {
    "api": {
        "v3": "https://fuji-v3-api.arrow.markets/v1",
        "v4": "https://fuji-v4-api.arrow.markets/v1",
        "competition": "https://competition-v3-api.arrow.markets/v1"
    },
    "provider": {
        "fuji": "https://api.avax-test.network/ext/bc/C/rpc"
    }
}

binanceSymbols = {
    "AVAX": "AVAXUSDT",
    "ETH": "ETHUSDT",
    "BTC": "BTCUSDT"
}

coingeckoIDs = {
    "AVAX": "avalanche-2",
    "ETH": "ethereum",
    "BTC": "bitcoin"
}

versions = {"v3", "v4", "competition"}
secondsPerDay = 60 * 60 * 24
quantityScaleFactor = 10**2

class UNSUPPORTED_VERSION_ERROR(Exception):
    """Raised when incorrect version"""
    pass

class UNSUPPORTED_EXPIRATION_ERROR(Exception):
    """Raised when expiration date not Friday"""
    pass

# Custom classes

class Greeks(TypedDict):
    delta: float # Sensitivity of an option’s price to changes in the value of the underlying.
    gamma: float # Change in delta per change in price of the underlying.
    rho: float # Sensitivity of option prices to changes in interest rates.
    theta: float # Measures time decay of price of option.
    vega: float # Change in value from a 1% change in volatility.

class OptionContract(TypedDict):
    ticker: str # Ticker enum that denotes a particular asset.
    expiration: str # Readable expiration date in "MMDDYYYY" format (e.g. "01252022" for January 25th, 2022).
    strike: list # Accepts arrays with two values for spreads. Formatted as [longStrike, shortStrike].
    contractType: int # ContractType enum that indicates whether the option is a call, put, call spread, or put spread.
    price: float # Float number that indicates the price of 1 option.
    spotPrice: float # Most up-to-date price of underlying asset.
    priceHistory: list # Prices of underlying asset over some period of history.
    greeks: Greeks # Greeks interface that specifies which greeks are tied to this option.

class OptionOrderParams(OptionContract):
    quantity: float # Float number of contracts desired in the order.
    orderType: int # OrderType enum that indicates whether this option is a long open, long close, short open, or short close.
    thresholdPrice: float # The minimum (or maximum) price the user is willing to receive (or pay) for this specific option.

class DeliverOptionParams(OptionOrderParams):
    hashedValues: str
    signature: str
    amountToApprove: int
    unixExpiration: int # UTC expiration date of option in UNIX timestamp.
    formattedStrike: str # Turns strike[] into formatted string with format like "longStrike|shortStrike".
    bigNumberStrike: list
    bigNumberThresholdPrice: int

