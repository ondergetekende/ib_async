[ ![Codeship Status for ondergetekende/ib_async](https://app.codeship.com/projects/2c7e6b90-2e79-0136-5387-6651c56c84d3/status?branch=master)](https://app.codeship.com/projects/288237)

An asynchronous implementation of an Interactive Brokers API client.

Design
---

This library grew out of frustration of the quality of `ib_api` and 
`ibridgepy`. These libraries are direct ports from the official IB C++/Java
client library, and as a result, don't fit well in the python world.

In contrast, `ib_async` was designed from the perspective of an end user. It 
attempts to be easy to use and easy to learn. At the moment, this library does 
not attempt to be feature complete. Instead, it tries to implement commonly 
used functionality well.

Examples
---

Obtain an instrument:

```python
import ib_async

client = ib_async.IBClient()
client.connect('127.0.0.1', 4001, 100)  # 100 is the client_id.
instrument = client.get_instrument_by_id('US0378331005', 'ISIN') 
```

Receiving market data for said instrument:
```python
async for tick_type in instrument.on_market_data:
    print(tick_type)
```

Or, if you prefer event handlers:
```python
def handle(tick_type):
    pass

instrument.on_market_data += handle
```

Features
---

* Fully asyncio-based
* All simple calls are awaitable (no need to register callbacks)
* Fully type annotated
* Support for python >= 3.5
* High test coverage

API Stability
---

This project uses semantic versionions. Starting with the release of 1.0.0, 
the API will be backward compatible within a major version, and forward 
compatible within a minor version. This applies to public methods, attributes 
and enums. Log messages and exact mypy types may change between versions, 
though. The protocol itself is not considered a public API.
 

Contributing
---

At the moment, development is mostly guided by the needs of the developer. If 
you need specific functionality, feel free to open an issue. If you need 
functionality urgently, feel free to contact the author for paid support.

Of course, pull-requests are always welcome. Pull requests are expected to pass
the test suite, and not reduce test coverage.

License
---

Copyright 2018 Koert van der Veer

Licensed under the Apache License, Version 2.0 (the "License"); you may not use 
this file except in compliance with the License. You may obtain a copy of the 
License [here](http://www.apache.org/licenses/LICENSE-2.0).

Unless required by applicable law or agreed to in writing, software 
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT 
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the 
License for the specific language governing permissions and limitations under 
the License.

**Note** depending on your jurisdiction, this library may be considered a 
derived work of Interactive Brokers intellectual property, and may need to be
licensed from them accordingly.





