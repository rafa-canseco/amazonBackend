import os

import requests
from dotenv import load_dotenv

from ..schemas.schemas import (
    Product,
    ProductDetail,
    ProductDetailResponse,
    ProductPrice,
    SearchResponse,
)

load_dotenv()

API_KEY: str = os.environ["API_KEY"]
API_URL: str = os.environ["API_URL"]


def search_products(query: str) -> SearchResponse:
    params = {
        "api_key": API_KEY,
        "engine": "amazon_search",
        "q": query,
        "amazon_domain": "amazon.com.mx",
    }

    response = requests.get(API_URL, params=params)
    response.raise_for_status()

    data = response.json()

    products = []
    shopping_results = data.get("shopping_results", [])
    if not shopping_results and "organic_results" in data:
        shopping_results = data["organic_results"]

    for item in shopping_results:
        product = Product(
            asin=item.get("asin", ""),
            title=item.get("title", ""),
            price=ProductPrice(
                value=float(
                    item.get("price", {}).get("value", 0)
                    if isinstance(item.get("price"), dict)
                    else 0
                ),
                currency=(
                    item.get("price", {}).get("currency", "")
                    if isinstance(item.get("price"), dict)
                    else ""
                ),
                raw=(
                    item.get("price", {}).get("raw", "")
                    if isinstance(item.get("price"), dict)
                    else str(item.get("price", ""))
                ),
            ),
            image=item.get("thumbnail", ""),
            rating=item.get("rating", None),
            ratings_total=item.get("ratings_total", None),
            link=item.get("link", ""),
            brand=item.get("brand", None),
            position=item.get("position", None),
            is_sponsored=item.get("is_sponsored", None),
            is_prime=item.get("is_prime", None),
            fulfillment=item.get("fulfillment", None),
        )
        products.append(product)

    return SearchResponse(products=products)


def get_product_details(asin: str) -> ProductDetailResponse:
    params = {
        "api_key": API_KEY,
        "engine": "amazon_product",
        "asin": asin,
        "amazon_domain": "amazon.com.mx",
    }

    response = requests.get(API_URL, params=params)
    response.raise_for_status()

    data = response.json()
    product_data = data.get("product", {})

    product_detail = ProductDetail(
        asin=product_data.get("asin", ""),
        title=product_data.get("title", ""),
        description=product_data.get("description", ""),
        feature_bullets=product_data.get("feature_bullets", []),
        variants=[
            {
                "asin": v.get("asin", ""),
                "title": v.get("title", ""),
                "link": v.get("link", ""),
                "dimensions": v.get("dimensions", []),
                "main_image": v.get("main_image", ""),
                "images": v.get("images", []),
            }
            for v in product_data.get("variants", [])
        ],
        attributes={
            attr["name"]: attr["value"] for attr in product_data.get("attributes", [])
        },
        images=[img.get("link", "") for img in product_data.get("images", [])],
        price=(
            ProductPrice(
                value=float(
                    product_data.get("buybox", {}).get("price", {}).get("value", 0)
                ),
                currency=product_data.get("buybox", {})
                .get("price", {})
                .get("currency", ""),
                raw=product_data.get("buybox", {}).get("price", {}).get("raw", ""),
            )
            if product_data.get("buybox", {}).get("price")
            else None
        ),
        rating=product_data.get("rating", None),
        ratings_total=product_data.get("reviews", None),
        reviews=[],
        link=product_data.get("link", ""),
        brand=(
            product_data.get("brand_store", {}).get("text", "")
            if product_data.get("brand_store")
            else ""
        ),
        availability={"status": product_data.get("buybox", {}).get("availability", "")},
    )

    return ProductDetailResponse(product=product_detail)
