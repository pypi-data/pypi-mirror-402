from slurpit.apis.baseapi import BaseAPI
from slurpit.models.platform import Platform, PlatformLicense
from slurpit.utils.utils import handle_response_data, json_to_toon_bytes

class PlatformAPI(BaseAPI):
    def __init__(self, base_url, api_key, verify):
        """
        Initializes a new instance of the PlatformAPI class, which extends BaseAPI. This class is designed to interact with platform-related endpoints of an API.

        Args:
            base_url (str): The root URL for the API endpoints.
            api_key (str): The API key used for authenticating requests.
            verfify (bool): Verify HTTPS Certificates.
        """
        formatted_url = "{}/api".format(base_url if base_url[-1] != "/" else base_url[:-1])  # Format the base URL to ensure it ends with '/api'
        self.base_url = formatted_url  # Set the formatted base URL
        super().__init__(api_key, verify)

    async def license(self, format: str = "json"):
        """
        Retrieves a list of the current license status

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            PlatformLicense | bytes: A PlatformLicense object or TOON bytes if the request is successful.
        """
        url = f"{self.base_url}/platform/license" 
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            platform_data = response.json()  
            return PlatformLicense(**platform_data)
        
    async def ping(self, format: str = "json"):
        """
        Sends a 'ping' request to the platform's ping endpoint to check connectivity and retrieve platform information.

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Platform | bytes: A Platform object or TOON bytes if the request is successful.
        """
        url = f"{self.base_url}/platform/ping" 
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            platform_data = response.json()  
            return Platform(**platform_data)
    
    async def version(self, format: str = "json"):
        """
        Returns the current installed Slurp'it version.

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: A dictionary initialized with the data from the Version response or TOON bytes if the request is successful.
        """
        url = f"{self.base_url}/platform/version" 
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            platform_data = response.json()  
            return platform_data  
    
    async def scraper_connectivity(self, format: str = "json"):
        """
        Test the Scraper (Data Collector) connectivity.

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Platform | bytes: A Platform object or TOON bytes if the request is successful (online/offline).
        """
        url = f"{self.base_url}/platform/scraper_connectivity" 
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            platform_data = response.json()  
            return Platform(**platform_data)
    
    async def scanner_connectivity(self, format: str = "json"):
        """
        Test the Scanner (Device Finder) connectivity.

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Platform | bytes: A Platform object or TOON bytes if the request is successful (online/offline).
        """
        url = f"{self.base_url}/platform/scanner_connectivity" 
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            platform_data = response.json()  
            return Platform(**platform_data)

    async def warehouse_connectivity(self, format: str = "json"):
        """
        Test the Warehouse connectivity.

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Platform | bytes: A Platform object or TOON bytes if the request is successful (online/offline).
        """
        url = f"{self.base_url}/platform/warehouse_connectivity" 
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            platform_data = response.json()  
            return Platform(**platform_data)
    
    async def warehouse_db_size(self, format: str = "json"):
        """
        Get the Scraper (Data Collector) DB (MongoDB) size in MB

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Platform | bytes: A Platform object or TOON bytes if the request is successful.
        """
        url = f"{self.base_url}/platform/warehouse_db_size" 
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            platform_data = response.json()  
            return Platform(**platform_data)  

    async def timezone(self, format: str = "json"):
        """
        Returns the current timezone of the Slurp'it platform.

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: A dictionary initialized with the data from the Timezone response or TOON bytes if the request is successful.
        """
        url = f"{self.base_url}/platform/timezone" 
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            platform_data = response.json()  
            return platform_data  