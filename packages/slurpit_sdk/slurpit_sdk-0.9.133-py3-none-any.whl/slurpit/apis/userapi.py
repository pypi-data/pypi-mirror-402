from slurpit.apis.baseapi import BaseAPI
from slurpit.models.user import User
from slurpit.utils.utils import handle_response_data, json_to_toon_bytes
class UserAPI(BaseAPI):
    def __init__(self, base_url, api_key, verify):
        """
        Initializes a new instance of the UserAPI class, setting up the base URL and inheriting from BaseAPI.

        Args:
            base_url (str): The root URL for the user service API.
            api_key (str): The API key used for authorization in the API requests.
            verfify (bool): Verify HTTPS Certificates.
        """
        formatted_url = "{}/api".format(base_url if base_url[-1] != "/" else base_url[:-1])  # Format the base URL to ensure it ends with '/api'
        self.base_url = formatted_url  # Set the formatted base URL
        super().__init__(api_key, verify)

    async def get_users(self, offset: int = 0, limit: int = 1000, export_csv: bool = False, export_df: bool = False, format: str = "json"):
        """
        Fetches a list of users from the API and returns them as a list of User objects.
        Optionally exports the data to a CSV format or pandas DataFrame if specified.

        Args:
            offset (int): The starting index of the records to fetch.
            limit (int): The maximum number of records to return in one call.
            export_csv (bool): If True, returns the user data in CSV format as bytes. (Deprecated)
            export_df (bool): If True, returns the user data as a pandas DataFrame. (Deprecated)
            format (str): The desired output format ("json", "csv", "dataframe", "toon"). Default is "json".

        Returns:
            list[User] | bytes | pd.DataFrame: Returns a list of User objects if successful, CSV/TOON bytes,
                                            or a pandas DataFrame depending on the export format.
        """
        url = f"{self.base_url}/users"
        response = await self._pager(url, offset=offset, limit=limit)
        return handle_response_data(response, User, export_csv, export_df, format=format)

    async def get_user(self, user_id: int, format: str = "json"):
        """
        Fetches a single user by user ID from the API.

        Args:
            user_id (int): The unique identifier of the user to retrieve.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            User | bytes: Returns the User object or TOON bytes if the fetch is successful.
        """
        url = f"{self.base_url}/users/{user_id}"
        response = await self.get(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            user_data = response.json()
            return User(**user_data)

    async def update_user(self, user_id: int, update_data: dict, format: str = "json"):
        """
        Updates a user's information on the server.

        Args:
            user_id (int): The unique identifier of the user to update.
            update_data (dict): A dictionary containing the data to update. \n
                                The dictionary should include the following keys: \n
                                - "first_name" (str): The first name of the user.
                                - "last_name" (str): The last name of the user.
                                - "email" (str): The email address of the user.
                                - "language" (str): The preferred language of the user.
                                - "dark_mode" (int): The dark mode setting, where 0 indicates disabled and 1 indicates enabled.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            User | bytes: Returns the updated User object or TOON bytes if the update is successful.
        """
        url = f"{self.base_url}/users/{user_id}"
        response = await self.put(url, update_data)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            user_data = response.json()
            return User(**user_data)

    async def create_user(self, new_user: dict, format: str = "json"):
        """
        Creates a new user in the system.

        Args:
            new_user (dict): A dictionary containing the data of the new user to be created. \n
                            The dictionary should include the following keys: \n
                            - "first_name" (str): The first name of the user.
                            - "last_name" (str): The last name of the user.
                            - "email" (str): The email address of the user.
                            - "password" (str): The password for the user.
                            - "language" (str): The preferred language of the user.
                            - "dark_mode" (int): The dark mode setting, where 0 indicates disabled and 1 indicates enabled.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            User | bytes: Returns the newly created User object or TOON bytes if the creation is successful.
        """
        url = f"{self.base_url}/users"
        response = await self.post(url, new_user)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            user_data = response.json()
            return User(**user_data)

    async def delete_user(self, user_id: int, format: str = "json"):
        """
        Deletes a user from the system by user ID.

        Args:
            user_id (int): The unique identifier of the user to be deleted.
            format (str): The desired output format ("json", "toon"). Default is "json".

        Returns:
            User | bytes: Returns the User object or TOON bytes if the deletion is confirmed.
        """
        url = f"{self.base_url}/users/{user_id}"
        response = await self.delete(url)
        if response:
            if format == "toon":
                return json_to_toon_bytes(response.json())
            user_data = response.json()
            return User(**user_data)