''' 
curl -X POST http://localhost:7071/api/parse_receipt \
  -H "Content-Type: application/octet-stream" \
  --data-binary @receipt_sample.png
'''

'''
curl -X POST http://localhost:7071/api/save_review \
  -H "Content-Type: application/json" \
  -d '{
    "merchant": {
      "name": "La Cabaña",
      "address": "738 Rose Ave",
      "city": "Venice",
      "country": "USA",
      "rating": 4.5,"rating_count":929,
      "place_id": "ChIJc2JTRcO6woARZYR4EjVcAYs"
    },
    "dishes": [
      {"name": "Dos Tacos (Brunch)", "price": 18.00, "rating": 5, "notes": "Best tacos ever"},
      {"name": "Lime Margarita", "price": 12.75, "rating": 4, "notes": "Strong but tasty"}
    ],
    "my_rating": 4,
    "my_note": "Authentic vibe, great food", 
    "total": 57.71,
    "participant_count":1,
    "currency": "USD",
    "visit_date": "2024-03-10"
  }'
'''

'''
curl "http://localhost:7071/api/get_summary?from=2026-06-01&to=2026-06-30"
'''


from datetime import datetime, timezone
import json
import logging
import os
import re
import requests
import uuid

import azure.functions as func
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient, exceptions
from azure.servicebus import ServiceBusClient, ServiceBusMessage

app = func.FunctionApp()

# Document intelligence
di_client = None

def get_di_client():
    global di_client
    if di_client is None:
        di_client = DocumentIntelligenceClient(
            os.environ["DOC_INTELLIGENCE_ENDPOINT"],
            AzureKeyCredential(os.environ["DOC_INTELLIGENCE_KEY"])
        )
    return di_client

# DB
cosmos_container = None

def get_container():
    global cosmos_container
    if cosmos_container is None:
        client = CosmosClient(
            os.environ["COSMOS_ENDPOINT"],
            credential=os.environ["COSMOS_KEY"]
        )
        db = client.get_database_client(os.environ["COSMOS_DATABASE"])
        cosmos_container = db.get_container_client(os.environ["COSMOS_CONTAINER"])
    return cosmos_container

# Event bus
sb_client = None

def get_sb_client():
    global sb_client
    if sb_client is None:
        sb_client = ServiceBusClient.from_connection_string(
            os.environ["SERVICE_BUS_CONNECTION"]
        )
    return sb_client

sb_queue = os.environ["SERVICE_BUS_QUEUE"]

@app.route(route="parse_receipt", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def parse_receipt(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('======================== parse_receipt ========================')

    # get receipt image from request
    try:
        receipt_req = req.get_body()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid request"}),
            status_code=400,
            mimetype="application/json"
        )
    
    # get oct result of receipt from model
    try:
        di_resp = get_di_client().begin_analyze_document(
            model_id="prebuilt-receipt",
            body=receipt_req,
            content_type="application/octet-stream"
        )
        oct_receipt = di_resp.result()
    except Exception as e:
        logging.error(f"document intelligence error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to parse receipt", "detail": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
    
    # process oct to json result
    parsed_receipt = extract_receipt_info(oct_receipt)

    return func.HttpResponse(
        json.dumps(parsed_receipt),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="save_review", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def save_review(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("======================== save_review ========================")
    # get review from request
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid request"}),
            status_code=400,
            mimetype="application/json"
        )
    
    merchant = req_body.get("merchant")
    dishes = req_body.get("dishes")
    my_rating = req_body.get("my_rating")

    if not merchant or not merchant.get("name"):
        return func.HttpResponse(
            json.dumps({"error": "merchant.name is required"}),
            status_code=400,
            mimetype="application/json"
        )
    if not my_rating:
        return func.HttpResponse(
            json.dumps({"error": "my_rating is required"}),
            status_code=400,
            mimetype="application/json"
        )
    
    # construct db item
    review = {
        "id": str(uuid.uuid4()),
        "city": merchant.get("city"),
        "merchant": {
            "name": merchant.get("name"),
            "address": merchant.get("address"),
            "city": merchant.get("city", "Unknown"),
            "country": merchant.get("country", "Unknown"),
            "google_rating": merchant.get("google_rating"),
            "google_rating_count": merchant.get("google_rating_count"),
            "place_id": merchant.get("place_id")
        },
        "dishes": [
            {
                "name": d.get("name"),
                "price": d.get("price", 0),
                "dish_rating": d.get("dish_rating"),
                "dish_note": d.get("dish_note", "")
            }
            for d in dishes
        ],
        "my_rating": my_rating,
        "my_note": req_body.get("my_note", ""),
        "participant_count": req_body.get("participant_count", 1),
        "total": req_body.get("total", 0),
        "currency": req_body.get("currency", "EUR"),
        "visit_date": req_body.get("visit_date", datetime.now(timezone.utc).date().isoformat()),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # insert to db
    try:
        get_container().create_item(body=review)
    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Cosmos DB error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to save review", "message": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
    
    # sync new item to notion
    emit_event(review)

    return func.HttpResponse(
        json.dumps({"status": "success", "id": review["id"]}),
        status_code=201,
        mimetype="application/json"
    )


@app.route(route="get_summary", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def get_summary(req: func.HttpRequest) -> func.HttpResponse:
    # TODO: pagenation
    logging.info("======================== get_summary ========================")
    
    country_filter = req.params.get("country")
    city_filter = req.params.get("city")

    from_date = req.params.get("from") 
    to_date = req.params.get("to") 
    
    try:
        query = "SELECT * FROM reviews r "
        params = [{}]
        if city_filter:
            query += "WHERE r.city = @city"
            params = [{"name": "@city", "value": city_filter}]
        if country_filter:
            query += "WHERE r.merchant.country = @country"
            params = [{"name": "@country", "value": country_filter}]
        if from_date and to_date:
            query += "WHERE r.visit_date >= @from_date AND r.visit_date < @to_date"
            params = [{"name": "@from_date", "value": from_date}, {"name": "@to_date", "value": to_date}]
        
        if city_filter:
            items = list(get_container().query_items(
                query=query,
                parameters=params,
                partition_key=city_filter
            ))
        else:
            items = list(get_container().query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))

    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Cosmos DB query error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Fail to query reviews", "message": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
    
    if not items:
        return func.HttpResponse(
            json.dumps({
                "filters": {"country": country_filter, "city": city_filter, "from": from_date, "to": to_date},
                "total_reviews": 0,
                "countries": [],
                "message": f"No records found for"
            }),
            status_code=200,
            mimetype="application/json"
        )
    
    summary = group_items(items)
    summary["filters"] = {"country": country_filter, "city": city_filter, "from": from_date, "to": to_date}
    summary["total_reviews"] = len(items)

    return func.HttpResponse(
        json.dumps(summary),
        status_code=200,
        mimetype="application/json"
    )

@app.service_bus_queue_trigger(arg_name="msg", queue_name="sync-review-to-notion-event", connection="SERVICE_BUS_CONNECTION")
def notion_sync(msg: func.ServiceBusMessage):
    logging.info("======================== notion_sync ========================")

    try:
        body = msg.get_body()
        review = json.loads(body)
    except Exception as e:
        # service bus will retry later
        logging.error(f"Invalid event payload: {e}")
        return
    
    merchant = review["merchant"]
    dishes = review["dishes"]
    rated_dishes = [d for d in dishes if d.get("dish_rating")]
    best_dish = max(rated_dishes, key=lambda d: d["dish_rating"]) if rated_dishes else None
    best_dish_text = (
        f"{best_dish["name"]} ({best_dish["dish_rating"]}⭐)"
        if best_dish else ""
    )

    notion_payload = {
        "parent": {"database_id": os.environ["NOTION_DATABASE_ID"]},
        "properties": {
            "Merchant": {
                "title": [{"text": {"content": merchant.get("name", "Unknown")}}]
            },
            "City": {
                "rich_text": [{"text": {"content": merchant.get("city", "Unknown")}}]
            },
            "Country": {
                "rich_text": [{"text": {"content": merchant.get("country", "Unknown")}}]
            },
            "My Rating": {
                "number": review.get("my_rating")
            },
            "My Note": {
                "rich_text": [{"text": {"content": merchant.get("my_note", "")}}]
            },
            "Best Dish": {
                "rich_text": [{"text": {"content": best_dish_text}}]
            },
            "Total Cost": {
                "number": review.get("total", 0)
            },
            "Visit Date": {
                "date": {"start": review.get("visit_date")}
            },
        }
    }

    api_token = os.environ["NOTION_TOKEN"]
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(url=url, json=notion_payload, headers=headers, timeout=10)
        resp.raise_for_status()
        logging.info(f"Sync review {review['id']} to Notion")
    except Exception as e:
        logging.error(f"Fail to sync review to Notion: {e}")
        logging.error(f"Notion response body: {resp.text}")
        logging.error(f"Notion payload: {json.dumps(notion_payload)}")
        # service bus will retry later
        raise


def extract_receipt_info(oct_result) -> dict:
    if not oct_result.documents:
        return {"merchant": {}, "dishes": [], "total": 0}
    
    doc = oct_result.documents[0]
    fields = doc.fields
    logging.info(f"=============== di resp: {fields}")
    merchant_name = get_field_value(fields.get("MerchantName"))
    total = get_field_value(fields.get("Total"))
    currency = get_field_value(fields.get("CurrencyCode")) or "EUR"
    city = get_field_value(fields.get("MerchantAddress"))
    country = get_field_value(fields.get("CountryRegion"))
    visit_date = get_field_value(fields.get("TransactionDate"))
    dishes = []
    items = fields.get("Items")
    if items and items.value_array:
        for item in items.value_array:
            item_field = item.value_object or {}
            dish_name = get_field_value(item_field.get("Description"))
            dish_price = get_field_value(item_field.get("TotalPrice"))
            if dish_name:
                correct_dish_name, extracted_dish_price = correct_dish_info(dish_name)
                if extracted_dish_price and not dish_price:
                    dish_name = correct_dish_name
                    dish_price = extracted_dish_price
                
                dishes.append({
                    "name": dish_name,
                    "price": dish_price or 0
                })

    google_place_info = get_google_places(merchant_name, city)
    logging.info(f"=============== google resp: {google_place_info}")

    return {
        "merchant": {
            "name": merchant_name or "Unknown",
            "city": city or google_place_info["city"],       
            "country": country or google_place_info["country"],
            "address": google_place_info["address"],
            "place_id": google_place_info["place_id"],
            "google_rating": google_place_info["google_rating"],
            "google_rating_count": google_place_info["google_rating_count"]
        },
        "dishes": dishes,
        "total": total or 0,
        "currency": currency,
        "visit_date": visit_date
    }

def get_field_value(field):
    if field is None:
        return None
    
    if hasattr(field, "value_string") and field.value_string:
        return field.value_string
    
    if hasattr(field, "value_number") and field.value_number is not None:
        return field.value_number
    
    if hasattr(field, "value_currency") and field.value_currency:
        return field.value_currency.amount
    
    if hasattr(field, "value_date") and field.value_date:
        return str(field.value_date)
    
    if hasattr(field, "value_address") and field.value_address:
        return str(field.value_address.city)
    
    if hasattr(field, "value_country_region") and field.value_country_region:
        return str(field.value_country_region)
    
    if hasattr(field, "content") and field.content:
        return field.content
    
    return None


def correct_dish_info(name: str) -> tuple[str, float | None]:
    if not name:
        return name, None
    
    # match trailing number like "21.95" or "21,95"
    match = re.search(r"(\d+[.,]\d{2})$", name.strip())
    if match:
        price = float(match.group(1).replace(",", "."))
        correct_name = name[:match.start()].strip()
        return correct_name, price
    
    return name.strip(), None

def get_google_places(merchant_name: str, city: str) -> dict:
    fallback = {
        "city": "Unknown",
        "country": "Unknown",
        "address": None,
        "place_id": None,
        "google_rating": None,
        "google_rating_count": None
    }

    if not merchant_name:
        return fallback
    
    try:
        api_key = os.environ["GOOGLE_PLACES_KEY"]
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.formattedAddress,places.addressComponents,places.id,places.rating,places.userRatingCount"
        }
        query = f"{merchant_name} {city}" if city else merchant_name
        body = {"textQuery": query}
        response = requests.post(url, json=body, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("places"):
            logging.warning("%s not found in Google Places", {merchant_name})
            return fallback
        
        place = data.get("places")[0]
        g_city = "Unknown"
        country = "Unknown"
        for component in place.get("addressComponents", []):
            types = component.get("types", [])
            if "locality" in types:
                g_city = component.get("longText", "Unknown")
            if "country" in types:
                country = component.get("longText", "Unknown")

        return {
            "city": g_city,
            "country": country,
            "address": place.get("formattedAddress"),
            "place_id": place.get("id"),
            "google_rating": place.get("rating"),
            "google_rating_count": place.get("userRatingCount"),
        }
    
    except Exception as e:
        logging.error(f"Fail to get Google Places result: {e}")
        return fallback

def emit_event(review: dict):
    try:
        with get_sb_client().get_queue_sender(sb_queue) as sender:
            message = ServiceBusMessage(json.dumps(review))
            sender.send_messages(message)
        logging.info(f"Emit event for review {review['id']}")
    except Exception as e:
        logging.error(f"Fail to emit event: {e}")


def group_items(reviews: list) -> dict:
    # append multiple records for the same merchant
    merchants_aggregated = {}
    for review in reviews:
        merchant = review["merchant"]
        key = (
            merchant.get("country", "Unknown"),
            merchant.get("city", "Unknown"),
            merchant.get("place_id") or merchant["name"]
        )
        if key not in merchants_aggregated:
            merchants_aggregated[key] = {
                "name": merchant["name"],
                "city": merchant.get("city"),
                "country": merchant.get("country"),
                "address": merchant.get("address"),
                "google_rating": merchant.get("google_rating"),
                "google_rating_count": merchant.get("google_rating_count"),
                "place_id": merchant.get("place_id"),
                "my_ratings": [],
                "my_notes": [],
                "dishes": [],
                "participant_count": 0,
                "total": 0,
                "visit_dates": [],
                "currency": review.get("currency", "EUR"),
                "visit_count": 0
            }
        
        review_aggregated = merchants_aggregated[key]
        review_aggregated["my_ratings"].append(review["my_rating"])
        if review.get("my_note"):
            review_aggregated["my_notes"].append(review["my_note"])
        review_aggregated["dishes"].extend(review["dishes"])
        review_aggregated["participant_count"] += review.get("participant_count", 0)
        review_aggregated["total"] += review.get("total", 0)
        if review.get("visit_date"):
            review_aggregated["visit_dates"].append(review["visit_date"])
        review_aggregated["visit_count"] += 1

    # merge multiple reviews to one dict for the same merchant
    merchants_merged = []
    for review_aggregated in merchants_aggregated.values():
        avg_my_rating = int(round(sum(review_aggregated["my_ratings"]) / len(review_aggregated["my_ratings"]), 0))
        if review_aggregated["participant_count"] > 0:
            cost_per_person = round(review_aggregated["total"] / review_aggregated["participant_count"], 2)
        else:
            cost_per_person = review_aggregated["total"]

        merchants_merged.append({
            "name": review_aggregated["name"],
            "city": review_aggregated["city"],
            "country": review_aggregated["country"],
            "address": review_aggregated["address"],
            "google_rating": review_aggregated["google_rating"],
            "google_rating_count": review_aggregated["google_rating_count"],
            "place_id": review_aggregated["place_id"],
            "my_rating": avg_my_rating,
            "my_note": review_aggregated["my_notes"][-1] if review_aggregated["my_notes"] else None,
            "dishes": review_aggregated["dishes"],
            "cost_total": review_aggregated["total"],
            "cost_per_person": cost_per_person,
            "latest_visit_date": max(review_aggregated["visit_dates"]) if review_aggregated["visit_dates"] else None,
            "currency": review_aggregated["currency"],
            "visit_count": review_aggregated["visit_count"],
        })

    merchants_grouped = {}
    # group reviews by country / city
    # {
    #   "USA": {
    #       "Venice": [review1, review2, ...]
    #   }
    # }
    for review_merged in merchants_merged:
        country = review_merged["country"]
        city = review_merged["city"]
        merchants_grouped.setdefault(country, {}).setdefault(city, []).append(review_merged)

    # Sort merchants within each city by my_rating desc
    for country in merchants_grouped:
        for city in merchants_grouped[country]:
            merchants_grouped[country][city].sort(key=lambda x: x["my_rating"], reverse=True)
    
    # final output to frontend 
    # (use list rather than dict to preserve order; use countries and cities for better handle data in frontend)
    # {
    #   "countries": [
    #       {
    #           "country": "USA",
    #           "cities": [
    #               {"city": "Venice", "merchants": [review1, review2, ...]}
    #           ]
    #       }
    #   ]
    # }
    countries = []
    for country in sorted(merchants_grouped.keys()):
        cities = []
        for city in sorted(merchants_grouped[country].keys()):
            cities.append({
                "city": city,
                "merchants": merchants_grouped[country][city]
            })
        countries.append({
            "country": country,
            "cities": cities
        })

    return {"countries": countries}