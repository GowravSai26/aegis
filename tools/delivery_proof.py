from typing import Optional
from datetime import datetime, timedelta

def get_delivery_proof(order_id: str) -> Optional[dict]:
    """Get delivery confirmation and tracking info."""
    return {
        "order_id": order_id,
        "tracking_number": f"TRACK-{order_id[-6:]}-IN",
        "carrier": "BlueDart",
        "status": "delivered",
        "delivered_at": (datetime.now() - timedelta(days=10)).isoformat(),
        "delivery_confirmed": True,
        "customer_signed": True,
        "signature_name": "R. Kumar",
        "delivery_address": "123 MG Road, Hyderabad, TS 500001",
        "proof_url": f"https://bluedart.com/proof/{order_id}",
    }
