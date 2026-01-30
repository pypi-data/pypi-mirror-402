from slurpit.models.basemodel import BaseModel

class VaultSnmpCredentials(BaseModel):
    """
    Vault SNMP Credentials model representing SNMP credential information.
    
    Args:
        id (int): The unique identifier for the SNMP credential (read-only).
        snmp_version (str): The SNMP version (e.g., "snmpv2c", "snmpv3").
        description (str): Description of the SNMP credential.
        group_id (int): Identifier of the group this credential belongs to.
        group_name (str): Display name of the group (read-only).
        priority (int): Priority of the credential within the group (read-only).
        createddate (str): The date when the credential was created (read-only).
        changeddate (str): The date when the credential was last modified (read-only).
    """
    def __init__(
        self,
        id: int,
        snmp_version: str,
        description: str,
        group_id: int,
        group_name: str,
        priority: int,
        createddate: str,
        changeddate: str,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        self.id = int(id)  # Convert to int to ensure correct type
        self.snmp_version = snmp_version  # Store the SNMP version
        self.description = description  # Store the description
        self.group_id = int(group_id)  # Convert to int for consistent data type
        self.group_name = group_name  # Store the group name
        self.priority = int(priority)  # Convert to int for consistent data type
        self.createddate = createddate  # Store the creation date
        self.changeddate = changeddate  # Store the last changed date

class SingleVaultSnmpCredentials(VaultSnmpCredentials):
    """
    Detailed representation of SNMP credentials including all SNMP version specific fields.
    
    Args:
        id (int): The unique identifier for the SNMP credential (read-only).
        snmp_version (str): The SNMP version (e.g., "snmpv2c", "snmpv3").
        description (str): Description of the SNMP credential.
        group_id (int): Identifier of the group this credential belongs to.
        group_name (str): Display name of the group (read-only).
        snmpv2ckey (str): SNMPv2c community string.
        snmpv3username (str): SNMPv3 username.
        snmpv3authtype (str): SNMPv3 authentication type.
        snmpv3authkey (str): SNMPv3 authentication key.
        snmpv3privtype (str): SNMPv3 privacy type.
        snmpv3privkey (str): SNMPv3 privacy key.
        priority (int): Priority of the credential within the group (read-only).
        createddate (str): The date when the credential was created (read-only).
        changeddate (str): The date when the credential was last modified (read-only).
    """
    def __init__(
        self,
        id: int,
        snmp_version: str,
        description: str,
        group_id: int,
        group_name: str,
        snmpv2ckey: str,
        snmpv3username: str,
        snmpv3authtype: str,
        snmpv3authkey: str,
        snmpv3privtype: str,
        snmpv3privkey: str,
        priority: int,
        createddate: str,
        changeddate: str,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        # Store SNMP version specific fields
        self.snmpv2ckey = snmpv2ckey  # Store the SNMPv2c community string
        self.snmpv3username = snmpv3username  # Store the SNMPv3 username
        self.snmpv3authtype = snmpv3authtype  # Store the SNMPv3 authentication type
        self.snmpv3authkey = snmpv3authkey  # Store the SNMPv3 authentication key
        self.snmpv3privtype = snmpv3privtype  # Store the SNMPv3 privacy type
        self.snmpv3privkey = snmpv3privkey  # Store the SNMPv3 privacy key
        
        # Initialize the base class with common fields
        super().__init__(id, snmp_version, description, group_id, group_name, priority, createddate, changeddate)
