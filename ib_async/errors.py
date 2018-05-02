class ApiException(Exception):
    def __init__(self, code: int, message: str) -> None:
        self.error_code = code
        self.error_message = message


class NotConnectedError(Exception):
    error_code = 504

    def __str__(self):
        return "Client is not connected"


class OutdatedServerError(Exception):
    error_code = 502

    def __init__(self, feature=None) -> None:
        self.feature = feature

    def __str__(self):
        result = "The TWS is out of date and must be upgraded."
        if self.feature:
            result += " It does not support %s." % self.feature

        return result


class UnsupportedServerVersion(Exception):
    error_code = 506
    msg = "Unsupported version"


class SocketException(Exception):
    error_code = 509
    msg = "Exception caught while reading socket - "


class SocketCreationException(SocketException):
    error_code = 520
    msg = "Failed to create socket"


class ConnectionFailed(SocketException):
    error_code = 502
    msg = ("Couldn't connect to TWS. Confirm that \"Enable ActiveX and Socket EClients\" "
           "is enabled and connection port is the same as \"Socket Port\" on the "
           "TWS \"Edit->Global Configuration...->API->Settings\" menu. Live Trading ports: "
           "TWS: 7496; IB Gateway: 4001. Simulated Trading ports for new installations "
           "of version 954.1 or newer:  TWS: 7497; IB Gateway: 4002")


class UnsupportedFeature(NotImplementedError):
    def __init__(self, feature):
        super().__init__("ib_async does not yet support %s. Please contact the author if you need this implemented." %
                         feature)


warning_codes = {
    # Requested market data is not subscribed. Displaying delayed market data
    10167,

    # New account data requested from TWS. API client has been unsubscribed from account data.
    # The TWS only allows one IBApi.EClient.reqAccountUpdates request at a time. If the client application attempts to
    # subscribe to a second account without canceling the previous subscription, the new request will override the old
    # one and the TWS will send this message notifying so.
    2100,

    # Unable to subscribe to account as the following clients are subscribed to a different account.
    # If a client application invokes IBApi.EClient.reqAccountUpdates when there is an active subscription started
    # by a different client, the TWS will reject the new subscription request with this message.
    2101,

    # Unable to modify this order as it is still being processed.
    # If you attempt to modify an order before it gets processed by the system, the modification will be rejected.
    # Wait until the order has been fully processed before modifying it. See Placing Orders for further details.
    2102,
    # A market data farm is disconnected.
    # Indicates a connectivity problem to an IB server. Outside of the nightly IB server reset, this typically
    # indicates an underlying ISP connectivity issue.
    2103,
    # Market data farm connection is OK
    # A notification that connection to the market data server is ok. This is a notification and not a true error
    # condition, and is expected on first establishing connection.
    2104,
    # A historical data farm is disconnected.
    # Indicates a connectivity problem to an IB server. Outside of the nightly IB server reset, this typically
    # indicates an underlying ISP connectivity issue.
    2105,
    # A historical data farm is connected.
    # A notification that connection to the market data server is ok. This is a notification and not a true error
    # condition, and is expected on first establishing connection.
    2106,
    # A historical data farm connection has become inactive but should be available upon demand.
    # Whenever a connection to the historical data farm is not being used because there is not an active historical
    # data request, the connection will go inactive in IB Gateway. This does not indicate any connectivity issue or
    # problem with IB Gateway. As soon as a historical data request is made the status will change back to active.
    2107,

    # A market data farm connection has become inactive but should be available upon demand.
    # Whenever a connection to our data farms is not needed, it will become dormant. There is nothing abnormal nor
    # wrong with your client application nor with the TWS. You can safely ignore this message.
    2108,

    # Order Event Warning: Attribute "Outside Regular Trading Hours" is ignored based on the order type and
    # destination. PlaceOrder is now processed.
    # Indicates the outsideRth flag was set for an order for which there is not a regular vs outside regular trading
    # hour distinction
    2109,

    # Connectivity between TWS and server is broken. It will be restored automatically.
    # Indicates a connectivity problem between TWS or IBG and the IB server. This will usually only occur during the
    # IB nightly server reset; cases at other times indicate a problem in the local ISP connectivity.
    2110,

    # Cross Side Warning
    2137,
}
