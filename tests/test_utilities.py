import pytest
import sys
import os.path
# appending the parent directory path
sys.path.append(os.path.dirname(__file__)+'/../src/')
from utilities import *

def test_router_contract():
    v4Router = getRouterContract("v4")
    contestRouter = getRouterContract("competition")

    assert v4Router.address == '0xc4dADDc8b63B74939E8906c8EEb11572948307B4'
    assert contestRouter.address == '0x9857F37d83f6f2D777E37613C2466d9e7F8A3ad9'

def test_stablecoin_contract():
    v4Stablecoin = getStablecoinContract("v4")
    contestStablecoin = getStablecoinContract("competition")

    assert v4Stablecoin.address == '0x45ea5d57BA80B5e3b0Ed502e9a08d568c96278F9'
    assert contestStablecoin.address == '0x1912AD1949fd370B9B6C362f1c005A16bf9Ae59c'

def test_events_contract():
    v4Events = getEventsContract("v4")
    contestEvents = getEventsContract("competition")

    assert v4Events.address == '0xd1283BfdbD7Ed06E11B9c7922E4Eb286f6b98EfE'
    assert contestEvents.address == '0xed8f176a4E9f956B20125C9E8f9fA7639Fb9F27F'

def test_registry_contract():
    v4Registry = getRegistryContract("v4")
    contestRegistry = getRegistryContract("competition")

    assert v4Registry.address == '0x6c5764fcbcA221693a963dD7dFBe62207e6D6268'
    assert contestRegistry.address == '0x880eBd1F783890a983c0Ca3B58a3627a02A22a96'

def test_compute_option_chain():
    optionChainAddress = computeOptionChainAddress("BTC", 10072022)
        
    assert isinstance(optionChainAddress, str)
    assert optionChainAddress == '0x023B5Caf9C0D9eFAAe6CFAEaD88126670a0aee9B'

def test_current_utc_time():
    currentTimeUTC = getCurrentTimeUTC()

    assert isinstance(currentTimeUTC["millisTimestamp"], int)
    assert isinstance(currentTimeUTC["readableTimestamp"], str)
    assert isinstance(currentTimeUTC["unixTimestamp"], int)

def test_readable_timestamp():
    readableTimestamp = getReadableTimestamp(1664879367000)

    assert isinstance(readableTimestamp, str)
    assert readableTimestamp == '10042022'

def test_get_utc_time():
    utcTime = getTimeUTC(1664879367000)
       
    assert isinstance(utcTime["unixTimestamp"], int)
    assert isinstance(utcTime["millisTimestamp"], int)
    assert isinstance(utcTime["readableTimestamp"], str)
    assert utcTime["readableTimestamp"] == '10042022'
    assert utcTime["unixTimestamp"] == 1664879367
    assert utcTime["millisTimestamp"] == 1664879367000

def test_get_expiration_timestamp():
    validExpiration = getExpirationTimestamp('10072022')

    assert isinstance(validExpiration["unixTimestamp"], int)
    assert isinstance(validExpiration["millisTimestamp"], int)
    assert validExpiration["unixTimestamp"] == 1665129600
    assert validExpiration["millisTimestamp"] == 1665129600000

def test_expiration_exception():
    with pytest.raises(UNSUPPORTED_EXPIRATION_ERROR):
        getExpirationTimestamp('10042022')

def test_is_friday():
    notFriday = isFriday(1665052167)
    friday = isFriday(1665138567)
        
    assert notFriday == False
    assert friday == True

def test_valid_version():
    valid = isValidVersion("v4")
    invalid = isValidVersion("INVALID")
        
    assert invalid == False
    assert valid == True

def test_prepare_deliver_option():
    # Option order parameters
    key = '65acf45f04d6c793712caa5aba61a9e3d2f9194e1aae129f9ca6fe39a32d159f' # Public facing test account

    today = datetime.date.today()
    friday = today + datetime.timedelta(weeks=1) + datetime.timedelta( (4-today.weekday()) % 7 )
    readableExpiration = datetime.date.strftime(friday, '%m%d%Y')
        
    option: OptionContract = {
        "ticker": "AVAX",
        "expiration": readableExpiration, # The next nearest friday from today
        "strike": [87.02, 84.0], # Note that the ordering of the strikes is always [long, short] for spreads and always [long, 0] for single calls/puts
        "contractType": 3 # 0 for call, 1 for put, 2 for call spread, and 3 for put spread
    }
        
    # Get current price of underlying asset from Binance/CryptoWatch and 12 weeks of price history from CoinGecko.
    option["spotPrice"] = getUnderlierSpotPrice(option["ticker"])
    option["priceHistory"] = getUnderlierMarketChart(option["ticker"])[1] # priceHistory
        
    # Estimate option price by making API request.
    optionOrderParams: OptionOrderParams = {
        "quantity": 2.0, # 2.0 contracts
        "orderType": 0
    }
    optionOrderParams.update(option)

    optionOrderParams["thresholdPrice"] = 1.0

    deliverOptionParams = prepareDeliverOptionParams(optionOrderParams, "v4")

    assert deliverOptionParams != None