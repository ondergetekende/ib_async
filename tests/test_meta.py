# Tests about the tests or supporting code
import glob
import os
import sys

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
