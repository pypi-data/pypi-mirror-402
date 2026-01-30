from slurpit.apis.baseapi import BaseAPI
from slurpit.models.site import Site, SiteRule
from slurpit.utils.utils import handle_response_data, json_to_toon_bytes

class SiteAPI(BaseAPI):
    def __init__(self, base_url, api_key, verify):
        """
        Initializes a new instance of SiteAPI, extending the BaseAPI class.
        Sets up the base URL for API calls specific to sites and initializes authentication.

        Args:
            base_url (str): The root URL for the site-related API endpoints.
            api_key (str): The API key used for authenticating requests.
            verfify (bool): Verify HTTPS Certificates.,
        """
        formatted_url = "{}/api".format(base_url if base_url[-1] != "/" else base_url[:-1])  # Format the base URL to ensure it ends with '/api'
        self.base_url = formatted_url  # Set the formatted base URL
        super().__init__(api_key, verify)

    async def get_sites(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieves a list of sites from the API.

        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the site data in CSV format as bytes. (Deprecated)
                            If False, returns a list of Site objects.
            export_df (bool): If True, returns the site data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            List[Site] | bytes | pd.DataFrame: A list of Site objects, CSV/TOON bytes, or DataFrame if the request is successful.
        """
        url = f"{self.base_url}/sites"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, Site, export_csv, export_df, format=format)

    async def get_site(self, site_id: int, format: str = "json"):
        """
        Fetches a single site by its ID.

        Args:
            site_id (int): The unique identifier of the site to retrieve.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Site | bytes: A Site instance or TOON bytes if successful.
        """
        url = f"{self.base_url}/sites/{site_id}"
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            site_data = response.json()
            return Site(**site_data)

    async def update_site(self, site_id: int, update_data: dict, format: str = "json"):
        """
        Updates a specific site using its ID.

        Args:
            site_id (int): The unique identifier of the site to update.
            update_data (dict): A dictionary containing the updated site attributes. \n
                            The dictionary should include the following keys: \n
                            - "sitename" (str): Name of the site.
                            - "description" (str): Description of the site.
                            - "street" (str): Street of the site.
                            - "street" (str): Street of the site.
                            - "county" (str): County (district) of the site.
                            - "state" (str): State of the site.
                            - "number" (str): Number of the site.
                            - "zipcode" (str): Zipcode of the site.
                            - "city" (str): City of the site.
                            - "country" (str): Country of the site.
                            - "phonenumber" (int): Phone number of the site.
                            - "status" (int): Status flag where 1 indicates enabled and 0 indicates disabled.
                            - "longitude" (str): Longitude of the site.
                            - "latitude" (str): Latitude of the site.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Site | bytes: An updated Site instance or TOON bytes if successful.
        """
        url = f"{self.base_url}/sites/{site_id}"
        response = await self.put(url, update_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            site_data = response.json()
            return Site(**site_data)
        
    async def create_site(self, site_data: dict, format: str = "json"):
        """
        Creates a new site in the system.

        Args:
            site_data (dict): A dictionary containing the site attributes. \n
                            The dictionary should include the following keys: \n
                            - "sitename" (str): Name of the site.
                            - "description" (str): Description of the site.
                            - "street" (str): Street of the site.
                            - "county" (str): County (district) of the site.
                            - "state" (str): State of the site.
                            - "number" (str): Number of the site.
                            - "zipcode" (str): Zipcode of the site.
                            - "city" (str): City of the site.
                            - "country" (str): Country of the site.
                            - "phonenumber" (int): Phone number of the site.
                            - "status" (int): Status flag where 1 indicates enabled and 0 indicates disabled.
                            - "longitude" (str): Longitude of the site.
                            - "latitude" (str): Latitude of the site.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Site | bytes: A newly created Site instance or TOON bytes if successful.
        """
        url = f"{self.base_url}/sites"
        response = await self.post(url, site_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            site_data = response.json()
            return Site(**site_data)
        
    async def delete_site(self, site_id: int, format: str = "json"):
        """
        Deletes a site using its ID.

        Args:
            site_id (int): The unique identifier of the site to delete.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Site | bytes: A Site instance representing the deleted site or TOON bytes if successful.
        """
        url = f"{self.base_url}/sites/{site_id}"
        response = await self.delete(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            site_data = response.json()
            return Site(**site_data)

    async def get_siterules(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieves a list of site rules from the API.

        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the site rule data in CSV format as bytes. (Deprecated)
                            If False, returns a list of SiteRule objects.
            export_df (bool): If True, returns the site rule data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            List[Site] | bytes | pd.DataFrame: A list of Site objects, CSV/TOON bytes, or DataFrame if the request is successful.
        """
        url = f"{self.base_url}/sites/siterules"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, SiteRule, export_csv, export_df, format=format)

    async def create_siterule(self, siterule_data: dict, format: str = "json"):
        """
        Creates a new site rule in the system.

        Args:
            siterule_data (dict): A dictionary containing the site rule attributes. \n
                            The dictionary should include the following keys: \n
                            - "rule" (str): The rule to be applied.
                            - "applied_to" (str): The element to which the rule is applied.
                            - "rule_order" (int): The order of the rule.
                            - "site_id" (int): The ID of the site to which the rule is applied.
                            - "create_site" (int): Flag where 1 will create-site and 0 will select existing site.
                            - "disabled" (int): Whether the rule is disabled.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            SiteRule | bytes: A newly created SiteRule instance or TOON bytes if successful.
        """
        url = f"{self.base_url}/sites/siterules"
        response = await self.post(url, siterule_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            siterule_data = response.json()
            return SiteRule(**siterule_data)
        
    async def delete_siterule(self, siterule_id: int, format: str = "json"):
        """
        Deletes a site rule using its ID.

        Args:
            siterule_id (int): The unique identifier of the site rule to delete.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            SiteRule | bytes: A SiteRule instance representing the deleted site rule or TOON bytes if successful.
        """
        url = f"{self.base_url}/sites/siterules/{siterule_id}"
        response = await self.delete(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            siterule_data = response.json()
            return SiteRule(**siterule_data)

    async def test_siterule(self, test_data: dict, format: str = "json"):
        """
        Tests a site rule.

        Args:
            test_data (dict): The test data.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: The test result or TOON bytes.
        """
        url = f"{self.base_url}/sites/siterules/test"
        response = await self.post(url, test_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            test_result = response.json()
            return test_result

    async def reset_devices(self, format: str = "json"):
        """
        Resets the devices for all sites.

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: The result or TOON bytes.
        """
        url = f"{self.base_url}/sites/reset_devices"
        response = await self.post(url, {})
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return response.json()
