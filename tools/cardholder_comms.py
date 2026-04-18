from typing import Optional
from datetime import datetime, timedelta

def get_correspondence(customer_email: str) -> Optional[dict]:
    """Get all merchant-cardholder communication history."""
    return {
        "customer_email": customer_email,
        "total_messages": 2,
        "cancellation_request_found": False,
        "complaint_received": False,
        "messages": [
            {
                "date": (datetime.now() - timedelta(days=14)).isoformat(),
                "direction": "outbound",
                "subject": "Your order has shipped",
                "body": "Tracking: TRACK-001-IN. Expected delivery in 3-5 days.",
            },
            {
                "date": (datetime.now() - timedelta(days=10)).isoformat(),
                "direction": "outbound",
                "subject": "Order delivered",
                "body": "Your order has been delivered. Enjoy your purchase!",
            },
        ],
    }
