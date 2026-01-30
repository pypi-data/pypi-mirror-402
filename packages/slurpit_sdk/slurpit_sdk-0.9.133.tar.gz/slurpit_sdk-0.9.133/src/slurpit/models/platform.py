from slurpit.models.basemodel import BaseModel

class Platform(BaseModel):
    """
    This class represent platform status.

    Args:
        status (str): The status of the platform, indicating its current operational state.
    """
    def __init__(self, status: str, **extra):
        if extra:
            self.notify_unrecognized_fields(extra)

        self.status = status  # Store the platform's status

class PlatformLicense(BaseModel):
    """
    This class represents the Platform License details.

    Args:
        status (str): License status
        always_online (int): Does the system require an active internet connection
        amount_of_devices (int): Amount of devices that are licensed
        enterprise (int): Are enterprise features enabled
        license_end_date (str): The date the license ends
    """

    def __init__(
        self,
        status: str,
        always_online: int,
        amount_of_devices: int,
        enterprise: int,
        license_end_date: str,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        self.status = status
        self.always_online = int(always_online)
        self.amount_of_devices = int(amount_of_devices)
        self.enterprise = int(enterprise)
        self.license_end_date = license_end_date