"""Qasa scraper module for rental property data extraction"""

import datetime as dt
import logging
from datetime import datetime

import requests

from .constants import (
    QASA_API_URL,
    QASA_HEADERS,
    DEFAULT_HOME_TYPES,
    DEFAULT_SHARED,
    DEFAULT_FURNITURE,
    DEFAULT_CATEGORY,
    DEFAULT_MIN_MONTHLY_COST,
    DEFAULT_MAX_MONTHLY_COST,
)

logger = logging.getLogger(__name__)


class QasaScraper:
    """Scraper for Qasa rental property data

    Examples:
        >>> scraper = QasaScraper()
        >>> homes = scraper.get_homes(
        ...     area_identifier="se/helsingborg",
        ...     home_types=["house", "terrace_house"]
        ... )
        >>> details = scraper.get_home_details(home_id="12345")
    """

    def __init__(self):
        """Initialize the Qasa scraper"""
        self.url = QASA_API_URL
        self.headers = QASA_HEADERS.copy()

    @staticmethod
    def _parse_date(date_string: str | None) -> dt.date | None:
        """Parse ISO datetime string and return date object (internal helper)

        Args:
            date_string: ISO format datetime string

        Returns:
            Date object or None if parsing fails
        """
        if not date_string:
            return None
        try:
            # Parse ISO datetime string like "2026-01-06T00:00:00+00:00"
            dt_obj = datetime.fromisoformat(date_string)
            return dt_obj.date()
        except (ValueError, AttributeError, TypeError):
            return None

    def _make_request(self, payload: dict) -> dict:
        """Make GraphQL request to Qasa API (internal)

        Args:
            payload: GraphQL query payload

        Returns:
            Response data from API

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails
            ValueError: If the response is invalid
        """
        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request failed: {e}")

    def _parse_home_list(self, data: dict) -> list[dict]:
        """Parse home list data from API response (internal)

        Args:
            data: Parsed JSON data from API

        Returns:
            List of dictionaries containing home details

        Raises:
            ValueError: If required data structure is missing or invalid
        """
        try:
            homes = data["data"]["homeIndexSearch"]["documents"]["nodes"]

            parsed_homes = []
            for home in homes:
                try:
                    location = home.get("location", {})
                    parsed_homes.append({
                        "id": home.get("id"),
                        "title": home.get("title"),
                        "rent": home.get("rent"),
                        "currency": home.get("currency"),
                        "rooms": home.get("roomCount"),
                        "square_meters": home.get("squareMeters"),
                        "start_date": self._parse_date(home.get("startDate")),
                        "locality": location.get("locality"),
                        "route": location.get("route"),
                        "street_number": location.get("streetNumber"),
                        "country_code": location.get("countryCode"),
                    })
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Skipping home {home.get('id', 'unknown')}: {e}")
                    continue

            return parsed_homes
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid JSON structure: {e}")

    def _parse_home_details(self, data: dict) -> dict:
        """Parse detailed home data from API response (internal)

        Args:
            data: Parsed JSON data from API

        Returns:
            Dictionary containing detailed home information

        Raises:
            ValueError: If required data structure is missing or invalid
        """
        try:
            home = data["data"]["home"]
            if home is None:
                raise ValueError("Home not found or invalid home ID")

            return {
                "id": home.get("id"),
                "title": home.get("title"),
                "rent": home.get("rent"),
                "roomCount": home.get("roomCount"),
                "squareMeters": home.get("squareMeters"),
                "currency": home.get("currency"),
                "description": home.get("description"),
                "shared": home.get("shared"),
                "firsthand": home.get("firsthand"),
                "studentHome": home.get("studentHome"),
                "seniorHome": home.get("seniorHome"),
                "corporateHome": home.get("corporateHome"),
                "floor": home.get("floor"),
                "buildingFloors": home.get("buildingFloors"),
                "bedCount": home.get("bedCount"),
                "bedroomCount": home.get("bedroomCount"),
                "hasKitchen": home.get("hasKitchen"),
                "toiletCount": home.get("toiletCount"),
                "houseRules": home.get("houseRules"),
                "housingAssociation": home.get("housingAssociation"),
                "location": home.get("location"),
                "landlord": home.get("landlord"),
                "duration": home.get("duration"),
                "electricityFee": home.get("electricityFee"),
                "heatingFee": home.get("heatingFee"),
                "waterFee": home.get("waterFee"),
                "tenantBaseFee": home.get("tenantBaseFee"),
                "rentalType": home.get("rentalType"),
                "rentalRequirement": home.get("rentalRequirement"),
                "status": home.get("status"),
                "publishedAt": home.get("publishedAt"),
                "buildYear": home.get("buildYear"),
                "energyClass": home.get("energyClass"),
                "kitchenRenovationYear": home.get("kitchenRenovationYear"),
                "bathroomRenovationYear": home.get("bathroomRenovationYear"),
                "tenantCount": home.get("tenantCount"),
                "minTenantCount": home.get("minTenantCount"),
                "maxTenantCount": home.get("maxTenantCount"),
                "tenureType": home.get("tenureType"),
            }
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid JSON structure for home details: {e}")

    def get_homes(
        self,
        area_identifier: str | list[str] = [],
        home_types: list[str] | None = DEFAULT_HOME_TYPES,
        shared: bool | None = DEFAULT_SHARED,
        furnished: bool | None = DEFAULT_FURNITURE,
        category: str | None = DEFAULT_CATEGORY,
        pets_allowed: bool = False,
        smoking_allowed: bool = False,
        min_monthly_cost: int | None = DEFAULT_MIN_MONTHLY_COST,
        max_monthly_cost: int | None = DEFAULT_MAX_MONTHLY_COST,
    ) -> list[dict]:
        """Get list of available rental homes from Qasa

        Args:
            area_identifier: Area identifier(s) (e.g., "se/helsingborg")
            home_types: List of home types (e.g., ["house", "terrace_house", "duplex"])
            shared: Whether shared rentals (True), non-shared (False), or all (None)
            furnished: Whether furnished (True), unfurnished (False), or all (None)
            category: Category filter ("firsthand", "studentHome", "seniorHome", "corporateHome", or None)
            pets_allowed: Whether pets are allowed (default: False)
            smoking_allowed: Whether smoking is allowed (default: False)
            min_monthly_cost: Minimum monthly rent cost
            max_monthly_cost: Maximum monthly rent cost

        Returns:
            List of dictionaries containing home details

        Raises:
            ValueError: If the API response is invalid or data cannot be parsed
            requests.exceptions.HTTPError: If the HTTP request fails
        """
        # Normalize area_identifier to list
        if isinstance(area_identifier, str):
            area_identifier = [area_identifier]

        payload = {
            "operationName": "HomeSearch",
            "query": """
                query HomeSearch(
                    $order: HomeIndexSearchOrderInput,
                    $offset: Int,
                    $limit: Int,
                    $params: HomeSearchParamsInput
                ) {
                homeIndexSearch(order: $order, params: $params) {
                    documents(offset: $offset, limit: $limit) {
                    hasNextPage
                    hasPreviousPage
                    nodes {
                        id
                        title
                        rent
                        currency
                        roomCount
                        squareMeters
                        startDate
                        location {
                        locality
                        route
                        streetNumber
                        countryCode
                        point {
                            lat
                            lon
                        }
                        }
                        uploads {
                        url
                        type
                        }
                    }
                    totalCount
                    pagesCount
                    }
                }
                }
            """,
            "variables": {
                "limit": 60,
                "offset": 0,
                "order": {"direction": "descending", "orderBy": "published_or_bumped_at"},
                "params": {
                    "areaIdentifier": area_identifier,
                    "currency": "SEK",
                    "market": "sweden",
                    "rentalType": ["long_term"],
                },
            },
        }

        # Add optional parameters
        if home_types:
            payload["variables"]["params"]["homeType"] = home_types
        if shared is not None:
            payload["variables"]["params"]["shared"] = shared
        if furnished is not None:
            payload["variables"]["params"]["furnished"] = furnished
        if category:
            payload["variables"]["params"][category] = True
        if pets_allowed:
            payload["variables"]["params"]["pets"] = True
        if smoking_allowed:
            payload["variables"]["params"]["smoker"] = True
        if min_monthly_cost is not None:
            payload["variables"]["params"]["minMonthlyCost"] = min_monthly_cost
        if max_monthly_cost is not None:
            payload["variables"]["params"]["maxMonthlyCost"] = max_monthly_cost

        try:
            data = self._make_request(payload)
            return self._parse_home_list(data)
        except ValueError as e:
            raise ValueError(f"Failed to get homes: {e}")

    def get_home_details(self, home_id: str) -> dict:
        """Get detailed information for a specific home

        Args:
            home_id: Qasa home ID

        Returns:
            Dictionary containing detailed home information, including:
                - Basic info: id, title, rent, rooms, square_meters, currency
                - Location: locality, latitude, longitude, route, street_number
                - Landlord info: name, company, premium status
                - Duration: start/end dates, possibility of extension
                - Requirements: credit check, income verification
                - Additional: traits, points of interest, images

        Raises:
            ValueError: If the API response is invalid or data cannot be parsed
            requests.exceptions.HTTPError: If the HTTP request fails
        """
        payload = {
            "operationName": "HomeView",
            "query": """
                query HomeView($id: ID!) {
                home(id: $id) {
                    id
                    title
                    rent
                    roomCount
                    squareMeters
                    currency
                    description
                    shared
                    firsthand
                    studentHome
                    seniorHome
                    corporateHome
                    floor
                    buildingFloors
                    bedCount
                    bedroomCount
                    hasKitchen
                    toiletCount
                    houseRules
                    housingAssociation
                    location {
                    locality
                    latitude
                    longitude
                    route
                    streetNumber
                    countryCode
                    postalCode
                    pointsOfInterest(first: 5) {
                        nodes {
                        category
                        distance
                        name
                        latitude
                        longitude
                        }
                    }
                    }
                    landlord {
                    uid
                    firstName
                    companyName
                    premium
                    professional
                    mainPlatform
                    proAgent
                    landlordApplicationResponseRate
                    landlordApplicationResponseTimeHours
                    contactLocation {
                        postalCode
                        route
                        streetNumber
                        locality
                    }
                    bio {
                        intro
                    }
                    createdAt
                    seenAt
                    }
                    duration {
                    startOptimal
                    endOptimal
                    startAsap
                    endUfn
                    possibilityOfExtension
                    }
                    electricityFee {
                    paymentPlan
                    monthlyFee
                    }
                    heatingFee {
                    paymentPlan
                    monthlyFee
                    }
                    waterFee {
                    paymentPlan
                    monthlyFee
                    }
                    tenantBaseFee
                    rentalType
                    rentalRequirement {
                    approvedCreditCheck
                    verifiedIncome
                    rentMultiplier
                    verifiedIdNumber
                    }
                    status
                    publishedAt
                    buildYear
                    energyClass
                    kitchenRenovationYear
                    bathroomRenovationYear
                    tenantCount
                    minTenantCount
                    maxTenantCount
                    tenureType
                }
                }
            """,
            "variables": {"id": home_id},
        }

        try:
            data = self._make_request(payload)
            return self._parse_home_details(data)
        except ValueError as e:
            raise ValueError(f"Failed to get home details: {e}")
