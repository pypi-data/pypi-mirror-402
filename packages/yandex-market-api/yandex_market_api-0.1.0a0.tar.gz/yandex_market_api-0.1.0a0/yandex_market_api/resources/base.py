from yandex_market_api.client import ApiClient


class BaseResource:
    def __init__(self, client: ApiClient) -> None:
        self._client: ApiClient = client
