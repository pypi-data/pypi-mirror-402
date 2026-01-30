from yandex_market_api.config import Config
import httpx


class ApiClient:
    def __init__(self, config: Config) -> None:
        self._config: Config = config
        self._client: httpx.AsyncClient = httpx.AsyncClient(
            base_url=self._config.base_url, headers={"Api-Key": self._config.api_key}
        )

    async def request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict:
        response = await self._client.request(method, path, params=params, json=json)

        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
