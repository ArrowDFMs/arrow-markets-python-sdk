from web3 import Web3
from web3.auto import w3 as account
from eth_utils import to_checksum_address
from eth_account.messages import encode_defunct
import requests
import datetime
import math
import pytz

# Constants
from constants import *

def isValidVersion(version):
    return version in versions

""""
 * Get the router contract from Arrow's contract suite.
 *
 * @param version Version of Arrow contract suite with which to interact. Default is V4.
 * @param wallet Wallet with which you want to connect the instance of the router contract. Default is Fuji provider.
 * @returns Local instance of ethers.Contract for the Arrow router contract.
"""
def getRouterContract(version=DEFAULT_VERSION): 
    if not isValidVersion(version):
        raise UNSUPPORTED_VERSION_ERROR

    router = w3.eth.contract(
        address=addresses["fuji"]["router"][version],
        abi=IArrowRouterABI
    )
    return router

""""
 * Get the stablecoin contract that is associated with Arrow's contract suite.
 *
 * @param version Version of Arrow contract suite with which to interact. Default is V4.
 * @param wallet Wallet with which you want to connect the instance of the stablecoin contract. Default is Fuji provider.
 * @returns Local instance of ethers.Contract for the stablecoin contract.
"""
def getStablecoinContract(version=DEFAULT_VERSION):
    if not isValidVersion(version):
        raise UNSUPPORTED_VERSION_ERROR

    stablecoin = w3.eth.contract(
        address=getRouterContract(version).functions.getStablecoinAddress().call(),
        abi=ERC20ABI
    )
    return stablecoin

""""
 * Get the events contract from Arrow's contract suite.
 *
 * @param version Version of Arrow contract suite with which to interact. Default is V4.
 * @param wallet Wallet with which you want to connect the instance of the Arrow events contract. Default is Fuji provider.
 * @returns Local instance of ethers.Contract for the Arrow events contract.
"""
def getEventsContract(version=DEFAULT_VERSION):
    if not isValidVersion(version):
        raise UNSUPPORTED_VERSION_ERROR

    events = w3.eth.contract(
        address=getRouterContract(version).functions.getEventsAddress().call(),
        abi=IArrowEventsABI
    )
    return events

""""
 * Get the registry contract from Arrow's registry suite.
 *
 * @param version Version of Arrow contract suite with which to interact. Default is V4.
 * @param wallet Wallet with which you want to connect the instance of the Arrow registry contract. Default is Fuji provider.
 * @returns Local instance of ethers.Contract for the Arrow registry contract.
"""
def getRegistryContract(version=DEFAULT_VERSION):
    if not isValidVersion(version):
        raise UNSUPPORTED_VERSION_ERROR

    registry = w3.eth.contract(
        address=getRouterContract(version).functions.getRegistryAddress().call(),
        abi=IArrowRegistryABI
    )
    return registry

"""
 * Get the current price (in USD) of an underlying asset from Binance or CryptoWatch.
 * If there is a specific timeout code in the return from Binance, try on CryptoWatch.
 * Throw custom error if there is some issue getting the spot price.
 * 
 * @param ticker Ticker of the underlying asset.
 * @returns Spot price of underlying asset specified by ticker.
"""
def getUnderlierSpotPrice(ticker):
    # Using Binance API to get latest price
    binanceResponse = requests.get(
        "https://api.binance.com/api/v3/ticker/price?symbol={}".format(binanceSymbols[ticker])
    )

    # If Binance tells us we have been making too many requests, use Cryptowatch
    if "code" in binanceResponse.json() and binanceResponse.json()["code"] == -1003: 
        # Use CryptoWatch API to get latest price
        cryptowatchResponse = requests.get(
            "https://api.cryptowat.ch/markets/binance/{}/price".format(binanceSymbols[ticker])
        )
        try:
            return float(cryptowatchResponse.json()["result"]["price"])
        except:
            raise Exception("Could not retrieve underlying spot price from Cryptowatch.")
    else:
        try:
            return float(binanceResponse.json()["price"])
        except:
            raise Exception("Could not retrieve underlying spot price from Binance.")

"""
 * Get the price history and market caps for the underlying asset using CoinGecko.
 * 
 * @param ticker Ticker of underlying asset.
 * @param days Number of days worth of historical data to get from CoinGecko. Default is 84 days to match the API.
 * @param currency Currency to which we wish to convert the value. Default is USD to match the API.
 * @returns Price history and market caps of the underlying asset as 2D arrays of dates and values (floats).
"""
def getUnderlierMarketChart(ticker, days=84, currency="usd"):
    underlierID = coingeckoIDs[ticker]

    params = {
        "days": days,
        "vs_currency": currency
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.get("https://api.coingecko.com/api/v3/coins/{}/market_chart".format(underlierID), params=params, headers=headers)
    marketCaps = response.json()["market_caps"]
    prices = response.json()["prices"]
    priceHistory = []
    for item in prices:
        priceHistory.append([item[0], item[1]]) # item[0] is date, item[1] is price

    return priceHistory, marketCaps

"""
 * Get the spot price and market chart (refer to getUnderlierMarketChart) for the underlying asset using CoinGecko.
 * 
 * @param ticker Ticker of underlying asset.
 * @param days Number of days worth of historical data to get from CoinGecko. Default is 84 days to match the API.
 * @param currency Currency to which we wish to convert the value. Default is USD to match the API.
 * @returns JSON object that contains the spot price and market chart information of the underlying asset.
"""
def getUnderlierSpotPriceAndMarketChart(ticker, days=84, currency="usd"):
    spotPrice = getUnderlierSpotPrice(ticker)
    marketChart = getUnderlierMarketChart(ticker, days, currency)

    return spotPrice, marketChart

"""
 * Get readable timestamp from millisecond timestamp.
 *
 * @param millisTimestamp Millisecond timestamp in UTC. For example, 1654848000000 for Jun 10 2022 08:00:00.
 * @returns Readable timestamp in the "MMDDYYYY" format.
"""
def getReadableTimestamp(millisTimestamp, includeSlashes=False):
    time = datetime.datetime.fromtimestamp(millisTimestamp / 1000)
    return time.strftime('%m/%d/%Y') if includeSlashes else time.strftime('%m%d%Y')

"""
 * Get current time in UTC.
 *
 * @returns Object that contains a moment object & unix, millisecond, and readable timestamp representations of the current time.
"""
def getCurrentTimeUTC():
    currentTime = datetime.datetime.utcnow()
    print(currentTime)

    return {
        "datetimeTimestamp": currentTime,
        "unixTimestamp": round(currentTime.timestamp()),
        "millisTimestamp": round(currentTime.timestamp() * 1000),
        "readableTimestamp": getReadableTimestamp(currentTime.timestamp() * 1000)
    }

"""
 * Get unix, millisecond, and readable UTC timestamps from millisecond timestamp in any other time zone.
 *
 * @param millisTimestamp Millisecond timestamp in UTC. For example, 1654848000000 for Jun 10 2022 08:00:00.
 * @returns JSON object that contains a moment object as well as unix, millisecond, and readable UTC timestamp representations of millisTimestamp.
"""
def getTimeUTC(millisTimestamp):

    return {
        "datetimeTimestamp": datetime.datetime.fromtimestamp(millisTimestamp / 1000),
        "unixTimestamp": round(millisTimestamp / 1000),
        "millisTimestamp": millisTimestamp,
        "readableTimestamp": getReadableTimestamp(millisTimestamp)
    }

"""
 * Get unix and millisecond timestamps from readable expiration. This works for any readable timestamp, not just expirations.
 *
 * @param readableExpiration Readable timestamp in the "MMDDYYYY" format.
 * @returns JSON object that contains a moment object as well as unix and millisecond timestamp representations of the readable timestamp.
"""
def getExpirationTimestamp(readableExpiration):
    expiration = datetime.datetime.strptime(readableExpiration, '%m%d%Y').replace(hour=8)
    timezone = pytz.timezone("UTC")
    expiration = timezone.localize(expiration)
    
    if not isFriday(expiration.timestamp()):
        raise UNSUPPORTED_EXPIRATION_ERROR

    return {
        "datetimeTimestamp": expiration,
        "unixTimestamp": round(expiration.timestamp()),
        "millisTimestamp": round(expiration.timestamp() * 1000)
    }

"""
 * Checks if a UNIX timestamp is a Friday (specifically, in the timezone from which the timestamp came).
 *
 * @param unixTimestamp UNIX timestamp.
 * @returns True if is a Friday, else returns False.
"""
def isFriday(unixTimestamp):
    dayOfTheWeek = (math.floor(unixTimestamp / secondsPerDay) + 4) % 7
    return dayOfTheWeek == 5

"""
 * Compute address of on-chain option chain contract using CREATE2 functionality.
 *
 * @param ticker Ticker of the underlying asset.
 * @param readableExpiration Readable expiration in the "MMDDYYYY" format.
 * @param version Version of Arrow contract suite with which to interact. Default is V4.
 * @param wallet Wallet with which you want to connect the instance of the Arrow registry contract. Default is Fuji provider.
 * @returns Address of the option chain corresponding to the passed ticker and expiration.
"""
def computeOptionChainAddress(ticker, readableExpiration, version=DEFAULT_VERSION):
    # Get chain factory contract address from router
    router = getRouterContract(version)

    if version == "v4" or version == "competition":
        optionChainFactoryAddress = router.functions.getOptionChainFactoryAddress().call()
    else:
        raise UNSUPPORTED_VERSION_ERROR

    # Build salt for CREATE2
    salt = Web3.solidityKeccak(["address", "string", "uint256"], [optionChainFactoryAddress, ticker, readableExpiration])

    # Compute option chain proxy address using CREATE2
    pre = '0xff'
    b_pre = bytes.fromhex(pre[2:])
    b_address = bytes.fromhex(optionChainFactoryAddress[2:])
    b_salt = bytes.fromhex(salt.hex()[2:])
    b_init_code = bytes.fromhex(bytecodeHashes["ArrowOptionChainProxy"][version].hex()[2:])
    b_result = Web3.keccak(b_pre + b_address + b_salt + b_init_code)
    optionChainAddress = to_checksum_address(b_result[12:].hex())

    return optionChainAddress

"""
 * Help construct DeliverOptionParams object that can be passed to the Arrow API to submit an option order.
 *
 * @param optionOrderParams Object containing parameters necesssary in computing parameters for submitting an option order.
 * @param version Version of Arrow contract suite with which to interact. Default is V4.
 * @param wallet Wallet with which you want to submit the option order.
 * @returns JSON that contains the variables necessary in completing the option order.
"""
def prepareDeliverOptionParams(optionOrderParams: OptionOrderParams, version = DEFAULT_VERSION): 
    # Get stablecoin decimals
    stablecoinDecimals = getStablecoinContract(version).functions.decimals().call()

    # Define scope for variables
    thresholdPrice = round(optionOrderParams["thresholdPrice"] * pow(10, stablecoinDecimals))
    unixExpiration = getExpirationTimestamp(optionOrderParams["expiration"])["unixTimestamp"]
    strikes = [round(strike,2) for strike in optionOrderParams["strike"]]
    bigNumberStrike = [strike * pow(10, stablecoinDecimals) for strike in strikes]
    strikes = ['{:.2f}'.format(round(strike, 2)) for strike in strikes]
    bigNumberStrike = [round(strike) for strike in bigNumberStrike]
    formattedStrike = "|".join(strikes)

    if version == "v4" or version == "competition":
        intQuantity = round(optionOrderParams["quantity"] * quantityScaleFactor)
    else: 
        raise UNSUPPORTED_VERSION_ERROR

    # Hash and sign the option order parameters for on-chain verification
    types = [
        "bool",       # buyFlag - Boolean to indicate whether this is a buy (true) or sell (false).
        "string",     # ticker - String to indicate a particular asset ("AVAX", "ETH", or "BTC").
        "uint256",    # expiration - Date in Unix timestamp. Must be 8:00 AM UTC (e.g. 1643097600 for January 25th, 2022).
        "uint256",    # readableExpiration - Date in "MMDDYYYY" format (e.g. "01252022" for January 25th, 2022).
        "uint256[2]", # strike - Ethers BigNumber versions of the strikes in terms of the stablecoin's decimals (e.g. [ethers.utils.parseUnits(strike, await usdc_e.decimals()), ethers.BigNumber.from(0)]).
        "string",     # decimalStrike - String version of the strike that includes the decimal places (e.g. "12.25").
        "uint256",    # contractType - 0 for call, 1 for put, 2 for call spread, and 3 for put spread.
        "uint256",    # quantity - Integer number of contracts desired in the order. Has to be scaled by supported decimals (10**2).
        "uint256"     # thresholdPrice - Indication of the price the user is willing to pay (e.g. ethers.utils.parseUnits(priceWillingToPay, await usdc_e.decimals()).toString()).
    ]
    data = [
        optionOrderParams["orderType"] == 0,
        optionOrderParams["ticker"],
        unixExpiration,
        int(optionOrderParams["expiration"]),
        bigNumberStrike,
        formattedStrike,
        optionOrderParams["contractType"],
        intQuantity,
        thresholdPrice
    ]
    hashedValues = Web3.solidityKeccak(types, data) 

    # Note that we are signing a message, not a transaction
    message = encode_defunct(hexstr=hashedValues.hex())
    private_key = '65acf45f04d6c793712caa5aba61a9e3d2f9194e1aae129f9ca6fe39a32d159f' # Public facing test account
    signature = account.eth.account.sign_message(message, private_key)

    value = int(optionOrderParams["thresholdPrice"] * optionOrderParams["quantity"])
    amountToApprove = int(round(value, stablecoinDecimals) * pow(10, stablecoinDecimals))

    result = {
        "hashedValues": hashedValues,
        "signature": signature,
        "amountToApprove": amountToApprove
    }
    result.update(optionOrderParams)
    result.update({
        "unixExpiration": unixExpiration,
        "formattedStrike": formattedStrike,
        "bigNumberStrike": bigNumberStrike,
        "bugNumberThresholdPrice:" : thresholdPrice
    })

    return result
    