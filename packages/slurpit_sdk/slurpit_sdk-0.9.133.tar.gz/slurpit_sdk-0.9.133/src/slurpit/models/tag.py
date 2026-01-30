from slurpit.models.basemodel import BaseModel

class Tag(BaseModel):
    """
    This class represents a tag.

    Args:
        id (int): Unique identifier for the tag.
        name (str): Name of the tag.
        type (str): Type of the tag.
        tagRules (list): List of TagRule objects associated with this tag.
    """
    def __init__(
        self,
        id: int,
        name: str,
        type: str,
        tagRules: list = [],
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        self.id = int(id)
        self.name = name
        self.type = type
        self.tagRules = tagRules

class TagRule(BaseModel):
    """
    This class represents a tag rule.

    Args:
        id (int): Unique identifier for the tag rule.
        rule (str): The rule to be applied.
        applied_to (str): The element to which the rule is applied.
        rule_order (int): The order of the rule.
        tag_id (int): The ID of the tag to which the rule is applied.
        disabled (int): Whether the rule is disabled.
        createddate (str): The date the rule was created.
        changeddate (str): The date the rule was last updated.
    """
    def __init__(
        self,
        id: int,
        rule: str,
        applied_to: str,
        rule_order: int = 0,
        tag_id: int = 0,
        disabled: int = 0,
        createddate: str = None,
        changeddate: str = None,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        self.id = int(id)
        self.rule = rule
        self.applied_to = applied_to
        self.rule_order = rule_order
        self.tag_id = tag_id
        self.disabled = disabled
        self.createddate = createddate
        self.changeddate = changeddate
