import pytest
import sys
import os.path
# appending the parent directory path
sys.path.append(os.path.dirname(__file__)+'/../')
from utilities import *

def test_router_contract():
    v4Router = getRouterContract("v4")
    v3Router = getRouterContract("v3")
    contestRouter = getRouterContract("competition")

    assert v4Router.address == '0xa6EA0E47501627a964e11E31D2BD7D40452dff6F'
    assert v3Router.address == '0x31122CeF9891Ef661C99352266FA0FF0079a0e06'
    assert contestRouter.address == '0x33D1a0529D0C23f183fF1de346BDcA029dB0046E'

def test_stablecoin_contract():
    v4Stablecoin = getStablecoinContract("v4")
    v3Stablecoin = getStablecoinContract("v3")
    contestStablecoin = getStablecoinContract("competition")

    assert v4Stablecoin.address == '0x45ea5d57BA80B5e3b0Ed502e9a08d568c96278F9'
    assert v3Stablecoin.address == '0x45ea5d57BA80B5e3b0Ed502e9a08d568c96278F9'
    assert contestStablecoin.address == '0x6b8dA544EB543d7f3B533d79267b778e7427B288'

def test_events_contract():
    v4Events = getEventsContract("v4")
    v3Events = getEventsContract("v3")
    contestEvents = getEventsContract("competition")

    assert v4Events.address == '0xAF0bbA63B8B14e57B817CA6410978d75BBb65854'
    assert v3Events.address == '0x932BC618C972Ef2703cD66A751747d71e7A1BB3D'
    assert contestEvents.address == '0x4dc28938e5112c5729E582F80363f26982Afcc50'

def test_registry_contract():
    v4Registry = getRegistryContract("v4")
    v3Registry = getRegistryContract("v3")
    contestRegistry = getRegistryContract("competition")

    assert v4Registry.address == '0x20cee0F261F36A0CBcC3D38511D96C3AE0769706'
    assert v3Registry.address == '0xe72175c1b3A9A287302276491bfb9ad275842876'
    assert contestRegistry.address == '0x342F0b981a90c9fD70483Bb85CfB897b1A6091Dc'

def test_compute_option_chain():
    optionChainAddress = computeOptionChainAddress("BTC", 10072022)
        
    assert isinstance(optionChainAddress, str)
    assert optionChainAddress == '0x5c8134cD585431032ae752fbfc8f1508711D8285'

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
    valid = isValidVersion("v3")
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