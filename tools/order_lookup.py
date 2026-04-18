from typing import Optional
from datetime import datetime, timedelta
import random

def get_order(transaction_id: str) -> Optional[dict]:
    """Fetch order details for a transaction."""
    return {
        "transaction_id": transaction_id,
        "order_id": f"ORD-{transaction_id[-6:]}",
        "merchant_id": "MERCH-001",
        "merchant_name": "TechStore India",
        "customer_email": "customer@example.com",
        "amount": 1250.00,
        "currency": "USD",
        "order_date": (datetime.now() - timedelta(days=15)).isoformat(),
        "product": "Wireless Headphones",
        "status": "delivered",
        "terms_accepted": True,
        "terms_accepted_at": (datetime.now() - timedelta(days=15)).isoformat(),
    }
