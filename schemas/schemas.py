from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str


class ProductPrice(BaseModel):
    value: float
    currency: str
    raw: str


class Product(BaseModel):
    asin: str
    title: str
    price: ProductPrice
    image: str
    rating: Optional[float]
    ratings_total: Optional[int]
    link: str
    brand: Optional[str]
    position: Optional[int]
    is_sponsored: Optional[bool]
    is_prime: Optional[bool]
    fulfillment: Optional[dict]


class SearchResponse(BaseModel):
    products: List[Product]


class ProductDetailRequest(BaseModel):
    asin: str


class ProductDetail(BaseModel):
    asin: str
    title: str
    description: Optional[str]
    feature_bullets: Optional[List[str]]
    variants: Optional[List[Dict]]
    attributes: Optional[Dict]
    images: Optional[List[str]]
    price: Optional[ProductPrice]
    rating: Optional[float]
    ratings_total: Optional[int]
    reviews: Optional[List[Dict]]
    link: str
    brand: Optional[str]
    availability: Optional[Dict[str, str]] = None


class ProductDetailResponse(BaseModel):
    product: ProductDetail


class UserData(BaseModel):
    privy_id: str
    wallet_address: Optional[str] = None


class CartItem(BaseModel):
    asin: str
    quantity: int
    title: str
    price: float
    image_url: Optional[str] = None


class Cart(BaseModel):
    items: List[CartItem]


class OrderItem(BaseModel):
    asin: str
    quantity: int
    price: float
    title: str
    image_url: Optional[str] = None


class CreateOrderRequest(BaseModel):
    user_id: str
    items: List[OrderItem]
    total_amount: float
    total_amount_usd: float
    full_name: str
    street: str
    postal_code: str
    phone: str
    delivery_instructions: str
    blockchain_order_id: str


class Order(BaseModel):
    id: str
    user_id: str
    total_amount: float
    total_amount_usd: float
    status: str
    created_at: datetime
    items: List[OrderItem]
    full_name: str
    street: str
    postal_code: str
    phone: str
    delivery_instructions: str
    shipping_guide: Optional[str] = None
    blockchain_order_id: Optional[str] = None


class CreateOrderResponse(BaseModel):
    order: Order


class UpdateOrderStatusRequest(BaseModel):
    shippingGuide: str
