from slurpit.models.basemodel import BaseModel

class Site(BaseModel):
    """
    This class represents a site.

    Args:
        id (int): Unique identifier for the site.
        sitename (str): Name of the site.
        description (str): Description of the site.
        street (str): Street of the site.
        county (str): County (district) of the site.
        state (str): State of the site.
        number (str): Number of the site.
        zipcode (str): Zipcode of the site.
        city (str): City of the site.
        country (str): Country of the site.
        phonenumber (int): Phone number of the site.
        status (int): Status flag where 0 indicates enabled and 1 indicates disabled.
        longitude (str): Longitude of the site.
        latitude (str): Latitude of the site.
        siteRules (dict): List of all Site rules that apply to this site
        createddate (str): Date site was created.
        changeddate (str): Date site was updated.
    """

    def __init__(
        self,
        id: int,
        sitename: str,
        description: str,
        street: str,
        county: str,
        state: str,
        number: str,
        zipcode: str,
        city: str,
        country: str,
        phonenumber: int,
        status: int,
        longitude: str,
        latitude: str,
        createddate: str = None,
        changeddate: str = None,
        siteRules: dict = [],
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        self.id = int(id)
        self.sitename = sitename
        self.description = description
        self.street = street
        self.county = county
        self.state = state
        self.number = number
        self.zipcode = zipcode
        self.city = city
        self.country = country
        self.phonenumber = phonenumber
        self.status = status
        self.longitude = longitude
        self.latitude = latitude
        self.createddate = createddate
        self.changeddate = changeddate
        self.siteRules = siteRules


class SiteRule(BaseModel):
    """
    This class represents a site rule.

    Args:
        id (int): Unique identifier for the site rule.
        rule (str): The rule to be applied.
        applied_to (str): The element to which the rule is applied.
        rule_order (int): The order of the rule.
        site_id (int): The ID of the site to which the rule is applied.
        create_site (int): Flag where 1 will create-site and 0 will select existing site.
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
        site_id: int = 0,
        create_site: int = 0,
        disabled: int = 0,
        createddate: str = None,
        changeddate: str = None,
        **extra
    ):
        if extra:
            self.notify_unrecognized_fields(extra)

        self.id = int(id)
        self.rule = rule
        self.rule_order = rule_order
        self.site_id = site_id
        self.applied_to = applied_to
        self.create_site = create_site
        self.disabled = disabled
        self.createddate = createddate
        self.changeddate = changeddate