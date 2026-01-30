from slurpit.models.basemodel import BaseModel

class SshGroup(BaseModel):
    """
    SSH Group model representing a group of SSH credentials.
    
    Args:
        group_id (int): The unique identifier for the SSH group (read-only).
        group_name (str): The name of the SSH group.
        default (int): Indicates if this is the default SSH group (0 for no, 1 for yes).
    """
    def __init__(
        self,
        group_id: int,
        group_name: str,
        default: int,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        self.group_id = int(group_id)  # Convert to int to ensure correct type
        self.group_name = group_name  # Store the group name
        self.default = int(default)  # Convert to int for consistent data type

class SingleSshGroup(SshGroup):
    """
    SSH Group model that includes associated credentials.
    
    Args:
        group_id (int): The unique identifier for the SSH group (read-only).
        group_name (str): The name of the SSH group.
        default (int): Indicates if this is the default SSH group (0 for no, 1 for yes).
        credentials (list): List of credential objects associated with this group.
    """
    def __init__(
        self,
        group_id: int,
        group_name: str,
        default: int,
        credentials: list,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        super().__init__(group_id, group_name, default)  # Initialize the base class
        self.credentials = credentials  # Store the list of credentials
