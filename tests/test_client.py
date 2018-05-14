import inspect
import glob
import os
import sys

import pytest

import ib_async
import ib_async.functionality
import ib_async.protocol


def test_all_functionality_included():
    for path in glob.glob(os.path.dirname(ib_async.functionality.__file__) + "/*.py"):
        module_name = "ib_async.functionality." + os.path.basename(path)[:-3]
        if module_name.endswith('.__init__'):
            continue

        module = sys.modules.get(module_name)
        assert module, "%s not imported" % module_name

        for member_name in dir(module):
            if 'A' <= member_name[0] <= 'Z':
                member = getattr(module, member_name)
                if issubclass(member, ib_async.protocol.ProtocolInterface):
                    assert issubclass(ib_async.IBClient, member)


def test_handlers_valid():
    for member in dir(ib_async.IBClient):
        if not member.startswith('_handle_'):
            continue

        message_name = member[len('_handle_'):].upper()

        if not hasattr(ib_async.protocol.Incoming, message_name):
            pytest.fail("handler for unknown message %s" % message_name)

        signature = inspect.signature(getattr(ib_async.IBClient, member))
        parameters = list(signature.parameters.values())[1:]

        for parameter in parameters:
            if parameter.kind == 2:
                continue  # *args declaration

            annotation = parameter.annotation
            if annotation is ib_async.protocol.IncomingMessage:
                if parameter.name != 'message':
                    pytest.fail("IBClient.%s %s parameter should be named 'message'" % (
                        member, parameter.name
                    ))
            elif annotation is inspect.Parameter.empty:
                pytest.fail("IBClient.%s %s parameter is untyped" % (
                    member, parameter.name
                ))
