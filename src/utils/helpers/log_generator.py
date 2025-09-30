from typing import Optional
from src.utils.libs.logging import logging
from datetime import datetime, timezone

def generate_order_error(
    error_code: str,
    order_id: str,
    platform: str,
    item_id: Optional[str] = None,
    warehouse: Optional[str] = None,
    delivery_time: Optional[datetime] = None,
) -> None:
    """Generate a structured order error response based on error code and metadata."""
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    messages = {
        "ERR_MISSING_ADDRESS": "Missing or incomplete delivery address",
        "ERR_INVALID_SKU": f"Product '{item_id}' not found in ERP catalog" if item_id else "Product not found in ERP catalog",
        "ERR_OOS_ITEM": f"Item '{item_id}' is out of stock at {warehouse}" if item_id and warehouse else "Item out of stock in selected micro-warehouse",
        "ERR_PRICE_MISMATCH": f"Price mismatch for item '{item_id}'" if item_id else "Item price differs from ERP catalog price",
        "ERR_NO_LINE_ITEMS": "No products found in order",
        "ERR_DUPLICATE_ORDER": f"Duplicate order: {order_id}",
        "ERR_INVALID_DATETIME": f"Delivery time {delivery_time} is outside operating hours" if delivery_time else "Delivery time outside operating hours",
        "ERR_BAD_JSON": "Payload structure invalid or malformed",
        "ERR_PLATFORM_METADATA": "Required platform metadata missing",
        "ERR_UNSUPPORTED_ITEM": f"Item '{item_id}' category not supported" if item_id else "Item category not supported",
    }

    if error_code not in messages:
        raise ValueError(f"Unknown error code: {error_code}")

    log = {
        "error_code": error_code,
        "message": messages[error_code],
        "order_id": order_id,
        "platform": platform,
        "timestamp": timestamp,
    }

    logging.error(f"Error Log {log}")