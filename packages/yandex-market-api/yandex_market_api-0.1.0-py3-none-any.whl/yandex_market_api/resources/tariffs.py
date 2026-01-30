from yandex_market_api.resources.base import BaseResource


class TariffsResource(BaseResource):
    async def calculate_tariffs(self, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path="/v2/tariffs/calculate",
            json=body,
        )
