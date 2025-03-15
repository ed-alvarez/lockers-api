from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DetailModel(BaseModel):
    detail: str


class OrgSubscriptionInterval(Enum):
    monthly = "monthly"
    yearly = "yearly"


class OrgSubscriptionType(Enum):
    gold = "gold"
    premium = "premium"


class StripeCapabilities(BaseModel):
    card_payments: Optional[str]
    transfers: Optional[str]


class StripeAccount(BaseModel):
    id: str
    capabilities: StripeCapabilities
    details_submitted: bool
    email: str


class StripeCountry(Enum):
    # Euro
    AT = "AT"  # Austria
    BE = "BE"  # Belgium
    FI = "FI"  # Finland
    FR = "FR"  # France
    DE = "DE"  # Germany
    IE = "IE"  # Ireland
    IT = "IT"  # Italy
    NL = "NL"  # Netherlands
    PT = "PT"  # Portugal
    ES = "ES"  # Spain

    # GBP
    GB = "GB"  # United Kingdom / Great Britain

    # Dollar
    AU = "AU"  # Australia
    CA = "CA"  # Canada
    US = "US"  # United States


class OrgSubscriptionRequest(BaseModel):
    interval: OrgSubscriptionInterval
    plan_type: OrgSubscriptionType

    class Config:
        allow_population_by_field_name = True
        exclude_none = True
        min_anystr_length = 1


class StripePrice(BaseModel):
    recurring: Optional[dict]
    id: str
    product: str
