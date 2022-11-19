from web3 import Web3
from eth_utils import to_checksum_address
from eth_account.messages import encode_defunct
import requests
import datetime
import math

# Constants
from constants import *
from utilities import *

"""
 * Get an estimated price for the given option parameters from Arrow's pricing model.
 *
 * @param option Object containing parameters that define an option on Arrow.
 * @param version Version of Arrow contract suite with which to interact. Default is V4.
 * @returns Float that represents an estimate of the option price using Arrow's pricing model.
"""
def estimateOptionPrice(optionOrderParams: OptionOrderParams, version = DEFAULT_VERSION):
    # Take strike array and convert into string with format "longStrike|shortStrike"
    strike = "|".join(optionOrderParams["strike"])

    # Get spot price from optionOrderParams if it is included, otherwise get it from helper function
    spotPrice = optionOrderParams["spotPrice"]
    if spotPrice == None:
        spotPrice = getUnderlierSpotPrice(optionOrderParams["ticker"])

    # Get historical prices from optionOrderParams if they are included, otherwise, get them from helper function
    priceHistory = optionOrderParams["priceHistory"]
    if priceHistory == None:
        priceHistory = getUnderlierMarketChart(optionOrderParams["ticker"])[0]
    
    body = {
        "order_type": optionOrderParams["orderType"],
        "ticker": optionOrderParams["ticker"],
        "expiration": optionOrderParams["expiration"], # API only takes in readable expirations so it can manually set the UNIX expiration
        "strike": strike,
        "contract_type": optionOrderParams["contractType"],
        "quantity": optionOrderParams["quantity"],
        "spot_price": spotPrice,
        "price_history": [entry[1] for entry in priceHistory] # entry[1] is the price
    }

    estimatedOptionPriceResponse = requests.post(urls["api"][version] + "/estimate-option-price", json=body)

    return estimatedOptionPriceResponse.json()["option_price"]

"""
 * Get an estimated price and the greeks for a given option using Arrow's pricing model.
 *
 * @param option Object containing parameters that define an option on Arrow.
 * @param version Version of Arrow contract suite with which to interact. Default is V4.
 * @returns JSON object that contains an estimate of the option price using Arrow's pricing model as well as the greeks associated with the specified option.
"""
def estimateOptionPriceAndGreeks(optionOrderParams: OptionOrderParams, version = DEFAULT_VERSION):
    # Take strike array and convert into string with format "longStrike|shortStrike"
    strike = "|".join(optionOrderParams["strike"])

    # Get spot price from optionOrderParams if it is included, otherwise get it from helper function
    spotPrice = optionOrderParams["spotPrice"]
    if spotPrice == None:
        spotPrice = getUnderlierSpotPrice(optionOrderParams["ticker"])

    # Get historical prices from optionOrderParams if they are included, otherwise, get them from helper function
    priceHistory = optionOrderParams["priceHistory"]
    if priceHistory == None:
        priceHistory = getUnderlierMarketChart(optionOrderParams["ticker"])[0]
    
    body = {
        "order_type": optionOrderParams["orderType"],
        "ticker": optionOrderParams["ticker"],
        "expiration": optionOrderParams["expiration"], # API only takes in readable expirations so it can manually set the UNIX expiration
        "strike": strike,
        "contract_type": optionOrderParams["contractType"],
        "quantity": optionOrderParams["quantity"],
        "spot_price": spotPrice,
        "price_history": [entry[1] for entry in priceHistory] # entry[1] is the price
    }
    estimatedOptionPriceResponse = requests.post(urls["api"][version] + "/estimate-option-price", json=body)
    estimatedOptionPrice = estimatedOptionPriceResponse.json()["option_price"]
    greeks = estimatedOptionPriceResponse.json()["greeks"]

    return estimatedOptionPrice, greeks

"""
 * Get a recommended option from our server given some option parameters and a price forecast.
 *
 * @param ticker Ticker of the underlying asset.
 * @param readableExpiration Readable timestamp in the "MMDDYYYY" format.
 * @param forecast Forecasted price of underlying asset.
 * @param spotPrice // Most up-to-date price of underlying asset.
 * @param priceHistory // Prices of underlying asset over some period of history.
 * @param version Version of Arrow contract suite with which to interact. Default is V4.
 * @returns Option object with optional price and greeks parameters populated.
"""
def getRecommendedOption(ticker, readableExpiration, forecast, spotPrice, priceHistory, version = DEFAULT_VERSION):
    if spotPrice == None:
        spotPrice = getUnderlierSpotPrice(ticker)
    if priceHistory == None:
        priceHistory = [entry[1] for entry in getUnderlierMarketChart(ticker)[0]]

    if not isValidVersion(version):
        raise UNSUPPORTED_VERSION_ERROR

    try: 
        body = {
            "ticker": ticker,
            "expiration": readableExpiration,
            "forecast": forecast,
            "spot_price": spotPrice,
            "price_history": priceHistory
        }
        recommendedOptionResponse = requests.post(urls["api"][version] + "/get-recommended-option", json=body)

        recommendedOption = {
            "ticker": ticker,
            "expiration": readableExpiration,
            "strike": recommendedOptionResponse.json()["option"]["strike"],
            "contractType": recommendedOptionResponse.json()["option"]["contract_type"],
            "price": recommendedOptionResponse.json()["option"]["price"],
            "greeks": recommendedOptionResponse.json()["option"]["greeks"]
        }

        return recommendedOption
    except Exception as e:
        print(e)

"""
 * Get a strike grid given some option parameters.
 *
 * @param orderType Type of order the user is placing. 0 for long open, 1 for long close, 2 for short open, 3 for short close.
 * @param ticker Ticker of the underlying asset.
 * @param readableExpiration Readable timestamp in the "MMDDYYYY" format.
 * @param contractType // 0 for call, 1 for put.
 * @param spotPrice // Most up-to-date price of underlying asset.
 * @param priceHistory // Prices of underlying asset over some period of history.
 * @param version Version of Arrow contract suite with which to interact. Default is V4.
 * @returns Array of Option objects with optional price and greeks parameters populated.
"""
def getStrikeGrid(orderType, ticker, readableExpiration, contractType, spotPrice, priceHistory, version=DEFAULT_VERSION):
    if spotPrice == None:
        spotPrice = getUnderlierSpotPrice(ticker)
    if priceHistory == None:
        priceHistory = [entry[1] for entry in getUnderlierMarketChart(ticker)[0]]

    if not isValidVersion(version):
        raise UNSUPPORTED_VERSION_ERROR

    body = {
        "order_type": orderType,
        "ticker": ticker,
        "expiration": readableExpiration,
        "contract_type": contractType,
        "spot_price": spotPrice,
        "price_history": priceHistory
    }
    strikeGridResponse = requests.post(urls["api"][version] + "/get-strike-grid", json=body)

    strikeGrid = []
    for i in range(len(strikeGridResponse.json()["options"])):
        strikeGridOption = strikeGridResponse.json()["options"][i]
        option = {
            "ticker": ticker,
            "expiration": readableExpiration,
            "strike": strikeGridOption["strike"],
            "contractType": contractType,
            "price": strikeGridOption["price"],
            "greeks": strikeGridOption["greeks"]
        }
        strikeGrid.append(option)

    return strikeGrid

"""
 * Submit an option order to the API to compute the live price and submit a transaction to the blockchain.
 *
 * @param deliverOptionParams Object containing parameters necessary to create an option order on Arrow.
 * @param version Version of Arrow contract suite with which to interact. Default is V4.
 * @returns Data object from API response that includes transaction hash and per-option execution price of the option transaction.
"""
def submitOptionOrder(deliverOptionParams: DeliverOptionParams, version = DEFAULT_VERSION):
    if not isValidVersion(version):
        raise UNSUPPORTED_VERSION_ERROR

    # Submit option order through API
    body = {
        "order_type": deliverOptionParams["orderType"],
        "ticker": deliverOptionParams["ticker"],
        "expiration": deliverOptionParams["expiration"],
        "strike": deliverOptionParams["formattedStrike"],
        "contract_type": deliverOptionParams["contractType"],
        "quantity": deliverOptionParams["quantity"],
        "threshold_price": str(deliverOptionParams["bigNumberThresholdPrice"]),
        "hashed_params": deliverOptionParams["hashedValues"],
        "signature": deliverOptionParams["signature"]
    }
    orderSubmissionResponse = requests.post(urls["api"][version] + "/submit-order", json=body)

    # Return all data from response
    return orderSubmissionResponse.json()
