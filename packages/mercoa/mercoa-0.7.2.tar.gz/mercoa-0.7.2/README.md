# Mercoa Python Library

[![fern shield](https://img.shields.io/badge/%F0%9F%8C%BF-Built%20with%20Fern-brightgreen)](https://buildwithfern.com?utm_source=github&utm_medium=github&utm_campaign=readme&utm_source=https%3A%2F%2Fgithub.com%2Fmercoa-finance%2Fpython)
[![pypi](https://img.shields.io/pypi/v/mercoa)](https://pypi.python.org/pypi/mercoa)

The Mercoa Python library provides convenient access to the Mercoa APIs from Python.

## Table of Contents

- [Installation](#installation)
- [Reference](#reference)
- [Usage](#usage)
- [Async Client](#async-client)
- [Exception Handling](#exception-handling)
- [Advanced](#advanced)
  - [Access Raw Response Data](#access-raw-response-data)
  - [Retries](#retries)
  - [Timeouts](#timeouts)
  - [Custom Client](#custom-client)
- [Contributing](#contributing)

## Installation

```sh
pip install mercoa
```

## Reference

A full reference for this library is available [here](https://github.com/mercoa-finance/python/blob/HEAD/./reference.md).

## Usage

Instantiate and use the client with the following:

```python
from mercoa import Mercoa
from mercoa.entity_group_types import EntityGroupCreateRequest

client = Mercoa(
    token="YOUR_TOKEN",
)
client.entity_group.create(
    request=EntityGroupCreateRequest(
        foreign_id="your-group-id",
        name="Coastal Corporation",
        email_to_name="coastalcorp",
        entity_ids=[
            "ent_e8c2af94-61cd-4036-a765-80341209167b",
            "ent_1176dd0c-12e1-41c7-85a5-ae9b4746e64b",
            "ent_3dbb4ede-2d1d-49be-a996-a5dfad3641be",
        ],
    ),
)
```

## Async Client

The SDK also exports an `async` client so that you can make non-blocking calls to our API.

```python
import asyncio

from mercoa import AsyncMercoa
from mercoa.entity_group_types import EntityGroupCreateRequest

client = AsyncMercoa(
    token="YOUR_TOKEN",
)


async def main() -> None:
    await client.entity_group.create(
        request=EntityGroupCreateRequest(
            foreign_id="your-group-id",
            name="Coastal Corporation",
            email_to_name="coastalcorp",
            entity_ids=[
                "ent_e8c2af94-61cd-4036-a765-80341209167b",
                "ent_1176dd0c-12e1-41c7-85a5-ae9b4746e64b",
                "ent_3dbb4ede-2d1d-49be-a996-a5dfad3641be",
            ],
        ),
    )


asyncio.run(main())
```

## Exception Handling

When the API returns a non-success status code (4xx or 5xx response), a subclass of the following error
will be thrown.

```python
from mercoa.core.api_error import ApiError

try:
    client.entity_group.create(...)
except ApiError as e:
    print(e.status_code)
    print(e.body)
```

## Advanced

### Access Raw Response Data

The SDK provides access to raw response data, including headers, through the `.with_raw_response` property.
The `.with_raw_response` property returns a "raw" client that can be used to access the `.headers` and `.data` attributes.

```python
from mercoa import Mercoa

client = Mercoa(
    ...,
)
response = client.entity_group.with_raw_response.create(...)
print(response.headers)  # access the response headers
print(response.data)  # access the underlying object
```

### Retries

The SDK is instrumented with automatic retries with exponential backoff. A request will be retried as long
as the request is deemed retryable and the number of retry attempts has not grown larger than the configured
retry limit (default: 2).

A request is deemed retryable when any of the following HTTP status codes is returned:

- [408](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/408) (Timeout)
- [429](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429) (Too Many Requests)
- [5XX](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/500) (Internal Server Errors)

Use the `max_retries` request option to configure this behavior.

```python
client.entity_group.create(..., request_options={
    "max_retries": 1
})
```

### Timeouts

The SDK defaults to a 60 second timeout. You can configure this with a timeout option at the client or request level.

```python

from mercoa import Mercoa

client = Mercoa(
    ...,
    timeout=20.0,
)


# Override timeout for a specific method
client.entity_group.create(..., request_options={
    "timeout_in_seconds": 1
})
```

### Custom Client

You can override the `httpx` client to customize it for your use-case. Some common use-cases include support for proxies
and transports.

```python
import httpx
from mercoa import Mercoa

client = Mercoa(
    ...,
    httpx_client=httpx.Client(
        proxies="http://my.test.proxy.example.com",
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
    ),
)
```

## Contributing

While we value open-source contributions to this SDK, this library is generated programmatically.
Additions made directly to this library would have to be moved over to our generation code,
otherwise they would be overwritten upon the next generated release. Feel free to open a PR as
a proof of concept, but know that we will not be able to merge it as-is. We suggest opening
an issue first to discuss with us!

On the other hand, contributions to the README are always very welcome!
