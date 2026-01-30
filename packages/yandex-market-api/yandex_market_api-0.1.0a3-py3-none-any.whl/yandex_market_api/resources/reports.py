from yandex_market_api.resources.base import BaseResource


class ReportsResource(BaseResource):
    async def generate_barcodes_report(self, body: dict) -> dict:
        return await self._client.request(
            method="POST",
            path="/v1/reports/documents/barcodes/generate",
            json=body,
        )
