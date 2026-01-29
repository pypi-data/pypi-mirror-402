
import os
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

        # Initialize API instances
        self.filings = FilingsApi(self.api_client)
        self.companies = CompaniesApi(self.api_client)
        self.filing_types = FilingTypesApi(self.api_client)
        self.filing_categories = FilingCategoriesApi(self.api_client)
        self.sources = SourcesApi(self.api_client)
        self.languages = LanguagesApi(self.api_client)
        self.countries = CountriesApi(self.api_client)
        self.isic = ISICClassificationsApi(self.api_client)
        self.webhooks = WebhooksManagementApi(self.api_client)

    def close(self):
        self.api_client.close()

    # Async Context Managers to match library=asyncio
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
