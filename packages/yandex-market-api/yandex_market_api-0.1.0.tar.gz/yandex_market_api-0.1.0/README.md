# yandex-market-api

Async Python client for the **Yandex Market Partner API** (unofficial).

This library provides an asynchronous, resource-oriented interface for interacting with
the Yandex Market Partner API. It is designed as a thin, explicit SDK that mirrors the API
structure while following Python and async best practices.

---

## Features

- Fully asynchronous HTTP client based on `httpx`
- Resource-oriented design (`client.offers`, `client.campaigns`, etc.)
- Explicit and predictable method naming
- Python 3.10+ support
- Designed to be extended with typed models (Pydantic) over time

---

## Installation

The library can be installed from PyPI:

```bash
pip install yandex-market-api
```

Python 3.10 or newer is required.

---

## Quick start

```python
from yandex_market_api import YandexMarketClient
import asyncio

async def main() -> None:
    client = YandexMarketClient(api_key="YOUR_API_TOKEN")

    campaigns = await client.campaigns.list_campaigns()
    print(campaigns)

    await client.close()

asyncio.run(main())
```

The client is asynchronous, so it should be used inside an async context
(e.g. with `asyncio.run`).

---

## Project status

**Work in progress**

- Some endpoints are not implemented yet
- Request and response schemas are mostly returned as plain dictionaries
- Error handling and retries are still evolving