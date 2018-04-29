
class ApiException(Exception):
    def __init__(self, code:int, message: str):
        self.error_code = code
        self.error_message = message


class NotConnectedError(Exception):
    error_code = 504

    def __str__(self):
        return "Client is not connected"


class OutdatedServerError(Exception):
    error_code = 502

    def __init__(self, feature=None):
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
