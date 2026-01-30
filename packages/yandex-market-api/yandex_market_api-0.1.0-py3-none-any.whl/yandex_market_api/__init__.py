from yandex_market_api.config import Config
from yandex_market_api.client import ApiClient
from yandex_market_api.resources.campaigns import CampaignsResource
from yandex_market_api.resources.businesses import BusinessesResource
from yandex_market_api.resources.categories import CategoriesResource
from yandex_market_api.resources.offers import OffersResource
from yandex_market_api.resources.reports import ReportsResource
from yandex_market_api.resources.tariffs import TariffsResource
from yandex_market_api.resources.prices import PricesResource
from yandex_market_api.resources.recommendations import RecommendationsResource


class YandexMarketClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.partner.market.yandex.ru",
    ):
        config: Config = Config(api_key=api_key, base_url=base_url)

        self._client: ApiClient = ApiClient(config)

        self.campaigns: CampaignsResource = CampaignsResource(self._client)
        self.businesses: BusinessesResource = BusinessesResource(self._client)
        self.categories: CategoriesResource = CategoriesResource(self._client)
        self.offers: OffersResource = OffersResource(self._client)
        self.reports: ReportsResource = ReportsResource(self._client)
        self.tariffs: TariffsResource = TariffsResource(self._client)
        self.prices: PricesResource = PricesResource(self._client)
        self.recommendations: RecommendationsResource = RecommendationsResource(self._client)

    async def close(self) -> None:
        await self._client.close()


__all__ = ["YandexMarketClient"]
