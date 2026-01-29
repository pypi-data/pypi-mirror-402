# Foru.ms Python Library

![](https://foru.ms/images/cover.png)

[![fern shield](https://img.shields.io/badge/%F0%9F%8C%BF-Built%20with%20Fern-brightgreen)](https://buildwithfern.com?utm_source=github&utm_medium=github&utm_campaign=readme&utm_source=https%3A%2F%2Fgithub.com%2Fforu-ms%2Fpython-sdk)
[![pypi](https://img.shields.io/pypi/v/foru-ms-sdk)](https://pypi.python.org/pypi/foru-ms-sdk)

The Foru.ms Python library provides convenient access to the Foru.ms APIs from Python.

## Table of Contents

- [Documentation](#documentation)
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

## Documentation

API reference documentation is available [here](https://foru.ms/docs/api-reference).

## Installation

```sh
pip install foru-ms-sdk
```

## Reference

A full reference for this library is available [here](https://github.com/foru-ms/python-sdk/blob/HEAD/./reference.md).

## Usage

Instantiate and use the client with the following:

```python
from foru_ms_sdk import ForumClient

client = ForumClient(
    api_key="YOUR_API_KEY",
)
client.auth.register(
    username="username",
    email="email",
    password="password",
)
```

## Async Client

The SDK also exports an `async` client so that you can make non-blocking calls to our API. Note that if you are constructing an Async httpx client class to pass into this client, use `httpx.AsyncClient()` instead of `httpx.Client()` (e.g. for the `httpx_client` parameter of this client).

```python
import asyncio

from foru_ms_sdk import AsyncForumClient

client = AsyncForumClient(
    api_key="YOUR_API_KEY",
)


async def main() -> None:
    await client.auth.register(
        username="username",
        email="email",
        password="password",
    )


asyncio.run(main())
```

## Exception Handling

When the API returns a non-success status code (4xx or 5xx response), a subclass of the following error
will be thrown.

```python
from foru_ms_sdk.core.api_error import ApiError

try:
    client.auth.register(...)
except ApiError as e:
    print(e.status_code)
    print(e.body)
```

## Advanced

### Access Raw Response Data

The SDK provides access to raw response data, including headers, through the `.with_raw_response` property.
The `.with_raw_response` property returns a "raw" client that can be used to access the `.headers` and `.data` attributes.

```python
from foru_ms_sdk import ForumClient

client = ForumClient(
    ...,
)
response = client.auth.with_raw_response.register(...)
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
client.auth.register(..., request_options={
    "max_retries": 1
})
```

### Timeouts

The SDK defaults to a 60 second timeout. You can configure this with a timeout option at the client or request level.

```python

from foru_ms_sdk import ForumClient

client = ForumClient(
    ...,
    timeout=20.0,
)


# Override timeout for a specific method
client.auth.register(..., request_options={
    "timeout_in_seconds": 1
})
```

### Custom Client

You can override the `httpx` client to customize it for your use-case. Some common use-cases include support for proxies
and transports.

```python
import httpx
from foru_ms_sdk import ForumClient

client = ForumClient(
    ...,
    httpx_client=httpx.Client(
        proxy="http://my.test.proxy.example.com",
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
    ),
)
```

