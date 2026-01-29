"""Constants for Hemnet scraper"""

from enum import Enum

# Hemnet URLs mapping
HEMNET_URLS = {
    "listings": "https://www.hemnet.se/bostader",
    "sold": "https://www.hemnet.se/salda/bostader"
}


class HemnetItemType(str, Enum):
    """Hemnet property item types"""
    VILLA = "villa"
    RADHUS = "radhus"
    BOSTADSRATT = "bostadsratt"
    FRITIDSHUS = "fritidshus"
    TOMT = "tomt"
    GARD = "gard"
    OTHER = "other"


# Qasa API configuration
QASA_API_URL = "https://api.qasa.se/graphql"
QASA_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",  # noqa: E501
}


class QasaHomeType(Enum):
    """Qasa home types"""
    HOUSE = ["house"]
    TERRACE_HOUSE = ["terrace_house", "duplex"]
    APARTMENT = ["apartment", "loft"]
    DORM = ["corridor", "room"]
    COTTAGE = ["cottage"]
    OTHER = ["other"]


class QasaShared(Enum):
    """Qasa shared rental options"""
    SHARED = True
    NOT_SHARED = False
    ALL = None


class QasaFurniture(Enum):
    """Qasa furniture options"""
    FURNISHED = True
    UNFURNISHED = False
    ALL = None


class QasaCategory(Enum):
    """Qasa rental category filters (mutually exclusive)"""
    ALL_HOMES = None  # No filter applied
    FIRST_HAND = "firsthand"  # firsthand: true
    STUDENT_HOUSING = "studentHome"  # studentHome: true
    SENIOR_HOUSING = "seniorHome"  # seniorHome: true
    CORPORATE_HOUSING = "corporateHome"  # corporateHome: true


class QasaRules(Enum):
    """Qasa rental rules filters (can be combined)"""
    PETS_ALLOWED = "pets"  # pets: true
    SMOKING_ALLOWED = "smoker"  # smoker: true


# Qasa query parameter names
QASA_PARAM_MIN_MONTHLY_COST = "minMonthlyCost"
QASA_PARAM_MAX_MONTHLY_COST = "maxMonthlyCost"


# Default values
DEFAULT_HOME_TYPES = [
    *QasaHomeType.HOUSE.value,
    *QasaHomeType.TERRACE_HOUSE.value,
]
DEFAULT_SHARED = False
DEFAULT_FURNITURE = None
DEFAULT_CATEGORY = None
DEFAULT_MIN_MONTHLY_COST = None
DEFAULT_MAX_MONTHLY_COST = None
