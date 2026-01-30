from slurpit.models.basemodel import BaseModel

class VaultSnmpGroup(BaseModel):
    """
    Vault SNMP Group model representing a group of SNMP credentials.
    
    Args:
        group_id (int): The unique identifier for the SNMP group (read-only).
        group_name (str): The name of the SNMP group.
    """
    def __init__(
        self,
        group_id: int,
        group_name: str,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        self.group_id = int(group_id)  # Convert to int to ensure correct type
        self.group_name = group_name  # Store the group name

class SingleVaultSnmpGroup(VaultSnmpGroup):
    """
    Vault SNMP Group model that includes associated credentials.
    
    Args:
        group_id (int): The unique identifier for the SNMP group (read-only).
        group_name (str): The name of the SNMP group.
        credentials (list): List of credential objects associated with this group.
    """
    def __init__(
        self,
        group_id: int,
        group_name: str,
        credentials: list,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        super().__init__(group_id, group_name)  # Initialize the base class
        self.credentials = credentials  # Store the list of credentials
