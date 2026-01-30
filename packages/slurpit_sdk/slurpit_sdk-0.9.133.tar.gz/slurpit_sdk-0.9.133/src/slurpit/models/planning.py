from slurpit.models.basemodel import BaseModel

class Planning(BaseModel):
    """
    This class represents a planning entity with various attributes used in management systems.

    Args:
        id (int): Unique identifier for the planning entry.
        name (str): Name of the planning entry.
        comment (int): Numeric comment identifier, which could link to further details or logs.
        disabled (str): Indicates the status of the planning entry, whether it's active or disabled.
        columns (list): A list of column names or specifications used in the planning entry.
        createddate (str): The date when the planning entry was created.
        changeddate (str): The date when the planning entry was last updated or modified.
    """
    
    def __init__(
        self,
        id: int,
        name: str,
        comment: int,
        disabled: str,
        columns: list,
        slug: str,
        createddate: str = None,
        changeddate: str = None,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)
        
        self.id = int(id)
        self.name = name
        self.comment = comment
        self.disabled = disabled
        self.columns = columns
        self.slug = slug
        self.createddate = createddate
        self.changeddate = changeddate
