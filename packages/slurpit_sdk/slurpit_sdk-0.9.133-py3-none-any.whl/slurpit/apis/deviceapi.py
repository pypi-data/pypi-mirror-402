from slurpit.apis.baseapi import BaseAPI
from slurpit.models.device import Device, Vendor, DeviceProfile
from slurpit.utils.utils import handle_response_data, deprecated, json_to_toon_bytes
import httpx

class DeviceAPI(BaseAPI):
    def __init__(self, base_url, api_key, verify):
        """
        Initializes a new instance of DeviceAPI, extending the BaseAPI class.
        Sets up the base URL for API calls specific to devices and initializes authentication.

        Args:
            base_url (str): The root URL for the device-related API endpoints.
            api_key (str): The API key used for authenticating requests.
            verfify (bool): Verify HTTPS Certificates.
        """
        formatted_url = "{}/api".format(base_url if base_url[-1] != "/" else base_url[:-1])  # Format the base URL to ensure it ends with '/api'
        self.base_url = formatted_url  # Set the formatted base URL
        super().__init__(api_key, verify)

    async def get_devices(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Fetches a list of devices from the API with pagination and optionally exports the data to a CSV format or pandas DataFrame.
        
        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the device data in CSV format as bytes. (Deprecated)
                            If False, returns a list of Device objects.
            export_df (bool): If True, returns the device data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[Device] | bytes | pd.DataFrame: A list of Device instances, CSV/TOON data as bytes, 
                                                or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/devices"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, Device, export_csv, export_df, format=format)

    async def get_device(self, device_id: int, format: str = "json"):
        """
        Fetches a single device by its ID.

        Args:
            device_id (int): The unique identifier of the device to retrieve.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Device | bytes: A Device instance or TOON bytes if successful.
        """
        url = f"{self.base_url}/devices/{device_id}"
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            device_data = response.json()
            return Device(**device_data)

    async def update_device(self, device_id: int, update_data: dict, format: str = "json"):
        """
        Updates a specific device using its ID.

        Args:
            device_id (int): The unique identifier of the device to update.
            update_data (dict): A dictionary containing the updated device attributes. \n
                            The dictionary should include the following keys: \n
                            - "hostname" (str): The hostname of the device.
                            - "fqdn" (str): The fully qualified domain name of the device.
                            - "port" (int): The port number for device communication, typically 22.
                            - "address" (str, optional): The IP address of the device.
                            - "device_os" (str): The operating system running on the device.
                            - "os_version" (str, optional): The version of the operating system running on the device.
                            - "serial" (str, optional): The serial number of the device.
                            - "device_type" (str, optional): The type of the device.
                            - "telnet" (int, optional): Whether the device is telnet enabled (0 = not enabled, 1 = enabled).
                            - "disabled" (int): Status flag where 0 indicates enabled and 1 indicates disabled.
                            - "vault_group_id" (int, optional): Vault group identifier.
                            - "site" (str, optional): The site where the device is located.
                            - "description" (str, optional): A description of the device.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Device | bytes: An updated Device instance or TOON bytes if successful.
        """
        url = f"{self.base_url}/devices/{device_id}"
        response = await self.put(url, update_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            device_data = response.json()
            return Device(**device_data)

    async def create_device(self, device_data: dict, format: str = "json"):
        """
        Creates a new device in the system.

        Args:
            device_data (dict): A dictionary containing the device attributes. \n
                            The dictionary should include the following keys: \n
                            - "hostname" (str): The hostname of the device.
                            - "fqdn" (str): The fully qualified domain name of the device.
                            - "port" (int): The port number for device communication, typically 22.
                            - "address" (str, optional): The IP address of the device.
                            - "device_os" (str): The operating system running on the device.
                            - "os_version" (str, optional): The version of the operating system running on the device.
                            - "serial" (str, optional): The serial number of the device.
                            - "device_type" (str, optional): The type of the device.
                            - "telnet" (int, optional): Whether the device is telnet enabled (0 = not enabled, 1 = enabled).
                            - "disabled" (int): Status flag where 0 indicates enabled and 1 indicates disabled.
                            - "vault_group_id" (int, optional): Vault group identifier.
                            - "site" (str, optional): The site where the device is located.
                            - "description" (str, optional): A description of the device.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Device | bytes: A newly created Device instance or TOON bytes if successful.
        """
        url = f"{self.base_url}/devices"
        response = await self.post(url, device_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            device_data = response.json()
            return Device(**device_data)

    async def delete_device(self, device_id: int, format: str = "json"):
        """
        Deletes a device using its ID.

        Args:
            device_id (int): The unique identifier of the device to delete.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Device | bytes: A Device instance representing the deleted device or TOON bytes if successful.
        """
        url = f"{self.base_url}/devices/{device_id}"
        response = await self.delete(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            device_data = response.json()
            return Device(**device_data)

    async def sync_device(self, sync_data: dict, format: str = "json"):
        """
        Synchronizes a device with the given device data. Inserts or updates a device with the provided data.

        Args:
            sync_data (dict): A dictionary containing the device attributes to be synchronized. \n
                            The dictionary should include the following keys: \n
                            - "hostname" (str): The hostname of the device.
                            - "fqdn" (str): The fully qualified domain name of the device.
                            - "port" (int): The port number for device communication, typically 22.
                            - "address" (str, optional): The IP address of the device.
                            - "device_os" (str): The operating system running on the device.
                            - "os_version" (str, optional): The version of the operating system running on the device.
                            - "serial" (str, optional): The serial number of the device.
                            - "device_type" (str, optional): The type of the device.
                            - "telnet" (int, optional): Whether the device is telnet enabled (0 = not enabled, 1 = enabled).
                            - "disabled" (int): Status flag where 0 indicates enabled and 1 indicates disabled.
                            - "vault_group_id" (int, optional): Vault group identifier.
                            - "site" (str, optional): The site where the device is located.
                            - "description" (str, optional): A description of the device.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            None | Device | bytes: None if success (JSON), Device instance (JSON), or TOON bytes.
        """
        url = f"{self.base_url}/devices/sync"
        response = await self.post(url, sync_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            sync_result = response.json()
            if 'success' in sync_result:
                return None

            return Device(**sync_result)
        
    async def resync(self, format: str = "json"):
        """
        Resyncs all devices from warehouse to portal

        Args:
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: The status of the resync operation or TOON bytes.

        """
        url = f"{self.base_url}/devices/resync"
        response = await self.post(url,{})
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            sync_result = response.json()

            return sync_result

    async def get_vendors(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieves a list of vendors from the API and optionally exports the data to a CSV format or pandas DataFrame.
        
        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the vendor data in CSV format as bytes. (Deprecated)
                            If False, returns a list of Vendor objects.
            export_df (bool): If True, returns the vendor data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[Vendor] | bytes | pd.DataFrame: A list of Vendor instances, CSV/TOON data as bytes, 
                                                or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/devices/vendors"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, Vendor, export_csv, export_df, format=format)

    async def get_types(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieves a list of device types from the API and optionally exports the data to CSV format or pandas DataFrame.
        
        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the device type data in CSV format as bytes. (Deprecated)
                            If False, returns a list of device types as strings.
            export_df (bool): If True, returns the device type data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[str] | bytes | pd.DataFrame: A list of device types, CSV/TOON data as bytes, 
                                            or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/devices/types"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, export_csv=export_csv, export_df=export_df, format=format)


    async def get_snapshots(self, hostname: str, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieve latest data for a given hostname for all plannings, optionally filtered by date,
        and optionally exports the data to a CSV format or pandas DataFrame.
        
        Args:
            hostname (str): The hostname of the device for which snapshots are required.
            export_csv (bool): If True, returns the snapshot data in CSV format as bytes. (Deprecated)
                            If False, returns a list of snapshot data dictionaries.
            export_df (bool): If True, returns the snapshot data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[dict] | bytes | pd.DataFrame: A list of snapshot data dictionaries, CSV/TOON data as bytes,
                                            or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/devices/snapshot/all/{hostname}"
        response = await self.get(url)
        return handle_response_data(response, export_csv=export_csv, export_df=export_df, format=format)

    async def get_snapshot(self, hostname: str, planning_id: int, batch_id: int, format: str = "json"):
        """
        Retrieves latest data for a given hostname, planning id and batch id.

        Args:
            hostname (str): The hostname of the device.
            planning_id (int): The planning ID associated with the snapshot.
            batch_id (int): Batch ID, if empty it will use the latest batch id
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Snapshot data as a dictionary or TOON bytes if successful.
        """
        url = f"{self.base_url}/devices/snapshot/single/{hostname}/{planning_id}"
        if batch_id:
            url += f"/{batch_id}"
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            snapshot_data = response.json()
            return snapshot_data


    async def get_snapshot_batches(self, hostname: str, planning_id: int, format: str = "json"):
        """
        Retrieve batch id data for a given hostname.

        Args:
            hostname (str): The hostname of the device.
            planning_id (int): Planning id, if not given it returns data for all planning ids
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Batch id data for a given hostname and planning id or TOON bytes.

        """
        url = f"{self.base_url}/devices/snapshot/batches/{hostname}"
        if planning_id:
            url += f"/{planning_id}"
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            snapshot_data = response.json()
            return snapshot_data

    async def test_login(self, login_info: dict, format: str = "json"):
        """
        Tests SSH connectivity using the provided SSH information.

        Args:
            login_info (dict): A dictionary containing the SSH credentials and details. \n
                            The dictionary should include the following keys: \n
                            - "username" (str, optional): The username for SSH login.
                            - "password" (str, optional): The password for SSH login.
                            - "ssh_key" (str, optional): The ssh_key for SSH login.
                            - "ssh_passphrase" (str, optional): The ssh_passphrase for SSH Key logins.
                            - "enable_password" (str, optional): The Enable password.
                            - "host" (str): The IP address of the device to connect to.
                            - "port" (int, optional): The port number for SSH communication, typically 22.
                            - "device_os" (str, optional): The operating system running on the device.
                            - "vault_group_id" (int, optional): The vault group id to use for credentials.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: SSH test response as a dictionary or TOON bytes if successful.
        """
        url = f"{self.base_url}/devices/test/login"
        timeout = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=60.0)
        response = await self.post(url, login_info, timeout=timeout)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            ssh_response = response.json()
            return ssh_response
    
    async def test_reachability(self, host: str, port: int, format: str = "json"):
        """
        Validate if the device is reachable by the provided port.

        Args:
            - "host" (str): The IP address of the device to connect to.
            - "port" (int): The port number for SSH communication, typically 22 or 23.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Reachability test response as a dictionary or TOON bytes if successful.
        """
        url = f"{self.base_url}/devices/test/reachability/{host}/{port}"
        timeout = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=60.0)

        response = await self.get(url, timeout=timeout)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            reachability_response = response.json()
            return reachability_response
    
    async def search_devices(self, search_data: dict, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Searches for devices based on the provided search_data dictionary.

        Args:
            search_data (dict): A dictionary of search criteria. \n
                                The dictionary should include the following keys: \n
                                - "device_id" (int): The unique identifier of the device.
                                - "hostname" (str): The hostname of the device.
                                - "device_os" (str): The operating system running on the device.
                                - "sitename" (str): Name of the site to search for.
                                - "tag" (str): Name of the tag to search for.
                                - "disabled" (int): Status flag where 0 indicates enabled and 1 indicates disabled.
                                - "fqdn" (str): The fully qualified domain name of the device.
                                - "device_type" (str): The type of the device.
                                - "os_version" (str): The version of the operating system running on the device.
                                - "serial" (str): The serial number of the device.
                            

            export_csv (bool): If True, returns the search results in CSV format as bytes. (Deprecated)
                            If False, returns the search results as a dictionary.
            export_df (bool): If True, returns the search results as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[Device] | bytes | pd.DataFrame: A list of Device instances, CSV/TOON data as bytes,
                                                or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/devices/search"
        response = await self._pager(url, method="POST", payload=search_data)
        return handle_response_data(response, Device, export_csv, export_df, format=format)

    async def get_device_profiles(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Retrieves a list of device profiles from the API and optionally exports the data to CSV format or pandas DataFrame.

        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the device profile data in CSV format as bytes. (Deprecated)
                              If False, returns a list of DeviceProfile objects.
            export_df (bool): If True, returns the device profile data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[DeviceProfile] | bytes | pd.DataFrame: A list of DeviceProfile instances, CSV/TOON data as bytes,
                                                        or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/devices/profiles"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, DeviceProfile, export_csv, export_df, format=format)
    
    async def get_device_profile(self, device_id: int, format: str = "json"):
        """
        Retrieves a device profile by device ID.

        Args:
            device_id (int): The unique identifier of the device.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Device profile details containing:
                - device_id (int): The device identifier.
                - timeout (int): Connection timeout setting.
                - preferred_ssh_vault_id (int): Preferred SSH vault ID.
                - preferred_snmp_vault_id (int): Preferred SNMP vault ID.
                - blacklisted (bool): Whether the device is blacklisted.
                or TOON bytes if successful.
        """
        url = f"{self.base_url}/devices/profiles/{device_id}"
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            profile_data = response.json()
            return DeviceProfile(**profile_data)

    async def update_device_profile(self, device_id: int, profile_data: dict, format: str = "json"):
        """
        Updates an existing device profile.

        Args:
            device_id (int): The unique identifier of the device.
            profile_data (dict): A dictionary containing the profile attributes to update. \n
                                The dictionary should include the following keys: \n
                                - "timeout" (int): Connection timeout setting.
                                - "preferred_ssh_vault_id" (int): Preferred SSH vault ID.
                                - "preferred_snmp_vault_id" (int): Preferred SNMP vault ID.
                                - blacklisted (int): Indicates whether the device is blacklisted (0 or 1)
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: Updated device profile details containing:
                - device_id (int): The device identifier.
                - timeout (int): Connection timeout setting.
                - preferred_ssh_vault_id (int): Preferred SSH vault ID.
                - preferred_snmp_vault_id (int): Preferred SNMP vault ID.
                - blacklisted (int): Indicates whether the device is blacklisted (0 or 1).
                or TOON bytes if successful.
        """
        url = f"{self.base_url}/devices/profiles/{device_id}"
        response = await self.put(url, profile_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            profile_data = response.json()
            return DeviceProfile(**profile_data)

    async def search_device_profiles(self, search_data: dict, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Search for device profiles based on specified criteria.

        Args:
            search_data (dict): A dictionary containing search criteria. \n
                                The dictionary should include the following keys: \n
                                - "device_id" (int): The unique identifier of the device.
                                - "timeout" (int): Connection timeout setting.
                                - "blacklisted" (int): Blacklist status (0 or 1).
                                - "preferred_ssh_vault_id" (int): Preferred SSH vault ID.
                                - "preferred_snmp_vault_id" (int): Preferred SNMP vault ID.
            export_csv (bool): If True, returns the search results in CSV format as bytes. (Deprecated)
                            If False, returns the search results as a dictionary.
            export_df (bool): If True, returns the search results as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[DeviceProfile] | bytes | pd.DataFrame: A list of DeviceProfile instances, CSV/TOON data as bytes,
                                                       or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/devices/profiles/search"
        response = await self._pager(url, method="POST", payload=search_data)
        return handle_response_data(response, DeviceProfile, export_csv, export_df, format=format)
    
    async def add_tags(self, device_id, tag_ids: list[int], format: str = "json"):
        """
        Adds tags to a device.

        Args:
            device_id (int): The ID of the device to add tags to.
            tag_ids (list[int]): A list of tag IDs to add to the device.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            dict | bytes: The response from the API containing the updated device information or TOON bytes.
        """
        url = f"{self.base_url}/devices/{device_id}/tags"
        payload = {"tag_ids": tag_ids}
        response = await self.post(url, payload)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return response.json()

    async def remove_tags(self, device_id: int, tag_ids: list[int], format: str = "json"):
        """
        removes a tags from device using its ID.

        Args:
            device_id (int): The unique identifier of the device to remove tags.
            tag_ids (list[int]): A list of tag IDs to remove from the device.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            Device | bytes: response from the API containing the confirmation message or TOON bytes.
        """
        url = f"{self.base_url}/devices/{device_id}/tags"
        payload = {"tag_ids": tag_ids}
        response = await self.delete(url, json=payload)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            return response.json()
  

