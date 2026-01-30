from slurpit.models.basemodel import BaseModel

class Node(BaseModel):
    """
    This class represents a network device or node with various attributes that help identify and manage it in a network.

    Args:
        ip (str): The IP address of the network node, used for network communication and identification.
        device_type (str): The type of device, such as router, switch, or firewall, which helps in categorizing the node.
        hostname (str): The local name of the device, used for easier identification within a network.
        fqdn (str): The Fully Qualified Domain Name, providing a complete domain name address for the node.
        vendor (str): The manufacturer of the device, giving insights into the device's specifications and compatibility.
        product (str): The specific product name or model of the device as defined by the vendor.
        batch_id (int): A batch identifier that can link this node to a specific production or shipment batch.
        snmp_vars (str): A string representing SNMP variables used for monitoring the device via SNMP.
        timestamp (str): The date and time when the node data was last updated, important for tracking changes.
        error (str): A field to note any errors related to the node, useful for troubleshooting and maintenance.
    """
    def __init__(
        self,
        ip: str,
        device_type: str,
        hostname: str,
        fqdn: str,
        vendor: str,
        product: str,
        batch_id: int,
        snmp_vars: str,
        timestamp: str,
        error: str,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        self.ip = ip
        self.device_type = device_type
        self.hostname = hostname
        self.fqdn = fqdn
        self.vendor = vendor
        self.product = product
        self.batch_id = batch_id
        self.snmp_vars = snmp_vars
        self.timestamp = timestamp
        self.error = error

class DeviceFinder(BaseModel):
    """
    Representation of a Device Finder configuration.

    Args:
        id (int): The unique identifier for the device finder.
        name (str): The name of the device finder.
        group_id (int): The ID of the group to which the device finder belongs.
        target (str): The target IP address or subnet for the device finder.
        snmp_port (int): The SNMP port number for the device finder.
        disabled (int): Whether the device finder is disabled (1) or not (0).
        type (str): The type of device finder. Allowed values: "target", "plugin", "inventory".
        createddate (str): The date and time when the device finder was created.
        changeddate (str): The date and time when the device finder was last modified.
    """
    def __init__(
        self,
        id: int,
        name: str,
        group_id: int,
        target: str,
        snmp_port: int,
        disabled: int,
        type: str = "target",
        createddate: str = None,
        changeddate: str = None,
        snmp_auth: list = None,
        tags: list = None,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)
            
        self.id = id
        self.name = name
        self.group_id = group_id
        self.target = target
        self.snmp_port = snmp_port
        self.disabled = disabled
        self.type = type
        self.createddate = createddate
        self.changeddate = changeddate
        self.snmp_auth = snmp_auth
        self.tags = tags

class DeviceCrawler(BaseModel):
    """
    Representation of a Device Crawler configuration.

    Args:
        id (int): The unique identifier for the device crawler.
        planning_id (int): The ID of the planning to which the device crawler belongs.
        group_id (int): The ID of the group to which the device crawler belongs.
        snmp_port (int): The SNMP port number for the device crawler.
        disabled (int): Whether the device crawler is disabled (1) or not (0).
        include_public_ips (int): Whether to include public IP addresses (1) or not (0).
        createddate (str): The date and time when the device crawler was created.
        changeddate (str): The date and time when the device crawler was last modified.
        snmp_auth (list): List of SNMP authentication methods.
        tags (list, optional): List of tags associated with the device crawler.
    """
    def __init__(
        self,
        id: int,
        planning_id: int,
        group_id: int,
        snmp_port: int,
        disabled: int,
        include_public_ips: int,
        createddate: str = None,
        changeddate: str = None,
        snmp_auth: list = None,
        tags: list = None,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)
            
        self.id = id
        self.planning_id = planning_id
        self.group_id = group_id
        self.snmp_port = snmp_port
        self.disabled = disabled
        self.include_public_ips = include_public_ips
        self.createddate = createddate
        self.changeddate = changeddate
        self.snmp_auth = snmp_auth
        self.tags = tags
