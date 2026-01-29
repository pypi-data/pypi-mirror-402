"""Tests for Qasa scraper"""

from unittest.mock import patch, Mock
import pytest

from pyhemnet import QasaScraper


@pytest.fixture
def scraper():
    """Create a QasaScraper instance for testing"""
    return QasaScraper()


@pytest.fixture
def mock_homes_response():
    """Mock API response for home search"""
    return {
        "data": {
            "homeIndexSearch": {
                "documents": {
                    "nodes": [
                        {
                            "id": "home123",
                            "title": "Cozy apartment in Helsingborg",
                            "rent": 12000,
                            "currency": "SEK",
                            "roomCount": 3,
                            "squareMeters": 75,
                            "startDate": "2026-02-01T00:00:00+00:00",
                            "location": {
                                "locality": "Helsingborg",
                                "route": "Storgatan",
                                "streetNumber": "10",
                                "countryCode": "SE",
                            },
                        }
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_home_details_response():
    """Mock API response for detailed home information"""
    return {
        "data": {
            "home": {
                "id": "home123",
                "title": "Cozy apartment in Helsingborg",
                "rent": 12000,
                "roomCount": 3,
                "squareMeters": 75,
                "currency": "SEK",
                "description": "Beautiful apartment in the city center",
                "location": {
                    "locality": "Helsingborg",
                    "latitude": 56.0465,
                    "longitude": 12.6945,
                },
                "landlord": {"firstName": "John", "premium": True},
                "duration": {"startOptimal": "2026-02-01T00:00:00+00:00"},
                "electricityFee": {"paymentPlan": "included"},
                "heatingFee": {"paymentPlan": "included"},
                "waterFee": {"paymentPlan": "included"},
                "rentalRequirement": {"approvedCreditCheck": True},
            }
        }
    }


class TestQasaScraper:
    """Test cases for QasaScraper class"""

    def test_init(self, scraper):
        """Test scraper initialization"""
        assert scraper.url == "https://api.qasa.se/graphql"
        assert "Content-Type" in scraper.headers

    @patch("requests.post")
    def test_get_homes(self, mock_post, scraper, mock_homes_response):
        """Test home search"""
        mock_response = Mock()
        mock_response.json.return_value = mock_homes_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        homes = scraper.get_homes(area_identifier="se/helsingborg")

        assert len(homes) == 1
        assert homes[0]["id"] == "home123"
        assert homes[0]["rent"] == 12000
        assert homes[0]["locality"] == "Helsingborg"

    @patch("requests.post")
    def test_get_home_details(self, mock_post, scraper, mock_home_details_response):
        """Test home details retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = mock_home_details_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        details = scraper.get_home_details(home_id="home123")

        assert details["id"] == "home123"
        assert details["rent"] == 12000
        assert details["location"]["locality"] == "Helsingborg"
        assert details["landlord"]["firstName"] == "John"

    @patch("requests.post")
    def test_error_handling(self, mock_post, scraper):
        """Test error handling"""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        with pytest.raises(ValueError):
            scraper.get_homes(area_identifier="se/helsingborg")
