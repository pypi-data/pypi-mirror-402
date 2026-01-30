from yandex_market_api.resources.base import BaseResource


class OffersResource(BaseResource):
    async def update_offer_mappings(
        self, business_id: int, body: dict, language: str | None = None
    ) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/offer-mappings/update",
            json=body,
            params={"language": language},
        )

    async def update_campaign_offers(self, campaign_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/campaigns/{campaign_id}/offers/update",
            json=body,
        )

    async def generate_offer_barcodes(self, business_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v1/businesses/{business_id}/offer-mappings/barcodes/generate",
            json=body,
        )

    async def get_offer_cards_status(
        self, business_id: int, body: dict, limit: int | None = None, page_token: str | None = None
    ) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/offer-cards",
            json=body,
            params={"limit": limit, "page_token": page_token},
        )

    async def update_offer_cards(self, business_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/offer-cards/update",
            json=body,
        )

    async def list_offer_mappings(
        self,
        business_id: int,
        body: dict | None = None,
        language: str | None = None,
        limit: int | None = None,
        page_token: str | None = None,
    ) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/offer-mappings",
            json=body,
            params={"language": language, "limit": limit, "page_token": page_token},
        )

    async def list_campaign_offers(
        self,
        campaign_id: int,
        body: dict | None = None,
        language: str | None = None,
        limit: int | None = None,
        page_token: str | None = None,
    ):
        return await self._client.request(
            method="POST",
            path=f"/v2/campaigns/{campaign_id}/offers",
            json=body,
            params={"language": language, "limit": limit, "page_token": page_token},
        )

    async def delete_offer_mappings(self, business_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/offer-mappings/delete",
            json=body,
        )

    async def delete_campaign_offers(self, campaign_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/campaigns/{campaign_id}/offers/delete",
            json=body,
        )

    async def list_hidden_campaign_offers(
        self,
        campaign_id: int,
        offer_id: str | None = None,
        limit: int | None = None,
        page_token: str | None = None,
    ) -> dict:
        return await self._client.request(
            method="GET",
            path=f"/v2/campaigns/{campaign_id}/hidden-offers",
            params={"offer_id": offer_id, "limit": limit, "page_token": page_token},
        )

    async def hide_campaign_offers(self, campaign_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/campaigns/{campaign_id}/hidden-offers",
            json=body,
        )

    async def unhide_campaign_offers(self, campaign_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/campaigns/{campaign_id}/hidden-offers/delete",
            json=body,
        )

    async def archive_offer_mappings(self, business_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/offer-mappings/archive",
            json=body,
        )

    async def unarchive_offer_mappings(self, business_id: int, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/businesses/{business_id}/offer-mappings/unarchive",
            json=body,
        )
