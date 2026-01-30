from slurpit.apis.userapi import UserAPI  # Import UserAPI for user-related API interactions
from slurpit.apis.vaultapi import VaultAPI  # Import VaultAPI for vault-related API interactions
from slurpit.apis.platformapi import PlatformAPI  # Import PlatformAPI for platform-related API interactions
from slurpit.apis.deviceapi import DeviceAPI
from slurpit.apis.planningapi import PlanningAPI
from slurpit.apis.scannerapi import ScannerAPI
from slurpit.apis.scraperapi import ScraperAPI
from slurpit.apis.templateapi import TemplateAPI
from slurpit.apis.siteapi import SiteAPI
from slurpit.apis.tagapi import TagAPI  # Import TagAPI for tag-related API interactions
from slurpit.config import config

class Api:
    def __init__(self, url, api_key=None, verify=True, auto_pagination=True):
        """
        Initializes a new instance of the Api class, which aggregates access to various API services.

        Args:
            url (str): The base URL for the API server.
            api_key (str, optional): The API key used for authentication with the API server. Defaults to None.
            verify (bool): Verify HTTPS Certificates.
            auto_pagination (bool): Whether to enable automatic pagination across all API calls. Defaults to True.

        Attributes:
            base_url (str): The full base URL for the API including the '/api' endpoint suffix.
            api_key (str): The API key used for authenticating requests.
            verfify (bool): Verify HTTPS Certificates.
            users (UserAPI): An instance of UserAPI initialized with the base URL and API key.
            vault (VaultAPI): An instance of VaultAPI initialized with the base URL and API key.
            platform (PlatformAPI): An instance of PlatformAPI initialized with the base URL and API key.
        """
        self.base_url = url
        self.api_key = api_key  # Store the API key
        self.verify = verify
        
        # Set global auto-pagination setting
        config.set_auto_pagination(auto_pagination)
        
        self.user = UserAPI(url, api_key, verify)  # Initialize the UserAPI with the base URL and API key
        self.vault = VaultAPI(url, api_key, verify)  # Initialize the VaultAPI with the base URL and API key
        self.platform = PlatformAPI(url, api_key, verify)  # Initialize the PlatformAPI with the base URL and API key
        self.device = DeviceAPI(url, api_key, verify)
        self.planning = PlanningAPI(url, api_key, verify)
        self.site = SiteAPI(url, api_key, verify)
        self.scanner = ScannerAPI(url, api_key, verify)
        self.scraper = ScraperAPI(url, api_key, verify)
        self.templates = TemplateAPI(url, api_key, verify)
        self.tag = TagAPI(url, api_key, verify)  # Initialize the TagAPI with the base URL and API key

    def set_auto_pagination(self, enabled: bool):
        """
        Set the global auto-pagination setting for all API calls.
        
        Args:
            enabled (bool): Whether to enable automatic pagination across all API calls.
        """
        config.set_auto_pagination(enabled)
    
    def get_auto_pagination(self) -> bool:
        """
        Get the current global auto-pagination setting.
        
        Returns:
            bool: The current auto-pagination setting.
        """
        return config.get_auto_pagination()
