from yandex_market_api.resources.base import BaseResource


class PricesResource(BaseResource):
    async def update_offer_prices(self, business_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/offer-prices/updates",
            json=body,
        )

    async def update_campaign_offer_prices(self, campaign_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/campaigns/{campaign_id}/offer-prices/updates",
            json=body,
        )

    async def list_offer_prices(
        self,
        business_id: int,
        body: dict | None = None,
        limit: int | None = None,
        page_token: str | None = None,
    ) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/offer-prices",
            json=body,
            params={"limit": limit, "page_token": page_token},
        )

    async def list_campaign_offer_prices(
        self,
        campaign_id: int,
        body: dict | None = None,
        limit: int | None = None,
        page_token: str | None = None,
    ) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/campaigns/{campaign_id}/offer-prices",
            json=body,
            params={"limit": limit, "page_token": page_token},
        )

    async def list_price_quarantine_offers(
        self,
        business_id: int,
        body: dict | None = None,
        limit: int | None = None,
        page_token: str | None = None,
    ) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/price-quarantine",
            json=body,
            params={"limit": limit, "page_token": page_token},
        )

    async def list_campaign_price_quarantine_offers(
        self,
        campaign_id: int,
        body: dict | None = None,
        limit: int | None = None,
        page_token: str | None = None,
    ) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/campaigns/{campaign_id}/price-quarantine",
            json=body,
            params={"limit": limit, "page_token": page_token},
        )

    async def confirm_price_quarantine(self, business_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/price-quarantine/confirm",
            json=body,
        )

    async def confirm_campaign_price_quarantine(self, campaign_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/campaigns/{campaign_id}/price-quarantine/confirm",
            json=body,
        )
