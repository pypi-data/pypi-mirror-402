
import os
import asyncio
from .configuration import Configuration
from .api_client import ApiClient

# Import all API classes
from .api.filings_api import FilingsApi
from .api.companies_api import CompaniesApi
from .api.filing_types_api import FilingTypesApi
from .api.filing_categories_api import FilingCategoriesApi
from .api.sources_api import SourcesApi
from .api.languages_api import LanguagesApi
from .api.countries_api import CountriesApi
from .api.isic_classifications_api import ISICClassificationsApi
from .api.webhooks_management_api import WebhooksManagementApi

class ResourceWrapper:
    """
    Wraps the generated API classes to provide cleaner method names.
    Translates client.filings.list() -> client.filings.filings_list()
    """
    def __init__(self, api_instance, prefix):
        self._api = api_instance
        self._prefix = prefix

    def __getattr__(self, name):
        # 1. Try to find the method with the prefix (e.g., 'list' -> 'filings_list')
        prefixed_name = f"{self._prefix}_{name}"
        if hasattr(self._api, prefixed_name):
            return getattr(self._api, prefixed_name)
        
        # 2. Fallback: Return the original attribute if it exists
        return getattr(self._api, name)

class FinancialReports:
    """
    The main entry point for the Financial Reports SDK.
    
    Usage:
        async with FinancialReports(api_key="your_key") as client:
            filings = await client.filings.list()
    """
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.environ.get('FINANCIAL_REPORTS_API_KEY')
        
        if not api_key:
            raise ValueError("API Key is required. Pass it to the constructor or set FINANCIAL_REPORTS_API_KEY env var.")

        # Hardcode the Production Host
        self.config = Configuration(host="https://api.financialreports.eu")
        self.config.api_key['ApiKeyAuth'] = api_key
        
        self.api_client = ApiClient(self.config)

        # Initialize API instances with smart wrappers
        self.filings = ResourceWrapper(FilingsApi(self.api_client), "filings")
        self.companies = ResourceWrapper(CompaniesApi(self.api_client), "companies")
        self.filing_types = ResourceWrapper(FilingTypesApi(self.api_client), "filing_types")
        self.filing_categories = ResourceWrapper(FilingCategoriesApi(self.api_client), "filing_categories")
        self.sources = ResourceWrapper(SourcesApi(self.api_client), "sources")
        self.languages = ResourceWrapper(LanguagesApi(self.api_client), "languages")
        self.countries = ResourceWrapper(CountriesApi(self.api_client), "countries")
        
        # ISIC has multiple endpoints per API class, so we leave it unwrapped or user calls specific methods
        self.isic = ISICClassificationsApi(self.api_client)
        
        # Webhooks
        self.webhooks = ResourceWrapper(WebhooksManagementApi(self.api_client), "webhooks")

    async def close(self):
        await self.api_client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
