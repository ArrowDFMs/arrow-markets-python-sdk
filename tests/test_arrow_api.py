import pytest
import sys
import os.path
# appending the parent directory path
sys.path.append(os.path.dirname(__file__)+'/../')
from utilities import *
from arrow_sdk import *

def setup():
    # Option order parameters
    today = datetime.date.today()
    friday = today + datetime.timedelta(weeks=1) + datetime.timedelta( (4-today.weekday()) % 7 )
    readableExpiration = datetime.date.strftime(friday, '%m%d%Y')
        
    option: OptionContract = {
        "ticker": "AVAX",
        "expiration": readableExpiration, # The next nearest friday from today
        "strike": ["87.02", "84.0"], # Note that the ordering of the strikes is always [long, short] for spreads and always [long, 0] for single calls/puts
        "contractType": 3 # 0 for call, 1 for put, 2 for call spread, and 3 for put spread
    }
        
    # Get current price of underlying asset from Binance/CryptoWatch and 12 weeks of price history from CoinGecko.
    option["spotPrice"] = getUnderlierSpotPrice(option["ticker"])
    option["priceHistory"] = getUnderlierMarketChart(option["ticker"])[0] # priceHistory
        
    # Estimate option price by making API request.
    optionOrderParams: OptionOrderParams = {
        "quantity": 2.0, # 2.0 contracts
        "orderType": 0
    }
    optionOrderParams.update(option)

    return optionOrderParams

def test_estimate_option_price():
    optionOrderParams = setup()
    estimatedOptionPrice = estimateOptionPrice(optionOrderParams)

    assert isinstance(estimatedOptionPrice, float)
    assert estimatedOptionPrice > 0

def test_recommended_option():
    optionOrderParams = setup()
    # atSpotPriceForecast = optionOrderParams["spotPrice"]
    # belowSpotPriceForecast = optionOrderParams["spotPrice"] - 1.00
    aboveSpotPriceForecast = optionOrderParams["spotPrice"] + 1.00

    priceHistory = [entry[1] for entry in optionOrderParams["priceHistory"]]
    recommendedOption = getRecommendedOption(
        optionOrderParams["ticker"],
        optionOrderParams["expiration"],
        aboveSpotPriceForecast,
        optionOrderParams["spotPrice"],
        priceHistory
    )
        
    assert recommendedOption is not None
    assert list(recommendedOption.keys()) == ['ticker', 'expiration', 'strike', 'contractType', 'price', 'greeks']
    assert recommendedOption["contractType"] == 0
    assert list(recommendedOption["greeks"].keys()) == ['delta', 'gamma', 'rho', 'theta', 'vega']

def test_strike_grid():
    optionOrderParams = setup()
    priceHistory = [entry[1] for entry in optionOrderParams["priceHistory"]]
    strikeGrid = getStrikeGrid(
        optionOrderParams["orderType"],
        optionOrderParams["ticker"],
        optionOrderParams["expiration"],
        0,
        optionOrderParams["spotPrice"],
        priceHistory
    )
        
    assert strikeGrid is not None
    assert len(strikeGrid) > 0
    assert list(strikeGrid[0].keys()) == ['ticker', 'expiration', 'strike', 'contractType', 'price', 'greeks']
    assert list(strikeGrid[0]["greeks"].keys()) == ['delta', 'gamma', 'rho', 'theta', 'vega']
