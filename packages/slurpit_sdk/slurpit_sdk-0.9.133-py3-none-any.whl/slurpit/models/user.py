from slurpit.models.basemodel import BaseModel

class User(BaseModel):
    """
    Represents a User model, inheriting from BaseModel, and defines attributes specific to a user.
    
    Args:
        id (int): Unique identifier for the user.
        first_name (str): User's first name.
        last_name (str): User's last name.
        email (str): User's email address.
        type (str): Type of user (e.g., admin, user).
        dark_mode (int): Indicates if dark mode is enabled (1) or not (0).
        createddate: The date when the user account was created. Initially set to None.
        changeddate: The date when the user account was last updated. Initially set to None.
    """

    def __init__(
        self,
        id: int,
        first_name: str,
        last_name: str,
        email: str,
        type: str,
        language: str,
        dark_mode: int,
        createddate: str = None,
        changeddate: str = None,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        # Assigning the provided arguments to the instance variables
        self.id = int(id)  # Ensure id is stored as an integer
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.type = type
        self.language = language
        self.dark_mode = int(dark_mode)  # Ensure dark_mode is stored as an integer
        self.createddate = createddate
        self.changeddate = changeddate
