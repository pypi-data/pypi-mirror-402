from yandex_market_api.resources.base import BaseResource


class BusinessesResource(BaseResource):
    async def get_business_settings(self, business_id: int) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/settings",
        )
