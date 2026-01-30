from slurpit.models.basemodel import BaseModel

class Device(BaseModel):
    """
    This class represents a network device with various attributes.

    Args:
        id (int): Unique identifier for the device.
        hostname (str): Hostname of the device.
        fqdn (str): Fully qualified domain name of the device.
        address (str, optional): IP address assigned to the device.
        family (str, optional): Address family, e.g., 'IPv4' or 'IPv6'.
        port (int, optional): Network port number primarily used by the device.
        device_os (str): Operating system running on the device.
        os_version (str, optional): Device OS version.
        serial (str, optional): Device Hardware Serial collected by SNMP.
        device_type (str, optional): Type of the device, such as 'router' or 'switch'.
        brand (str, optional): Brand of the device, e.g., 'Cisco'.
        telnet (int, optional): Telnet enabled flag (0 or 1).
        disabled (int): Indicates whether the device is disabled (0 or 1).
        vault_group_id (int, optional): Vault group identifier.
        group_name (str, optional): Vault group display name (read-only).
        site (str, optional): Site Name as created in Sites. When not defined site rules will apply.
        description (str, optional): Description.
        added (str, optional): Date when the device was added to the system.
        snmp_contact (str, optional): Device Contact collected by SNMP.
        snmp_description (str, optional): Device Description collected by SNMP.
        snmp_location (str, optional): Device Location collected by SNMP.
        snmp_uptime (str, optional): Device Uptime collected by SNMP.
        snmp_port (int, optional): SNMP Port number.
        last_seen (str, optional): Last date when the device was active or seen.
        tags (str, optional): Tags associated with the device.
        createddate (str, optional): The date the device record was created.
        changeddate (str, optional): The date the device record was last modified.
        blacklisted (int, optional): Indicates whether the device is blacklisted (0 or 1).
        worker_id (int, optional): ID of the worker that processed the device (read-only).

    """
        
    def __init__(
        self,
        id: int,
        hostname: str,
        fqdn: str,
        device_os: str,
        disabled: int,
        address: str = None,
        family: str = None,
        os_version: str = None,
        serial: str = None,
        snmp_contact: str = None,
        snmp_description: str = None,
        snmp_location: str = None,
        snmp_uptime: str = None,
        snmp_port: int = None,
        telnet:int = None,
        device_type: str = None,
        brand: str = None,
        added: str = None,
        last_seen: str = None,
        port: int = None,
        vault_group_id: int = None,
        group_name: str = None,
        site: str = None,
        tags: str = None,
        description: str = None,
        createddate: str = None,
        changeddate: str = None,
        blacklisted: int = 0,
        worker_id: str = None,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)
            
        self.id = int(id)
        self.hostname = hostname
        self.fqdn = fqdn
        self.port = int(port)
        self.address = address 
        self.family = family
        self.device_os = device_os
        self.telnet = int(telnet) if telnet is not None else None
        self.disabled = int(disabled)
        self.os_version = os_version
        self.serial = serial
        self.snmp_contact = snmp_contact
        self.snmp_description = snmp_description
        self.snmp_location = snmp_location
        self.snmp_uptime = snmp_uptime
        self.snmp_port = int(snmp_port) if snmp_port is not None else None  
        self.device_type = device_type
        self.brand = brand
        self.added = added
        self.last_seen = last_seen
        self.vault_group_id = vault_group_id
        self.group_name = group_name
        self.site = site
        self.tags = tags
        self.description = description if description is not None else None
        self.createddate = createddate
        self.changeddate = changeddate
        self.blacklisted = blacklisted
        self.worker_id = worker_id

class Vendor(BaseModel):
    """
    This class represents a vendor, defined primarily by the operating system and brand.

    Args:
        device_os (str): Operating system commonly associated with the vendor.
        brand (str): Brand name of the vendor, e.g., 'Apple' or 'Samsung'.
    """
    def __init__(
        self,
        device_os: str,
        brand: str,
        telnet: str = None,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)
       
        self.device_os = device_os
        self.brand = brand
        self.telnet = telnet

class DeviceProfile(BaseModel):
    """
    Represents a device profile with connection preferences and flags.

    Args:
        device_id (int): Read-only unique identifier for the device this profile belongs to.
        timeout (int): Timeout value (seconds) for device interactions.
        preferred_ssh_vault_id (int): Preferred SSH credential vault ID.
        preferred_snmp_vault_id (int): Preferred SNMP credential vault ID.
        blacklisted (int): Whether the device is blacklisted (0 or 1).
    """

    def __init__(
        self,
        device_id: int,
        timeout: int,
        preferred_ssh_vault_id: int = None,
        preferred_snmp_vault_id: int = None,
        blacklisted: int = 0,
        profiler_batch_id: int = None,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)
 
        self.device_id = int(device_id)
        self.timeout = int(timeout) if timeout is not None else None
        self.preferred_ssh_vault_id = (
            int(preferred_ssh_vault_id) if preferred_ssh_vault_id is not None else None
        )
        self.preferred_snmp_vault_id = (
            int(preferred_snmp_vault_id) if preferred_snmp_vault_id is not None else None
        )
        self.blacklisted = int(blacklisted) if blacklisted is not None else 0
        self.profiler_batch_id = int(profiler_batch_id) if profiler_batch_id is not None else None
