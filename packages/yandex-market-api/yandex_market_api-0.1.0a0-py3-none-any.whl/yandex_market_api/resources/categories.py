from yandex_market_api.resources.base import BaseResource


class CategoriesResource(BaseResource):
    async def get_category_tree(self, body: dict | None = None) -> dict:
        return await self._client.request(
            method="POST",
            path="/v2/categories/tree",
            json=body,
        )

    async def list_category_parameters(
        self, category_id: int, business_id: int | None = None
    ) -> dict:
        return await self._client.request(
            method="POST",
            path=f"/v2/category/{category_id}/parameters",
            params={"businessId": business_id},
        )
