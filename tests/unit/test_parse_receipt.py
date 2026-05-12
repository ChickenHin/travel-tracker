import json
from unittest.mock import patch, MagicMock
import azure.functions as func
import pytest

from function_app import parse_receipt


def mock_di_result():
    def build_field(**values):
        defaults = {
            "value_string": None,
            "value_number": None,
            "value_currency": None,
            "value_date": None,
            "value_country_region": None,
            "value_address": None,
            "content": None,
        }
        defaults.update(values)
        return MagicMock(**defaults)
    
    merchant_name = build_field(
        value_string="La Cabaña",
        content="La Cabaña",
    )
    
    merchant_address = build_field(
        value_address=MagicMock(
            house_number="738",
            road="Rose Ave",
            postal_code="90291",
            city="Venice",
            state="CA",
            street_address="738 Rose Ave",
        ),
        content="738 Rose Ave, Venice, CA",
    )

    country_region = build_field(
        value_country_region="USA",
        content="USA",
    )
    
    total = build_field(
        value_currency=MagicMock(amount=57.71, currency_code="USD"),
        content="57.71",
    )
    
    currency_code = build_field(
        value_string="USD",
        content="USD",
    )
    
    def build_dish(description, price=None, quantity=1):
        fields = {
            "Description": build_field(value_string=description, content=description),
            "Quantity": build_field(value_number=quantity, content=str(quantity)),
        }
        if price is not None:
            fields["TotalPrice"] = build_field(
                value_currency=MagicMock(amount=price, currency_code="USD"),
                content=f"{price:.2f}",
            )
        return MagicMock(value_object=fields)
    
    items_field = MagicMock(value_array=[
        build_dish("Dos Tacos (Brunch)", 18.0),
        build_dish("Super Combo", 21.95),
        build_dish("Lime Margarita", 12.75),
    ])
    
    fields = {
        "MerchantName": merchant_name,
        "MerchantAddress": merchant_address,
        "CountryRegion": country_region,
        "Total": total,
        "CurrencyCode": currency_code,
        "Items": items_field,
    }
    
    doc = MagicMock(fields=fields)
    return MagicMock(documents=[doc])


def mock_google_places_result():
    response = MagicMock()
    response.json.return_value = {
        "places": [{
            "id": "ChIJc2JTRcO6woARZYR4EjVcAYs",
            "formattedAddress": "738 Rose Ave",
            "rating": 4.4,
            "userRatingCount": 929
        }]
    }
    response.raise_for_status = MagicMock()
    return response


class TestParseReceipt:
    @pytest.mark.unit
    def test_parse_receipt_valid(self, receipt_sample_bytes):
        req = func.HttpRequest(
            method="POST",
            url="http://localhost/api/parse_receipt",
            body=receipt_sample_bytes,
            headers={"Content-Type": "application/octet-stream"}
        )
        
        mock_poller = MagicMock()
        mock_poller.result.return_value = mock_di_result()
        
        with patch("function_app.get_di_client") as mock_get_di, \
             patch("function_app.requests.post") as mock_post:
            
            mock_get_di.return_value.begin_analyze_document.return_value = mock_poller
            mock_post.return_value = mock_google_places_result()
            response = parse_receipt(req)
        
        assert response.status_code == 200, response.get_body()
        
        body = json.loads(response.get_body())
        print(f"\nResponse body:\n{json.dumps(body, indent=2, ensure_ascii=False)}")

        assert body["merchant"]["name"] == "La Cabaña"
        assert body["merchant"]["city"] == "Venice"
        assert body["merchant"]["country"] == "USA"
        assert body["merchant"]["address"] == "738 Rose Ave"
        assert body["merchant"]["google_rating"] == 4.4
        assert body["merchant"]["google_rating_count"] == 929
        assert body["total"] == 57.71
        assert body["currency"] == "USD"
        assert len(body["dishes"]) == 3
        assert body["dishes"][0]["name"] == "Dos Tacos (Brunch)"
        assert body["dishes"][0]["price"] == 18.0