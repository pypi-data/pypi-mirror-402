from directory_api_client.base import AbstractAPIClient

url_markets = 'dataservices/markets/'
url_country_data_by_country = 'dataservices/country-data/'
url_cia_world_factbook_data = 'dataservices/cia-factbook-data/'
url_society_data_by_country = 'dataservices/society-data-by-country/'
url_last_year_import_data_by_country = 'dataservices/lastyearimportdatabycountry/'
url_suggested_countries = '/dataservices/suggested-countries/'
url_trading_blocs_by_country = '/dataservices/trading-blocs/'
url_trade_barriers = '/dataservices/trade-barriers/'
url_market_trends = '/dataservices/uk-market-trends/'
url_trade_highlights = '/dataservices/uk-trade-highlights/'
url_commodity_exports_data_by_country = '/dataservices/commodity-exports-data-by-country/'
url_top_five_services = '/dataservices/top-five-services/'
url_top_five_goods = '/dataservices/top-five-goods/'
url_economic_highlights = '/dataservices/economic-highlights/'
url_uk_free_trade_agreements = '/dataservices/uk-free-trade-agreements/'
url_business_cluster_information_by_sic = 'dataservices/business-cluster-information-by-sic/'
url_business_cluster_information_by_dbt_sector = 'dataservices/business-cluster-information-by-dbt-sector/'
url_eyb_salary_data = 'dataservices/eyb-salary-data/'
url_eyb_commercial_rent_data = 'dataservices/eyb-commercial-rent-data/'
url_dbt_sector = 'dataservices/dbt-sector/'
url_sector_gva_value_band = 'dataservices/sector-gva-value-band/'
url_all_sectors_gva_value_bands = 'dataservices/all-sectors-gva-value-bands/'
url_dbt_investment_opportunity = 'dataservices/dbt-investment-opportunity/'
url_countries_territories_regions = 'dataservices/countries-territories-regions/'
url_country_territory_region = 'dataservices/country-territory-region/'
url_news_content = 'dataservices/news-content/'
url_local_support_by_postcode = 'dataservices/growth-hubs-commerce-chambers/'


class DataServicesAPIClient(AbstractAPIClient):
    def get_markets_data(self):
        return self.get(url=url_markets)

    def get_country_data_by_country(self, countries, fields):
        return self.get(url=url_country_data_by_country, params={'countries': countries, 'fields': fields})

    def get_cia_world_factbook_data(self, country, data_key):
        return self.get(
            url=url_cia_world_factbook_data, params={'country': country, 'data_key': data_key}, use_fallback_cache=True
        )

    def get_society_data_by_country(self, countries: list):
        return self.get(url=url_society_data_by_country, params={'countries': countries}, use_fallback_cache=True)

    def get_last_year_import_data_by_country(self, commodity_code, countries: list):
        return self.get(
            url=url_last_year_import_data_by_country, params={'commodity_code': commodity_code, 'countries': countries}
        )

    def suggested_countries_by_hs_code(self, hs_code):
        return self.get(
            url=url_suggested_countries,
            params={
                'hs_code': hs_code,
            },
        )

    def trading_blocs_by_country(self, iso2):
        return self.get(
            url=url_trading_blocs_by_country,
            params={
                'iso2': iso2,
            },
        )

    def get_trade_barriers(self, sectors: list, countries: list):
        return self.get(url=url_trade_barriers, params={'sectors': sectors, 'countries': countries})

    def get_market_trends_by_country(self, iso2, from_year=None):
        params = {'iso2': iso2}
        if from_year:
            params['from_year'] = from_year

        return self.get(
            url=url_market_trends,
            params=params,
        )

    def get_trade_highlights_by_country(self, iso2):
        params = {'iso2': iso2}

        return self.get(
            url=url_trade_highlights,
            params=params,
        )

    def get_commodity_exports_data_by_country(self, iso2):
        return self.get(
            url=url_commodity_exports_data_by_country,
            params={'iso2': iso2},
        )

    def get_top_five_services_by_country(self, iso2):
        return self.get(url=url_top_five_services, params={'iso2': iso2})

    def get_top_five_goods_by_country(self, iso2):
        return self.get(url=url_top_five_goods, params={'iso2': iso2})

    def get_economic_highlights_by_country(self, iso2):
        return self.get(url=url_economic_highlights, params={'iso2': iso2})

    def list_uk_free_trade_agreements(self):
        return self.get(url=url_uk_free_trade_agreements)

    def get_business_cluster_information_by_sic(self, sic_code, geo_code=None):
        params = {'sic_code': sic_code}
        if geo_code:
            params['geo_code'] = geo_code

        return self.get(
            url=url_business_cluster_information_by_sic,
            params=params,
        )

    def get_business_cluster_information_by_dbt_sector(self, dbt_sector_name, geo_code=None):
        params = {'dbt_sector_name': dbt_sector_name}
        if geo_code:
            params['geo_code'] = geo_code

        return self.get(
            url=url_business_cluster_information_by_dbt_sector,
            params=params,
        )

    def get_eyb_salary_data(self, vertical, professional_level=None, geo_description=None):
        params = {'vertical': vertical}

        if professional_level:
            params['professional_level'] = professional_level

        if geo_description:
            params['geo_description'] = geo_description

        return self.get(url=url_eyb_salary_data, params=params)

    def get_eyb_commercial_rent_data(self, geo_description, vertical=None, sub_vertical=None):
        params = {'geo_description': geo_description}

        if vertical:
            params['vertical'] = vertical

        if sub_vertical:
            params['sub_vertical'] = sub_vertical

        return self.get(url=url_eyb_commercial_rent_data, params=params)

    def get_dbt_sectors(self):
        return self.get(url=url_dbt_sector)

    def get_gva_bandings(self, full_sector_name):
        params = {'full_sector_name': full_sector_name}

        return self.get(url=url_sector_gva_value_band, params=params)

    def get_all_sectors_gva_value_bands(self):
        return self.get(url=url_all_sectors_gva_value_bands)

    def get_all_countries_territories_regions(self):
        return self.get(url=url_countries_territories_regions)

    def get_country_territory_region(self, iso2_code: str) -> str:
        return self.get(url=f'{url_country_territory_region}{iso2_code.upper()}')

    def get_news_content(self):
        return self.get(url=url_news_content)

    def get_local_support_by_postcode(self, postcode):
        params = {'postcode': postcode}
        return self.get(url=url_local_support_by_postcode, params=params)
