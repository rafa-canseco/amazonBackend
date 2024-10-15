import logging
import os
from typing import List, Optional

import httpx
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from telegram import Bot
from telegram.error import TelegramError

from amazon.amazon_api import get_product_details, search_products
from database.supabase_client import supabase
from schemas.schemas import (
    Cart,
    CartItem,
    CreateOrderRequest,
    Order,
    OrderItem,
    ProductDetailRequest,
    ProductDetailResponse,
    SearchRequest,
    SearchResponse,
    UpdateOrderStatusRequest,
    UserData,
)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ADMIN_WALLET_ADDRESS = os.getenv("ADMIN_WALLET_ADDRESS")
ADMIN_PRIVY_ID = os.getenv("ADMIN_PRIVY_ID")
BMX_TOKEN = os.getenv("BMX_TOKEN")

app = FastAPI()

security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting application")


@app.get("/")
def read_root():
    logger.info("Received request for root endpoint")
    return {"hello": "world"}


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, options={"verify_signature": False}
        )
        privy_id = payload.get("sub")
        wallet_address = payload.get(
            "wallet_address"
        )  # Asumiendo que Privy incluye la dirección del wallet en el token

        if privy_id is None and wallet_address is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # Verificar si el usuario es un administrador
        if privy_id != ADMIN_PRIVY_ID and wallet_address != ADMIN_WALLET_ADDRESS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
            )

        return privy_id or wallet_address
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def send_telegram_notification(message: str):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except TelegramError as e:
        print(f"Error sending Telegram notification: {e}")


@app.post("/api/searchProduct", response_model=SearchResponse)
async def search_product_endpoint(request: SearchRequest):
    try:
        return search_products(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/productDetails", response_model=ProductDetailResponse)
async def product_details_endpoint(request: ProductDetailRequest):
    try:
        return get_product_details(request.asin)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/check")
async def check_user_registration(privy_id: str, wallet_address: Optional[str] = None):
    try:
        response = (
            supabase.table("users").select("*").eq("privy_id", privy_id).execute()
        )
        is_registered = len(response.data) > 0
        return {"isRegistered": is_registered}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/user")
async def register_user(user_data: UserData):
    try:
        response = supabase.table("users").insert(user_data.dict()).execute()
        if len(response.data) > 0:
            return response.data[0]
        else:
            raise HTTPException(status_code=400, detail="Failed to register user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cart/{user_id}", response_model=Cart)
async def get_cart(user_id: str):
    try:
        response = (
            supabase.table("cart_items").select("*").eq("user_id", user_id).execute()
        )
        return Cart(items=response.data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cart/{user_id}", response_model=Cart)
async def add_to_cart(user_id: str, item: CartItem):
    try:
        response = (
            supabase.table("cart_items")
            .insert(
                {
                    "user_id": user_id,
                    "asin": item.asin,
                    "quantity": item.quantity,
                    "title": item.title,
                    "price": item.price,
                    "image_url": item.image_url,
                }
            )
            .execute()
        )

        if not response.data:
            supabase.table("cart_items").update(
                {"quantity": supabase.raw(f"quantity + {item.quantity}")}
            ).eq("user_id", user_id).eq("asin", item.asin).execute()

        return await get_cart(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cart/{user_id}/{asin}", response_model=Cart)
async def remove_from_cart(user_id: str, asin: str):
    try:
        supabase.table("cart_items").delete().eq("user_id", user_id).eq(
            "asin", asin
        ).execute()
        return await get_cart(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/cart/{user_id}/{asin}", response_model=Cart)
async def update_cart_item_quantity(user_id: str, asin: str, quantity: int):
    try:
        if quantity > 0:
            supabase.table("cart_items").update({"quantity": quantity}).eq(
                "user_id", user_id
            ).eq("asin", asin).execute()
        else:
            await remove_from_cart(user_id, asin)
        return await get_cart(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/orders", response_model=Order)
async def create_order(order_details: CreateOrderRequest):
    try:
        # Insertar la orden principal
        order_response = (
            supabase.table("orders")
            .insert(
                {
                    "user_id": order_details.user_id,
                    "total_amount": order_details.total_amount,
                    "total_amount_usd": order_details.total_amount_usd,
                    "status": "order received",
                    "full_name": order_details.full_name,
                    "street": order_details.street,
                    "postal_code": order_details.postal_code,
                    "phone": order_details.phone,
                    "delivery_instructions": order_details.delivery_instructions,
                    "shipping_guide": None,
                    "blockchain_order_id": str(order_details.blockchain_order_id),
                }
            )
            .execute()
        )

        if not order_response.data:
            raise HTTPException(status_code=500, detail="Failed to create order")

        order_id = order_response.data[0]["id"]

        order_items = [
            {
                "order_id": order_id,
                "asin": item.asin,
                "quantity": item.quantity,
                "price": item.price,
                "title": item.title,
                "image_url": item.image_url,
            }
            for item in order_details.items
        ]

        supabase.table("order_items").insert(order_items).execute()

        # Borrar el carrito del usuario
        supabase.table("cart_items").delete().eq(
            "user_id", order_details.user_id
        ).execute()

        notification_message = f"""
        Nueva orden creada:
        ID: {order_id}
        Usuario: {order_details.user_id}
        Monto total: {order_details.total_amount}
        Monto total USD: {order_details.total_amount_usd}
        """
        await send_telegram_notification(notification_message)

        order_data = (
            supabase.table("orders")
            .select("*, order_items(*)")
            .eq("id", order_id)
            .single()
            .execute()
        )

        if not order_data.data:
            raise HTTPException(
                status_code=404, detail="Order not found after creation"
            )

        return Order(
            id=order_data.data["id"],
            user_id=order_data.data["user_id"],
            total_amount=float(order_data.data["total_amount"]),
            total_amount_usd=(
                float(order_data.data["total_amount_usd"])
                if order_data.data["total_amount_usd"] is not None
                else None
            ),
            status=order_data.data["status"],
            created_at=order_data.data["created_at"],
            items=[OrderItem(**item) for item in order_data.data["order_items"]],
            full_name=order_data.data["full_name"],
            street=order_data.data["street"],
            postal_code=order_data.data["postal_code"],
            phone=order_data.data["phone"],
            delivery_instructions=order_data.data["delivery_instructions"],
            shipping_guide=order_data.data.get("shipping_guide"),
            blockchain_order_id=order_data.data["blockchain_order_id"],
        )
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        print(f"Order details: {order_details}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@app.get("/api/orders/{user_id}", response_model=List[Order])
async def get_user_orders(user_id: str):
    try:
        # Obtener todas las órdenes del usuario con sus items en una sola consulta
        orders_data = (
            supabase.table("orders")
            .select("*, order_items(*)")
            .eq("user_id", user_id)
            .execute()
        )

        orders = []
        for order_data in orders_data.data:
            order_items = [
                OrderItem(
                    asin=item["asin"],
                    quantity=item["quantity"],
                    price=item["price"],
                    title=item["title"],
                    image_url=item.get("image_url"),
                )
                for item in order_data["order_items"]
            ]

            shipping_guide = order_data.get("shipping_guide")
            if shipping_guide is None:
                shipping_guide = "Generando orden de envío"

            order = Order(
                id=order_data["id"],
                user_id=order_data["user_id"],
                total_amount=order_data["total_amount"],
                total_amount_usd=order_data["total_amount_usd"],
                status=order_data["status"],
                created_at=order_data["created_at"],
                items=order_items,
                full_name=order_data["full_name"],
                street=order_data["street"],
                postal_code=order_data["postal_code"],
                phone=order_data["phone"],
                delivery_instructions=order_data["delivery_instructions"],
                shipping_guide=shipping_guide,
            )
            orders.append(order)

        return orders
    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/orders", response_model=List[Order])
async def get_all_orders(admin_id: str = Depends(verify_admin_token)):
    try:
        # Obtener todas las órdenes con sus items en una sola consulta
        orders_data = supabase.table("orders").select("*, order_items(*)").execute()

        orders = []
        for order_data in orders_data.data:
            order_items = [
                OrderItem(
                    asin=item["asin"],
                    quantity=item["quantity"],
                    price=item["price"],
                    title=item["title"],
                    image_url=item.get("image_url"),
                )
                for item in order_data["order_items"]
            ]

            order = Order(
                id=order_data["id"],
                user_id=order_data["user_id"],
                total_amount=float(order_data["total_amount"]),
                total_amount_usd=(
                    float(order_data["total_amount_usd"])
                    if order_data["total_amount_usd"] is not None
                    else None
                ),
                status=order_data["status"],
                created_at=order_data["created_at"],
                items=order_items,
                full_name=order_data["full_name"],
                street=order_data["street"],
                postal_code=order_data["postal_code"],
                phone=order_data["phone"],
                delivery_instructions=order_data["delivery_instructions"],
                shipping_guide=order_data.get(
                    "shipping_guide", "Generando orden de envío"
                ),
                blockchain_order_id=order_data.get("blockchain_order_id"),
            )
            orders.append(order)

        return orders
    except Exception as e:
        print(f"Error fetching all orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orders_admin/{order_id}", response_model=Order)
async def get_order_by_id(order_id: str, admin_id: str = Depends(verify_admin_token)):
    try:
        order_data = (
            supabase.table("orders")
            .select("*, order_items(*)")
            .eq("id", order_id)
            .single()
            .execute()
        )

        if not order_data.data:
            raise HTTPException(status_code=404, detail="Order not found")

        order_items = [
            OrderItem(
                asin=item["asin"],
                quantity=item["quantity"],
                price=item["price"],
                title=item["title"],
                image_url=item.get("image_url"),
            )
            for item in order_data.data["order_items"]
        ]
        shipping_guide = order_data.data.get("shipping_guide")
        if shipping_guide is None:
            shipping_guide = "Generando orden de envío"

        order = Order(
            id=order_data.data["id"],
            user_id=order_data.data["user_id"],
            total_amount=float(order_data.data["total_amount"]),
            total_amount_usd=(
                float(order_data.data["total_amount_usd"])
                if order_data.data["total_amount_usd"] is not None
                else None
            ),
            status=order_data.data["status"],
            created_at=order_data.data["created_at"],
            items=order_items,
            full_name=order_data.data["full_name"],
            street=order_data.data["street"],
            postal_code=order_data.data["postal_code"],
            phone=order_data.data["phone"],
            delivery_instructions=order_data.data["delivery_instructions"],
            shipping_guide=shipping_guide,
            blockchain_order_id=order_data.data.get("blockchain_order_id"),
        )
        return order
    except Exception as e:
        print(f"Error fetching order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    admin_id: str = Depends(verify_admin_token),
):
    try:
        response = (
            supabase.table("orders")
            .update({"status": "shipped", "shipping_guide": request.shippingGuide})
            .eq("id", order_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404, detail="Order not found or no update made"
            )

        return {"message": "Order status updated successfully"}

    except Exception as e:
        print(f"Error updating order status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/exchange-rate/latest")
async def get_latest_exchange_rate():
    try:
        url = (
            "https://www.banxico.org.mx/SieAPIRest/service/v1/"
            "series/SF43718/datos/oportuno"
        )

        headers = {
            "Accept": "application/json",
            "Bmx-Token": BMX_TOKEN,
            "Accept-Encoding": "gzip",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        data = response.json()

        latest_data = data.get("bmx", {}).get("series", [{}])[0]

        if not latest_data:
            raise HTTPException(
                status_code=404, detail="No data found for the given series."
            )

        idSerie = latest_data.get("idSerie")
        title = latest_data.get("titulo")
        datos = latest_data.get("datos", [])

        if not datos:
            raise HTTPException(
                status_code=404, detail="No data found for the given series."
            )

        latest_value = datos[0]
        date = latest_value.get("fecha")
        value = latest_value.get("dato")

        return {"idSerie": idSerie, "titulo": title, "fecha": date, "valor": value}

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Banxico API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
