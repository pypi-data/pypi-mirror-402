from yandex_market_api.resources.base import BaseResource


class CampaignsResource(BaseResource):
    async def list_campaigns(self, page: int = 1, page_size: int | None = None) -> dict:
        return await self._client.request(
            method="GET",
            path="/v2/campaigns",
            params={"page": page, "pageSize": page_size},
        )

    async def get_campaign(self, campaign_id: int) -> dict:
        return await self._client.request(
            method="GET",
            path=f"/v2/campaigns/{campaign_id}",
        )

    async def get_campaign_settings(self, campaign_id: int) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/campaigns/{campaign_id}/settings",
        )
