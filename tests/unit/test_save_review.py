import json
from unittest.mock import patch, MagicMock
import azure.functions as func
import pytest

from function_app import save_review


class TestSaveReview:
    
    @pytest.mark.unit
    def test_save_review_valid(self, review_payload):
        req = func.HttpRequest(
            method="POST",
            url="http://localhost/api/save_review",
            body=json.dumps(review_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        with patch("function_app.get_container") as mock_get_container, \
             patch("function_app.emit_event") as mock_emit:
            
            mock_container = MagicMock()
            mock_get_container.return_value = mock_container
            response = save_review(req)
        
        assert response.status_code == 201
        body = json.loads(response.get_body())
        assert body["status"] == "success"
        assert "id" in body
        
        mock_container.create_item.assert_called_once()
        saved_doc = mock_container.create_item.call_args.kwargs.get("body") \
                    or mock_container.create_item.call_args.args[0]
        assert saved_doc["merchant"]["name"] == "La Cabaña"
        assert saved_doc["city"] == "Venice"
        assert saved_doc["my_rating"] == 5
        
        mock_emit.assert_called_once()