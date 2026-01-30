from slurpit.apis.baseapi import BaseAPI
from slurpit.models.tag import Tag, TagRule
from slurpit.utils.utils import handle_response_data, json_to_toon_bytes

class TagAPI(BaseAPI):
    def __init__(self, base_url, api_key, verify):
        """
        Initializes a new instance of TagAPI, extending the BaseAPI class.
        Sets up the base URL for API calls specific to tags and initializes authentication.

        Args:
            base_url (str): The root URL for the tag-related API endpoints.
            api_key (str): The API key used for authenticating requests.
            verfify (bool): Verify HTTPS Certificates.
        """
        formatted_url = "{}/api".format(base_url if base_url[-1] != "/" else base_url[:-1])
        self.base_url = formatted_url
        super().__init__(api_key, verify)

    # TAGS
    async def get_tags(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieves a list of tags from the API.

        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the tag data in CSV format as bytes. (Deprecated)
                               If False, returns a list of Tag objects.
            export_df (bool): If True, returns the tag data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[Tag] | bytes | pd.DataFrame: A list of Tag objects, CSV/TOON bytes, or DataFrame depending on flags.
        """
        url = f"{self.base_url}/tags"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, Tag, export_csv, export_df, format=format)

    async def create_tag(self, tag_data: dict, format: str = "json"):
        """
        Creates a new tag in the system.

        Args:
            tag_data (dict): A dictionary containing tag attributes.
                             Expected keys:
                             - "name" (str): Name of the tag.
                             - "type" (str): Type of the tag (e.g., "device").
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Tag | bytes: A newly created Tag instance or TOON bytes if successful.
        """
        url = f"{self.base_url}/tags"
        response = await self.post(url, tag_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            tag_data = response.json()
            return Tag(**tag_data)

    async def get_tag(self, tag_id: int, format: str = "json"):
        """
        Fetches a single tag by its ID.

        Args:
            tag_id (int): The unique identifier of the tag to retrieve.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Tag | bytes: A Tag instance or TOON bytes if successful.
        """
        url = f"{self.base_url}/tags/{tag_id}"
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            tag_data = response.json()
            return Tag(**tag_data)

    async def update_tag(self, tag_id: int, tag_data: dict, format: str = "json"):
        """
        Updates a specific tag using its ID.

        Args:
            tag_id (int): The unique identifier of the tag to update.
            tag_data (dict): A dictionary containing the updated tag attributes.
                             Expected keys:
                             - "name" (str): Name of the tag.
                             - "type" (str): Type of the tag (e.g., "device").
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Tag | bytes: An updated Tag instance or TOON bytes if successful.
        """
        url = f"{self.base_url}/tags/{tag_id}"
        response = await self.put(url, tag_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            tag_data = response.json()
            return Tag(**tag_data)

    async def delete_tag(self, tag_id: int, format: str = "json"):
        """
        Deletes a tag using its ID.

        Args:
            tag_id (int): The unique identifier of the tag to delete.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Tag | bytes: A Tag instance representing the deleted tag or TOON bytes if successful.
        """
        url = f"{self.base_url}/tags/{tag_id}"
        response = await self.delete(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            tag_data = response.json()
            return Tag(**tag_data)

    async def reset_devices(self, format: str = "json"):
        """
        Resets the devices associated with tags.

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: the result of the reset operation or TOON bytes.
        """
        url = f"{self.base_url}/tags/reset_devices"
        response = await self.post(url, {})
        if format == "toon":
            return json_to_toon_bytes(response.json())
        return response.json()

    # TAG RULES
    async def get_tagrules(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieves a list of tag rules from the API.

        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the tag rule data in CSV format as bytes. (Deprecated)
                               If False, returns a list of TagRule objects.
            export_df (bool): If True, returns the tag rule data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[TagRule] | bytes | pd.DataFrame: A list of TagRule objects, CSV/TOON bytes, or DataFrame depending on flags.
        """
        url = f"{self.base_url}/tags/tagrules"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, TagRule, export_csv, export_df, format=format)

    async def create_tagrule(self, tagrule_data: dict, format: str = "json"):
        """
        Creates a new tag rule in the system.

        Args:
            tagrule_data (dict): A dictionary containing the tag rule attributes.
                                 Expected keys:
                                 - "rule" (str): The rule to be applied.
                                 - "applied_to" (str): The element to which the rule is applied (e.g., "hostname").
                                 - "rule_order" (int): The order of the rule.
                                 - "tag_id" (int): The ID of the tag to which the rule is applied.
                                 - "disabled" (int): Whether the rule is disabled.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            TagRule | bytes: A newly created TagRule instance or TOON bytes if successful.
        """
        url = f"{self.base_url}/tags/tagrules"
        response = await self.post(url, tagrule_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            tagrule_data = response.json()
            return TagRule(**tagrule_data)

    async def delete_tagrule(self, tagrule_id: int, format: str = "json"):
        """
        Deletes a tag rule using its ID.

        Args:
            tagrule_id (int): The unique identifier of the tag rule to delete.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            TagRule | bytes: A TagRule instance representing the deleted tag rule or TOON bytes if successful.
        """
        url = f"{self.base_url}/tags/tagrules/{tagrule_id}"
        response = await self.delete(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            tagrule_data = response.json()
            return TagRule(**tagrule_data)

    async def test_tagrule(self, data: dict, format: str = "json"):
        """
        Tests a tag rule to verify which tag a device would be added to by providing device info.

        Args:
            data (dict): Test payload containing:
                         - "test_string" (str): The value to test against the rules (e.g., "hostname").
                         - "applyTo" (str): The attribute to which the rule applies (e.g., hostname,fqdn, device_os, device_type, ipv4).
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: test results with tag if found or TOON bytes.
        """
        url = f"{self.base_url}/tags/tagrules/test"
        response = await self.post(url, data)
        if format == "toon":
            return json_to_toon_bytes(response.json())
        return response.json()
