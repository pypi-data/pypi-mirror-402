import httpx
from io import BytesIO
import os
from slurpit.config import config

class BaseAPI:
    def __init__(self, api_key, verify=True):
        """
        Initializes a new instance of the BaseAPI class with an `httpx` client.
        Args:
            api_key (str): The API key used for authorization, included in the headers of all requests.
            verfify (bool): Verify HTTPS Certificates.
        """
        self.client = httpx.AsyncClient(timeout=30, verify=verify)  # Creates an async client to persist certain parameters across requests
        self.client.headers.update({
            'Authorization': f'Bearer {api_key}',  # Bearer token for authorization
            'Content-Type': 'application/json'     # Sets default content type to JSON for all requests
        })

    async def get(self, url, **kwargs):
        """
        Sends an async GET request to the specified URL using httpx.
        Args:
            url (str): The URL to send the GET request to.
            **kwargs: Arbitrary keyword arguments that are forwarded to the `httpx.get` method.
        Returns:
            httpx.Response: The response object if the request was successful.
        Raises:
            httpx.HTTPStatusError: For responses with HTTP error statuses.
            httpx.RequestError: For network-related issues.
        """
        response = await self.client.get(url, **kwargs)  # Sends a GET request
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e.response.text)
            raise e
        return response

    async def post(self, url, data, **kwargs):
        """
        Sends an async POST request with JSON data to the specified URL using httpx.
        Args:
            url (str): The URL to send the POST request to.
            data (dict): The JSON data to send in the body of the POST request.
            **kwargs: Arbitrary keyword arguments that are forwarded to the `httpx.post` method.
        Returns:
            httpx.Response: The response object if the request was successful.
        """
        response = await self.client.post(url, json=data, **kwargs)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e.response.text)
            raise e
        return response

    async def put(self, url, data, **kwargs):
        """
        Sends an async PUT request with JSON data to the specified URL using httpx.
        Args:
            url (str): The URL to send the PUT request to.
            data (dict): The JSON data to send in the body of the PUT request.
            **kwargs: Arbitrary keyword arguments that are forwarded to the `httpx.put` method.
        Returns:
            httpx.Response: The response object if the request was successful.
        """
        response = await self.client.put(url, json=data, **kwargs)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e.response.text)
            raise e
        return response

    async def delete(self, url, **kwargs):
        """
        Sends an async DELETE request to the specified URL using httpx.
        Args:
            url (str): The URL to send the DELETE request to.
            **kwargs: Arbitrary keyword arguments that are forwarded to the `httpx.delete` method.
        Returns:
            httpx.Response: The response object if the request was successful.
        """
        if "json" in kwargs:
            response = await self.client.request("DELETE", url, **kwargs)
        else:
            response = await self.client.delete(url, **kwargs)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e.response.text)
            raise e
        return response
    
    def save_csv_bytes(self, byte_data, filename):
        """
        Saves CSV byte array data to a CSV file.

        Args:
            byte_data (bytes): CSV data in byte array format.
            filename (str): The filename to save the CSV file as.
        """
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        # Open file in binary write mode and write byte data
        with open(filename, 'wb') as file:
            file.write(byte_data)
        return True
    
    async def get_page(self, url, payload, offset_value, page_size, method="GET", paged_value="rows"):
        payload_copy = payload.copy()
        payload_copy['offset'] = offset_value
        payload_copy['limit'] = page_size
        try:
            if method == "GET":
                resp = await self.get(url, params=payload_copy)
            elif method == "POST":
                resp = await self.post(url, payload_copy)
            else:
                raise ValueError(f"Unsupported method: {method}")
            temp_data = resp.json()
            if paged_value in temp_data:
                return temp_data.get(paged_value, [])
            else:
                return temp_data
        except Exception as e:
            raise Exception(f"Error fetching page with offset {offset_value}: {str(e)}")

    async def _pager(self, url, payload=None, offset=0, limit=1000, page_size=1000, method="GET", paged_value="rows"):
        if payload is None:
            payload = {}
        payload_copy = payload.copy()
        payload_copy['offset'] = offset
        data = list()

        if not config.get_auto_pagination():
            if limit <= page_size:
                return await self.get_page(url, payload, offset, limit, method, paged_value)
            
            # Fetch initial page
        new_page = await self.get_page(url, payload, offset, page_size, method, paged_value)
        if not isinstance(new_page, list):
            return new_page
        data.extend(new_page)

        # Continue fetching until fewer results than page_size are returned
        while new_page and len(new_page) == page_size:
            offset += page_size
            limit_value = page_size

            # When no auto pagination and near the limit, only fetch the remaining needed to reach the limit
            if not config.get_auto_pagination():
                limit_value = min(limit - len(data), page_size)
                if limit_value == 0:
                    break
            new_page = await self.get_page(url, payload, offset, limit_value, method, paged_value)
            data.extend(new_page)

        return data

        
