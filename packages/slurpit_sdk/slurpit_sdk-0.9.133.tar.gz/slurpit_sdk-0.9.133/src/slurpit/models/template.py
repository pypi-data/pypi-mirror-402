from slurpit.models.basemodel import BaseModel

class Template(BaseModel):
    """
    Represents a Template model, inheriting from BaseModel, designed to manage templates 
    for different devices and commands.

    Args:
        id (int): Unique identifier for the template.
        device_os (str): Operating system of the device for which the template is intended.
        type (str): Type of the template (e.g., configuration, automation).
        name (str): Descriptive name of the template.
        command (str): Command or action that the template automates or configures.
        content (str): Detailed content or script of the template.
        variables (str): Variables required by the template, typically in a serialized format.
    """

    def __init__(
        self,
        id: int,
        device_os: str,
        type: str,
        name: str,
        command: str,
        content: str,
        variables: str,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        # Assigning the provided arguments to the instance variables
        self.id = int(id)  # Ensure id is stored as an integer
        self.device_os = device_os
        self.type = type
        self.name = name
        self.command = command
        self.content = content
        self.variables = variables
