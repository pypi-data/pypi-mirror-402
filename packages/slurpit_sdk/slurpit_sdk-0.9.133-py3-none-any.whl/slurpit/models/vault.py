from slurpit.models.basemodel import BaseModel

class Vault(BaseModel):
    """
    Vault class represents a vault credential storing sensitive access data.

    Args:
        id (int): The unique identifier for the vault.
        username (str): The username associated with the vault.
        device_os (str): The operating system of the device associated with the vault.
        comment (str): A user-provided comment about the vault.
        group_id (int): Identifier of the group this credential belongs to.
        group_name (str): Display name of the group.
        priority (int): Priority of the credential within the group.
        createddate (str): The date when the vault was created.
        changeddate (str): The date when the vault was last modified.        
    """
    def __init__(
        self,
        id: int,
        username: str,
        device_os: str,
        comment: str,
        group_id: int,
        group_name: str,
        priority: int,
        createddate: str,
        changeddate: str,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        
        self.id = int(id)  # Convert id to int to ensure it's the correct type
        self.username = username  # Store the username
        self.device_os = device_os  # Store the device operating system
        self.comment = comment  # Store the user comment
        self.group_id = group_id  # Group association
        self.group_name = group_name  #display name of the group
        self.priority = priority  # Priority of the credential within the group
        self.createddate = createddate  # Store the creation date
        self.changeddate = changeddate  # Store the last changed date
        

class SingleVault(Vault):
    """
    This class is used for instances where detailed information and password of a specific vault is needed.

    Args:
        id (int): The unique identifier for the vault.
        username (str): The username associated with the vault.
        password (str): The password associated with the vault.
        ssh_key (str): The SSH key associated with the vault.
        ssh_key_passphrase (str): The passphrase for the SSH key.
        enable_password (str): The enable password for the vault.
        device_os (str): The operating system of the device associated with the vault.
        comment (str): A user-provided comment about the vault.
        group_id (int): Identifier of the group this credential belongs to.
        group_name (str): Display name of the group.
        priority (int): Priority of the credential within the group.
        createddate (str): The date when the vault was created.
        changeddate (str): The date when the vault was last modified.        
    """
    def __init__(
        self,
        id: int,
        username: str,
        password: str,
        ssh_key: str,
        ssh_key_passphrase: str,
        enable_password: str,
        device_os: str,
        comment: str,
        group_id: int,
        group_name: str,
        priority: int,
        createddate: str,
        changeddate: str,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        self.password = password  # Store the password
        self.ssh_key = ssh_key  # Store the ssh_key
        self.ssh_key_passphrase = ssh_key_passphrase  # Store the ssh_key_passphrase
        self.enable_password = enable_password  # Store the enable_password
        super().__init__(id, username, device_os, comment, group_id, group_name, priority, createddate, changeddate)
