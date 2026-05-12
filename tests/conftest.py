import sys
import os
from pathlib import Path
import pytest
import json
import base64

fake_key = base64.b64encode(b"x" * 64).decode("ascii")
os.environ.setdefault("COSMOS_KEY", fake_key)

PROJECT_ROOT = Path(__file__).parent.parent
FUNCTIONS_DIR = PROJECT_ROOT / "functions"
RESOURCES_DIR = PROJECT_ROOT / "resources"
sys.path.insert(0, str(FUNCTIONS_DIR))

os.environ.setdefault("DOC_INTELLIGENCE_ENDPOINT", "https://test.cognitiveservices.azure.com/")
os.environ.setdefault("DOC_INTELLIGENCE_KEY", "test-key")
os.environ.setdefault("GOOGLE_PLACES_KEY", "test-key")
os.environ.setdefault("COSMOS_ENDPOINT", "https://test.documents.azure.com:443/")
os.environ.setdefault("COSMOS_KEY", "test-key")
os.environ.setdefault("COSMOS_DATABASE", "test-db")
os.environ.setdefault("COSMOS_CONTAINER", "test-container")
os.environ.setdefault("SERVICE_BUS_CONNECTION", "Endpoint=sb://test.servicebus.windows.net/")
os.environ.setdefault("SERVICE_BUS_QUEUE", "test-queue")
os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_DATABASE_ID", "test-db-id")

@pytest.fixture
def receipt_sample_bytes() -> bytes:
    return (RESOURCES_DIR / "receipt_sample.png").read_bytes()


@pytest.fixture
def parsed_receipt() -> dict:
    return json.loads((RESOURCES_DIR / "parse_receipt_resp.json").read_text())


@pytest.fixture
def review_payload() -> dict:
    return json.loads((RESOURCES_DIR / "review_payload.json").read_text())


@pytest.fixture
def cosmos_items() -> list[dict]:
    return json.loads((RESOURCES_DIR / "cosmos_items.json").read_text())

@pytest.fixture
def sample_review():
    return {
        "id": "r1",
        "city": "Venice",
        "merchant": {
            "name": "La Cabaña",
            "city": "Venice",
            "country": "USA",
            "address": "738 Rose Ave",
            "google_rating": 4.4,
            "google_review_count": 929,
            "place_id": "ChIJabc123"
        },
        "dishes": [
            {"name": "Tacos", "price": 18.0, "dish_rating": 5, "dish_note": "Great"},
            {"name": "Margarita", "price": 12.75, "dish_rating": 4, "dish_note": "Good"}
        ],
        "my_rating": 4.5,
        "my_note": "Authentic vibe",
        "participant_count": 2,
        "total": 57.71,
        "currency": "USD",
        "visit_date": "2024-03-10",
        "created_at": "2024-03-11T08:00:00+00:00"
    }


@pytest.fixture
def sample_reviews():
    return [
        {
            "id": "rr1",
            "city": "Las Vegas",
            "merchant": {
                "name": "La Cabaña1", 
                "city": "Las Vegas", 
                "country": "USA", 
                "address": "",
                "google_rating": 4.3,
                "google_review_count": 929,
                "place_id": ""
            },
            "dishes": [{"name": "Tacos", "price": 18, "dish_rating": 5, "dish_note": ""}],
            "my_rating": 5,
            "my_note": "Excellent",
            "participant_count": 1,
            "total": 30,
            "currency": "USD",
            "visit_date": "2024-03-01",
            "created_at": "2024-03-02T00:00:00+00:00"
        },
        {
            "id": "rr2",
            "city": "Venice",
            "merchant": {
                "name": "La Cabaña2", 
                "city": "Venice", 
                "country": "USA", 
                "address": "",
                "google_rating": 4.3,
                "google_review_count": 929,
                "place_id": ""
            },
            "dishes": [{"name": "Tacos", "price": 18, "dish_rating": 5, "dish_note": ""}],
            "my_rating": 3,
            "my_note": "Excellent",
            "participant_count": 1,
            "total": 25.1,
            "currency": "USD",
            "visit_date": "2024-03-05",
            "created_at": "2024-03-05T00:00:00+00:00"
        },
        {
            "id": "rr3",
            "city": "Eindhoven",
            "merchant": {
                "name": "La Cabaña3", 
                "city": "Eindhoven", 
                "country": "Netherlands", 
                "address": "",
                "google_rating": 4.3,
                "google_review_count": 929,
                "place_id": ""
            },
            "dishes": [{"name": "Tacos", "price": 18, "dish_rating": 5, "dish_note": ""}],
            "my_rating": 3,
            "my_note": "Excellent",
            "participant_count": 1,
            "total": 35.1,
            "currency": "EUR",
            "visit_date": "2024-03-10",
            "created_at": "2024-03-12T00:00:00+00:00"
        }
    ]


@pytest.fixture
def review_payload():
    return {
        "merchant": {
            "name": "La Cabaña",
            "address": "738 Rose Ave",
            "city": "Venice",
            "country": "USA",
            "google_rating": 4.5,
            "google_rating_count": 929,
            "place_id": "ChIJc2JTRcO6woARZYR4EjVcAYs"
        },
        "dishes": [
        {"name": "Dos Tacos (Brunch)", "price": 18.00, "dish_rating": 5, "dish_note": "Best tacos ever"},
        {"name": "Lime Margarita", "price": 12.75, "dish_rating": 4, "dish_note": "Strong but tasty"}
        ],
        "my_rating": 5,
        "my_note": "Authentic vibe, great food",
        "total": 57.71,
        "participant_count": 1,
        "currency": "USD",
        "visit_date": "2026-06-30"
  }