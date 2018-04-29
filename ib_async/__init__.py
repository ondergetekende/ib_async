from ib_async.functionality.current_time import CurrentTimeMixin
from ib_async.functionality.matching_symbols import MatchingSymbolsMixin
from ib_async.functionality.instrument_details import ContractDetailsMixin

from ib_async.protocol import Protocol


class IBClient(CurrentTimeMixin, MatchingSymbolsMixin, ContractDetailsMixin,
               Protocol):
    # All of the functionality is delegated to the mixins and Protocol.
    pass
