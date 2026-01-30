from yandex_market_api.resources.base import BaseResource


class RecommendationsResource(BaseResource):
    async def get_offer_price_recommendations(
        self,
        business_id: int,
        body: dict | None = None,
        limit: int | None = None,
        page_token: str | None = None,
    ) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/offers/recommendations",
            json=body,
            params={"limit": limit, "page_token": page_token},
        )
