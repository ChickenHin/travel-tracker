import json
from unittest.mock import patch, MagicMock
import azure.functions as func
import pytest

from function_app import get_summary

def build_request(query: str = "") -> func.HttpRequest:
    base = "http://localhost/api/get_summary"
    url = f"{base}?{query}" if query else base
    return func.HttpRequest(
        method="GET",
        url=url,
        body=None,
        headers={}
    )

def mock_cosmos(items):
    mock_container = MagicMock()
    mock_container.query_items.return_value = items
    return patch("function_app.get_container", return_value=mock_container)

class TestGetSummary:
    @pytest.mark.unit
    def test_get_summary_without_params(self, cosmos_items):
        req = build_request({})
        
        with mock_cosmos(cosmos_items):
            response = get_summary(req)
        
        assert response.status_code == 200
        body = json.loads(response.get_body())
        
        country_names = [c["country"] for c in body["countries"]]
        assert "USA" in country_names
    
    @pytest.mark.unit
    def test_get_summary_filter_by_city(self, cosmos_items):
        req = build_request({"city=Venice"})
        
        venice_items = [r for r in cosmos_items if r["city"] == "Venice"]
        with mock_cosmos(venice_items):
            response = get_summary(req)
        
        assert response.status_code == 200
        body = json.loads(response.get_body())
        
        assert len(body["countries"]) == 1
        assert body["countries"][0]["country"] == "USA"
        
        cities = [c["city"] for c in body["countries"][0]["cities"]]
        assert cities == ["Venice"]
    
    @pytest.mark.unit
    def test_get_summary_filter_by_country(self, cosmos_items):
        req = build_request({"country=USA"})
        
        usa_items = [r for r in cosmos_items if r["merchant"]["country"] == "USA"]
        with mock_cosmos(usa_items):
            response = get_summary(req)
        
        assert response.status_code == 200
        body = json.loads(response.get_body())
        
        country_names = [c["country"] for c in body["countries"]]
        assert country_names == ["USA"]
    
    @pytest.mark.unit
    def test_filter_by_date_range(self, cosmos_items):
        req = build_request("from=2024-03-01&to=2024-04-01")
        
        march_items = [
            r for r in cosmos_items
            if "2024-03" in r["visit_date"]
        ]
        with mock_cosmos(march_items):
            response = get_summary(req)
        
        assert response.status_code == 200
        body = json.loads(response.get_body())

        print(f"========body: {body}")
        
        assert body["total_reviews"] == 1