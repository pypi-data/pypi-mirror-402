from slurpit.apis.baseapi import BaseAPI
from slurpit.models.scanner import Node, DeviceFinder, DeviceCrawler
from slurpit.utils.utils import handle_response_data, json_to_toon_bytes
import httpx

class ScannerAPI(BaseAPI):
    def __init__(self, base_url, api_key, verify):
        """
        Initialize the ScannerAPI with the base URL of the API and an API key for authentication.
        
        Args:
            base_url (str): The root URL for the API endpoints.
            api_key (str): The API key used for authenticating requests.
            verfify (bool): Verify HTTPS Certificates.
        """
        formatted_url = "{}/api".format(base_url if base_url[-1] != "/" else base_url[:-1])  # Format the base URL to ensure it ends with '/api'
        self.base_url = formatted_url  # Set the formatted base URL
        super().__init__(api_key, verify)  # Initialize the parent class with the API key

    async def get_nodes(self, batch_id: int, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieves a list of nodes based on the batch_id with pagination options and optionally exports the data to CSV format or pandas DataFrame.

        Args:
            batch_id (int): The batch identifier to filter nodes.
            offset (int): The starting index for pagination.
            limit (int): The maximum number of nodes to return.
            export_csv (bool): If True, returns the nodes data in CSV format as bytes. (Deprecated)
            export_df (bool): If True, returns the nodes data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[dict] | bytes | pd.DataFrame: A list of nodes, CSV/TOON data as bytes, 
                                            or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/scanner/{batch_id}"
        response = await self._pager(url, offset=offset, limit=limit, paged_value="nodes")
        return handle_response_data(response, export_csv=export_csv, export_df=export_df, format=format)

    async def get_finders(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieves a list of configured finders from the scanner API and optionally exports the data to CSV format or pandas DataFrame.

        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the finders data in CSV format as bytes. (Deprecated)
            export_df (bool): If True, returns the finders data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[DeviceFinder] | bytes | pd.DataFrame: A list of finders, CSV/TOON data as bytes,
                                            or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/scanner/configured/finders"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, DeviceFinder, export_csv, export_df, format=format)

    async def add_finder(self, finder_data: dict, format: str = "json"):
        """
        Add a new Device Finder configuration.

        Args:
            finder_data (dict): A dictionary containing the finder configuration. \n
                                The dictionary should include the following keys: \n
                                - "name" (str): Name of the finder.
                                - "group_id" (int): The SNMP vault group id.
                                - "target" (str): Target needs to be comma seperated (e.g. "192.168.1.1,192.168.1.2").
                                - "snmp_port" (int): Default snmp port is 161.
                                - "disabled" (int): 0 for enabled, 1 for disabled. 
                                - "type" (str): The type of device finder. Allowed values: "target", "plugin", "inventory". Type 'plugin' requires plugin prefix option to be enabled.
                                - "tags" (list, optional): List of tag IDs. Only works when you have an enterprise license.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            DeviceFinder | bytes: Response from the API or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/configured/finders"
        response = await self.post(url, finder_data)
        
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return DeviceFinder(**response.json())

    async def update_finder(self, finder_id: int, update_data: dict, format: str = "json"):
        """
        Update an existing Device Finder configuration.

        Args:
            finder_id (int): Finder ID.
            update_data (dict): A dictionary containing the updated finder configuration. \n
                                The dictionary should include the following keys: \n
                                - "name" (str): Name of the finder.
                                - "group_id" (int): The SNMP vault group id.
                                - "target" (str): Target needs to be comma seperated (e.g. "192.168.1.1,192.168.1.2").
                                - "snmp_port" (int): Default snmp port is 161.
                                - "disabled" (int): 0 for enabled, 1 for disabled. 
                                - "type" (str): The type of device finder. Allowed values: "target", "plugin", "inventory". Type 'plugin' requires plugin prefix option to be enabled.
                                - "tags" (list, optional): List of tag IDs. Only works when you have an enterprise license.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            DeviceFinder | bytes: Response from the API or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/configured/finders/{finder_id}"
        response = await self.put(url, update_data)
        
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return DeviceFinder(**response.json())
    
    async def delete_finder(self, finder_id: int, format: str = "json"):
        """
        Delete a Device Finder configuration.

        Args:
            finder_id (int): Finder ID.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            DeviceFinder | bytes: Response from the API or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/configured/finders/{finder_id}"
        response = await self.delete(url)
        
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return DeviceFinder(**response.json())

    async def get_crawlers(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieves a list of configured crawlers from the scanner API and optionally exports the data to CSV format or pandas DataFrame.

        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the crawlers data in CSV format as bytes. (Deprecated)
            export_df (bool): If True, returns the crawlers data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[DeviceCrawler] | bytes | pd.DataFrame: A list of crawlers, CSV/TOON data as bytes,
                                            or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/scanner/configured/crawlers"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, DeviceCrawler, export_csv, export_df, format=format)

    async def add_crawler(self, crawler_data: dict, format: str = "json"):
        """
        Add a new Device Crawler configuration.

        Args:
            crawler_data (dict): A dictionary containing the crawler configuration. \n
                                 The dictionary should include the following keys: \n
                                 - "planning_id" (int): Link to a planning item.
                                 - "group_id" (int): The SNMP vault group id.
                                 - "snmp_port" (int): Default snmp port is 161.
                                 - "disabled" (int): 0 for enabled, 1 for disabled. 
                                 - "include_public_ips" (int): 0 for disabled, 1 for enabled.
                                 - "tags" (list, optional): List of tag IDs. Only works when you have an enterprise license.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            DeviceCrawler | bytes: Response from the API or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/configured/crawlers"
        response = await self.post(url, crawler_data)
        
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return DeviceCrawler(**response.json())

    async def update_crawler(self, crawler_id: int, update_data: dict, format: str = "json"):
        """
        Update an existing Device Crawler configuration.

        Args:
            crawler_id (int): Crawler ID.
            update_data (dict): A dictionary containing the updated crawler configuration. \n
                                The dictionary should include the following keys: \n
                                - "planning_id" (int): Link to a planning item.
                                - "group_id" (int): The SNMP vault group id.
                                - "snmp_port" (int): Default snmp port is 161.
                                - "disabled" (int): 0 for enabled, 1 for disabled. 
                                - "include_public_ips" (int): 0 for disabled, 1 for enabled.
                                - "tags" (list, optional): List of tag IDs. Only works when you have an enterprise license.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            DeviceCrawler | bytes: Response from the API or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/configured/crawlers/{crawler_id}"
        response = await self.put(url, update_data)
        
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return DeviceCrawler(**response.json())
    
    async def delete_crawler(self, crawler_id: int, format: str = "json"):
        """
        Delete a Device Crawler configuration.

        Args:
            crawler_id (int): Crawler ID.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            DeviceCrawler | bytes: Response from the API or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/configured/crawlers/{crawler_id}"
        response = await self.delete(url)
        
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return DeviceCrawler(**response.json())

    async def get_excludes(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieve list of excluded subnets with notes.

        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the excludes data in CSV format as bytes. (Deprecated)
            export_df (bool): If True, returns the excludes data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[dict] | bytes | pd.DataFrame: A list of excluded subnets, CSV/TOON data as bytes,
                                            or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/scanner/configured/exclude"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, export_csv=export_csv, export_df=export_df, format=format)

    async def add_exclude(self, exclude_data: dict, format: str = "json"):
        """
        Add a new excluded subnet.

        Args:
            exclude_data (dict): A dictionary containing the exclude configuration. \n
                                 The dictionary should include the following keys: \n
                                 - "target" (str): Target subnet to exclude.
                                 - "note" (str): Note for the excluded subnet.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Response from the API or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/configured/exclude"
        response = await self.post(url, exclude_data)
        
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return response.json()

    async def update_exclude(self, exclude_id: int, update_data: dict, format: str = "json"):
        """
        Update an existing excluded subnet.

        Args:
            exclude_id (int): Exclude ID.
            update_data (dict): A dictionary containing the updated exclude configuration. \n
                                The dictionary should include the following keys: \n
                                - "target" (str): Target subnet to exclude.
                                - "note" (str): Note for the excluded subnet.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Response from the API or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/configured/exclude/{exclude_id}"
        response = await self.put(url, update_data)
        
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return response.json()

    async def delete_exclude(self, exclude_id: int, format: str = "json"):
        """
        Delete an excluded subnet.

        Args:
            exclude_id (int): Exclude ID.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Response from the API or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/configured/exclude/{exclude_id}"
        response = await self.delete(url)
        
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return response.json()

    async def start_scanner(self, scanner_data: dict, format: str = "json"):
        """
        Starts a scanning process with provided scanner configuration data.

        Args:
            scanner_data (dict): A dictionary containing the scanner configuration data. \n
                                The dictionary should include the following keys: \n
                                - "target" (str): The target to be scanned.
                                - "snmp_port" (int): The SNMP port number.
                                - "version" (str): The SNMP version, e.g., "snmpv2c".
                                - "batch_id" (int): The batch ID for the scanning process.
                                - "snmpv2c_key" (str): The SNMPv2c community string.
                                - "snmpv3_username" (str): The SNMPv3 username.
                                - "snmpv3_authkey" (str): The SNMPv3 authentication key.
                                - "snmpv3_authtype" (list of str): The SNMPv3 authentication types, possible values are ["none", "md5", "sha", "sha224", "sha256", "sha384", "sha512"].
                                - "snmpv3_privkey" (str): The SNMPv3 privacy key.
                                - "snmpv3_privtype" (list of str): The SNMPv3 privacy types, possible values are ["none", "des", "3des", "aes128", "aes192", "aes256", "aesblumenthal192", "aesblumenthal256"].
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Status of the scanning process or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner"
        response = await self.post(url, scanner_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            scanner_status = response.json()
            return scanner_status

    async def clean_logging(self, datetime: str, format: str = "json"):
        """
        Triggers a cleaning process for scanner logs older than the specified datetime.

        Args:
            datetime (str): The datetime string to clean logs older than.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Result of the cleaning process or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/clean"
        request_data = {"datetime": datetime}
        response = await self.post(url, request_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            clean_result = response.json()
            return clean_result

    async def get_status(self, format: str = "json"):
        """
        Retrieves the current status of the scanner.

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: The current status of the scanner or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/status"
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            status_result = response.json()
            return status_result

    async def test_snmp(self, ip_data: dict, format: str = "json"):
        """
        Tests SNMP configuration by attempting to gather device information from the specified IP.

        Args:
            ip_data (dict): A dictionary containing the SNMP configuration details. \n
                            The dictionary should include the following keys: \n
                            - "ip" (str): The IP address of the device to connect to.
                            - "version" (str): The SNMP version, e.g., "snmpv2c".
                            - "snmp_port" (int): The SNMP port number.
                            - "snmpv2c_key" (str): The SNMPv2c community string.
                            - "snmpv3_username" (str): The SNMPv3 username.
                            - "snmpv3_authkey" (str): The SNMPv3 authentication key.
                            - "snmpv3_authtype" (list of str): The SNMPv3 authentication types, possible values are ["none", "md5", "sha", "sha224", "sha256", "sha384", "sha512"].
                            - "snmpv3_privkey" (str): The SNMPv3 privacy key.
                            - "snmpv3_privtype" (list of str): The SNMPv3 privacy types, possible values are ["none", "des", "3des", "aes128", "aes192", "aes256", "aesblumenthal192", "aesblumenthal256"].
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Device information gathered via SNMP or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/test"
        timeout = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=60.0)
        response = await self.post(url, ip_data, timeout=timeout)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            device_info = response.json()
            return device_info

    async def get_queue_list(self, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Gives a list of currently queued tasks for the scanner.

        Args:
            export_csv (bool): If True, returns the queued tasks data in CSV format as bytes. If False, returns list of queued tasks. (Deprecated)
            export_df (bool): If True, returns the crawlers data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[dict] | bytes | pd.DataFrame: A list of queued tasks, CSV/TOON data as bytes,
                                            or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/scanner/queue/list"
        response = await self.post(url, None)
        return handle_response_data(response, export_csv=export_csv, export_df=export_df, format=format)
    
    async def clear_queue(self, format: str = "json"):
        """
        Clears the queue of the scanner by sending a DELETE request to the queue list endpoint.

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: The result of clearing the queue or TOON bytes if successful.
        """
        url = f"{self.base_url}/scanner/queue/clear"
        response = await self.delete(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            clear_result = response.json()
            return clear_result