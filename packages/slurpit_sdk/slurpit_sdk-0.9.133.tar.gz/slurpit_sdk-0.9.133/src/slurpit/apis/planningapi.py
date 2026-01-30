from slurpit.apis.baseapi import BaseAPI
from slurpit.models.planning import Planning
from slurpit.utils.utils import handle_response_data, json_to_toon_bytes


class PlanningAPI(BaseAPI):
    def __init__(self, base_url, api_key, verify):
        """
        Initializes a new instance of the PlanningAPI class, which extends BaseAPI. This class is designed to interact with the planning-related endpoints of an API, managing planning entries.

        Args:
            base_url (str): The root URL for the API endpoints.
            api_key (str): The API key used for authenticating requests.
            verfify (bool): Verify HTTPS Certificates.
        """
        formatted_url = "{}/api".format(base_url if base_url[-1] != "/" else base_url[:-1])  # Format the base URL to ensure it ends with '/api'
        self.base_url = formatted_url  # Set the formatted base URL
        super().__init__(api_key, verify)

    async def get_plannings(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Fetches all planning entries from the API and optionally exports the data to a CSV format or pandas DataFrame.
        
        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the planning data in CSV format as bytes. (Deprecated)
                            If False, returns a list of Planning objects.
            export_df (bool): If True, returns the planning data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[Planning] | bytes | pd.DataFrame: A list of Planning objects, CSV/TOON data as bytes,
                                                or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/planning"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, Planning, export_csv, export_df, format=format)

    async def search_plannings(self, search_data: dict, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        A more flexible way to search over the unique planning data and optionally exports the data to CSV format or pandas DataFrame.

        Args:
            search_data (dict): A dictionary of search criteria. \n
                                The dictionary should include the following keys: \n
                                - "planning_id" (int): The unique identifier of the planning.
                                - "batch_id" (int): The runs batch id in which to search.
                                - "hostnames" (list of str): A list of hostnames to search for.
                                - "device_os" (list of str): A list of device operating systems to search for.
                                - "search" (str): A search term to filter the results.
                                - "unique_results" (bool): Flag to indicate if only unique results should be returned.
                                - "latest" (bool): Flag to indicate if only results from the latest batch should be returned.
                                - "start_date" (str): The start date and time for the search range (format: "YYYY-MM-DD HH:MM").
                                - "end_date" (str): The end date and time for the search range (format: "YYYY-MM-DD HH:MM").

            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the search results in CSV format as bytes. (Deprecated)
                            If False, returns the search results as a dictionary.
            export_df (bool): If True, returns the search results as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            dict | bytes | pd.DataFrame: The search results as a dictionary, CSV/TOON data as bytes,
                                        or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/planning/search"
        response = await self._pager(url, payload=search_data, offset=offset, limit=limit, method="POST")
        return handle_response_data(response, export_csv=export_csv, export_df=export_df, format=format)

    async def regenerate_unique(self, planning_id: int, format: str = "json"):
        """
        Regenerates unique data for a planning entry based on the given ID. This is necessary when key attributes are changed and unique results need to be updated.

        Args:
            planning_id (int): The ID of the planning entry that requires regeneration of unique attributes.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Updated information of the planning entry or TOON bytes.
        """
        url = f"{self.base_url}/planning/regenerate_unique"
        planning_data = {
            'planning_id': planning_id
        }
        response = await self.post(url, planning_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            update_info = response.json()
            return update_info

    async def export_planning(self, planning_ids: list, format: str = "json"):
        """
        Export one or more plannings as JSON.

        Args:
            planning_ids (list): A list of planning IDs to export.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: The exported planning data or TOON bytes.
        """
        url = f"{self.base_url}/planning/export"
        payload = {
            "planning_ids": planning_ids
        }
        response = await self.post(url, payload)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return response.json()

    async def import_planning(self, planning_data: list, mode: str = "new", format: str = "json"):
        """
        Import planning from JSON data.

        Args:
            planning_data (list): A list of planning data dictionaries to import.
            mode (str): "new" creates a new planning with a unique name if one already exists, 
                        "overwrite" updates the existing planning with the same name. Default is "new".
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: The result of the import operation or TOON bytes.
        """
        url = f"{self.base_url}/planning/import"
        payload = {
            "planning_data": planning_data,
            "mode": mode
        }
        response = await self.post(url, payload)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return response.json()

