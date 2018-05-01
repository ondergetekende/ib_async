import enum
import typing  # noqa


class MarketDataTimeliness(enum.Enum):
    RealTime = 1
    Frozen = 2
    Delayed = 3
    DelayedFrozen = 4


class TickAttributes(enum.IntEnum):  # Actually an IntFlag, but that's not supported by py35
    CanAutoExecute = 0x01
    PastLimit = 0x02
    PreOpen = 0x04

    @classmethod
    def list_from_int(cls, val) -> typing.List["TickAttributes"]:
        key = 1
        result = []  # type: typing.List[TickAttributes]
        while val:
            if val & key:
                result.append(cls(key))
                val -= key

        return result


class TickTypeGroup(enum.Enum):
    Fundamentals = 47
    # IBDividends = 59

    Volume = 100  # currently for stocks
    OpenInterest = 101  # currently for stocks
    HistoricalVolatility = 104  # currently for stocks
    AverageVolume = 105  # currently for stocks
    ImpliedVolatility = 106
    ClImpliedVolatility = 107
    BondAnalyticData = 125

    IndexFuturePremium = 162
    MiscellaneousStats = 165
    CScreen = 166
    # MarkPrice = 220  # used in TWS P&L computations
    MarkPrice = 221  # used in TWS P&L computations
    Auction = 225  # volume, price and imbalance
    PlPrice = 232
    RTVolume = 233  # last trade price, last trade size, last trade time, total volume, VWAP, and single trade flag
    Shortable = 236
    Inventory = 256
    FundamentalRatios = 258
    InventoryClose = 291
    TradeCount = 293
    TradeRate = 294
    VolumeRate = 295
    LastRTHTrade = 318
    ParticipationMonitor = 370
    RTTrdVolume = 375
    CttTickTag = 377
    IBRate = 381
    RfqTickRespTag = 384
    DMM = 387
    IssuerFundamentals = 388
    IBWarrantImpVolCompeteTick = 391
    IndexCapabilities = 405
    FuturesMargins = 407
    RealtimeHistoricalVolatility = 411
    MonetaryClosePrice = 428
    MonitorTickTag = 439
    IBDividends = 456
    RTCLOSE = 459
    BondFactorMultiplier = 460
    FeeAndRebateRate = 499
    Midptiv = 506
    hvolrt10 = 511  # (per-underlying)
    hvolrt30 = 512  # (per-underlying)
    hvolrt50 = 513  # (per-underlying)
    hvolrt75 = 514  # (per-underlying)
    hvolrt100 = 515  # (per-underlying)
    hvolrt150 = 516  # (per-underlying)
    hvolrt200 = 517  # (per-underlying)
    fzmidptiv = 521
    vsiv = 545
    EtfNavBidAsk = 576  # (navbidask)
    EtfNavLast = 577  # (navlast)
    EtfNavClose = 578  # (navclose)
    AverageOpeningVolume = 584
    AverageClosingVolume = 585
    PlPriceDelayed = 587
    FuturesOpenInterest = 588
    ShorttermVolumeXMins = 595
    EMA_N = 608
    EtfNavMisc = 614  # (hight/low)
    CreditmanSlowMarkPrice = 619
    EtfFrozenNavLast = 623  # (fznavlast)
    # MonetaryClosePrice = 645
    AverageVolume1min = 658


class TickType(enum.Enum):
    # Number of contracts or lots offered at the bid price.
    BidSize = 0

    # Highest priced bid for the contract.
    Bid = 1

    # Lowest price offer on the contract.
    Ask = 2

    # Number of contracts or lots offered at the ask price.
    AskSize = 3

    # Last price at which the contract traded.
    Last = 4

    # Number of contracts or lots traded at the last price.
    LastSize = 5

    # High price for the day.
    High = 6

    # Low price for the day.
    Low = 7

    # Trading volume for the day for the selected contract (US Stocks: multiplier 100).
    Volume = 8

    # The last available closing price for the previous day. For US Equities, IB uses corporate action processing to
    # get the closing price, so the close price is adjusted to reflect forward and reverse splits and cash and
    # stock dividends.
    ClosePrice = 9

    # Computed Greeks for the underlying stock price and the option reference price.
    BidOption = 10

    # Computed Greeks for the underlying stock price and the option reference price.
    AskOption = 11

    # Computed Greeks for the underlying stock price and the option reference price.
    LastOption = 12

    # Computed Greeks and model's implied volatility for the underlying stock price and the option reference price.
    ModelOption = 13

    # Today's opening price.
    OpenTick = 14

    # Lowest price for the last 13 weeks.
    Low13Weeks = 15

    # Highest price for the last 13 weeks.
    High13Weeks = 16

    # Lowest price for the last 26 weeks.
    Low26Weeks = 17

    # Highest price for the last 26 weeks.
    High26Weeks = 18

    # Lowest price for the last 52 weeks.
    Low52Weeks = 19

    # Highest price for the last 52 weeks.
    High52Weeks = 20

    # The average daily trading volume over 90 days (multiply this value times 100).
    AverageVolume = 21

    # Total number of options that were not closed.
    OpenInterest = 22

    # The 30-day historical volatility (currently for stocks).
    OptionHistoricalVolatility = 23

    # A prediction of how volatile an underlying will be in the future. The IB 30-day volatility is the at-market
    # volatility estimated for a maturity thirty calendar days forward of the current trading day, and is based on
    # option prices from two consecutive expiration months.
    OptionImpliedVolatility = 24

    # Not Used.
    OptionBidExchange = 25

    # Not Used.
    OptionAskExchange = 26

    # Call option open interest.
    OptionCallOpenInterest = 27

    # Put option open interest.
    OptionPutOpenInterest = 28

    # Call option volume for the trading day.
    OptionCallVolume = 29

    # Put option volume for the trading day.
    OptionPutVolume = 30

    # The number of points that the index is over the cash index.
    IndexFuturePremium = 31

    # Identifies the options exchange(s) posting the best bid price on the options contract.
    BidExchange = 32

    # Identifies the options exchange(s) posting the best ask price on the options contract.
    AskExchange = 33

    # The number of shares that would trade if no new orders were received and the auction were held now.
    AuctionVolume = 34

    # The price at which the auction would occur if no new orders were received and the auction were held now.
    # The indicative price for the auction.
    AuctionPrice = 35

    # The number of unmatched shares for the next auction; returns how many more shares are on one side of the auction
    # than the other.
    AuctionImbalance = 36

    # The mark price is equal to the Last Price unless: Ask < Last - the mark price is equal to the Ask Price. Bid >
    # Last - the mark price is equal to the Bid Price.
    MarkPrice = 37

    BidEFP = 38
    AskEFP = 39
    LastEFP = 40
    OpenEFP = 41
    HighEFP = 42
    LowEFP = 43
    CloseEFP = 44

    # Time of the last trade (in UNIX time).
    LastTimestamp = 45

    # Describes the level of difficulty with which the contract can be sold short.
    Shortable = 46

    # Provides the available Reuter's Fundamental Ratios.
    FundamentalRatios = 47

    # (Time & Sales) Last trade details.
    RTVolume = 48

    # Indicates if a contract is halted.
    Halted = 49

    # Implied yield of the bond if it is purchased at the current bid.
    BidYield = 50

    # Implied yield of the bond if it is purchased at the current ask.
    AskYield = 51

    # Implied yield of the bond if it is purchased at the last price.
    LastYield = 52

    # Greek values are based off a user customized price.
    CustomOption = 53

    # Trade count for the day.
    TradeCount = 54

    # Trade count per minute.
    TradeRate = 55

    # Volume per minute.
    VolumeRate = 56

    # Last Regular Trading Hours traded price.
    LastRTHTrade = 57

    # 30-day real time historical volatility.
    RTHistoricalVolatility = 58

    # Contract's dividends.
    IBDividends = 59

    # DESC	METHOD
    BondFactorMultiplier = 60

    # The imbalance that is used to determine which at-the-open or at-the-close orders can be entered following the
    # publishing of the regulatory imbalance.
    RegulatoryImbalance = 61

    # Contract's news feed.
    News = 62

    # The past three minutes volume. Interpolation may be applied.
    ShortTermVolume3Minutes = 63

    # The past five minutes volume. Interpolation may be applied.
    ShortTermVolume5Minutes = 64

    # The past ten minutes volume. Interpolation may be applied.
    ShortTermVolume10Minutes = 65

    # Delayed bid price.
    DelayedBid = 66

    # Delayed ask price.
    DelayedAsk = 67

    # Delayed last traded price.
    DelayedLast = 68

    # Delayed bid size.
    DelayedBidSize = 69

    # Delayed ask size.
    DelayedAskSize = 70

    # Delayed last size.
    DelayedLastSize = 71

    # Delayed highest price of the day.
    DelayedHighPrice = 72

    # Delayed lowest price of the day.
    DelayedLowPrice = 73

    # Delayed traded volume of the day.
    DelayedVolume = 74

    # Delayed close price for the day.
    DelayedClose = 75

    # Delayed open price for the day.
    DelayedOpen = 76

    # Last trade details that excludes "Unreportable Trades".
    # The RT Volume tick type corresponds to the TWS' Time & Sales window and contains the last trade's price, size and
    # time along with current day's total traded volume, Volume Weighted Average Price (VWAP) and whether or not the
    # trade was filled by a single market maker.
    RTTradeVolume = 77

    CreditmanMarkPrice = 78  # Not currently available
    # Slower mark price update used in system calculations
    CreditmanSlowMarkPrice = 79

    # Computed greeks based on delayed bid price.
    DelayedBidOption = 80
    # Computed greeks based on delayed ask price.
    DelayedAskOption = 81
    # Computed greeks based on delayed last price.
    DelayedLastOption = 82
    # Computed Greeks and model's implied volatility based on delayed stock and option prices.
    DelayedModelOption = 83
    # Exchange of last traded price
    LastExchange = 84
    # Timestamp (in Unix ms time) of last trade returned with regulatory snapshot
    LastRegulatoryTime = 85
    # Average volume of the corresponding option contracts
    AverageOptionVolume = 87
    # Delayed time of the last trade (in UNIX time)
    DelayedLastTimestamp = 88

    # fill the missing gap
    UNKNOWN_86 = 86
