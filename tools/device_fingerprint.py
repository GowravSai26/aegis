from typing import Optional
from datetime import datetime, timedelta

def get_device_data(transaction_id: str) -> Optional[dict]:
    """Get device and IP data at time of transaction."""
    return {
        "transaction_id": transaction_id,
        "ip_address": "49.36.102.45",
        "ip_country": "IN",
        "ip_city": "Hyderabad",
        "device_id": f"DEV-{transaction_id[-8:]}",
        "device_type": "mobile",
        "os": "Android 14",
        "browser": "Chrome 124",
        "device_match": True,        # matches cardholder's registered device
        "prior_purchases": 4,        # times this device bought from merchant
        "transaction_time": (datetime.now() - timedelta(days=15)).isoformat(),
    }
