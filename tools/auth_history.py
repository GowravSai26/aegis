from typing import Optional
from datetime import datetime, timedelta

def get_auth_status(transaction_id: str) -> Optional[dict]:
    """Get 3DS authentication status for transaction."""
    return {
        "transaction_id": transaction_id,
        "three_ds_attempted": True,
        "three_ds_completed": True,
        "three_ds_version": "2.2",
        "eci_code": "05",            # 05 = fully authenticated
        "auth_timestamp": (datetime.now() - timedelta(days=15)).isoformat(),
        "liability_shift": True,     # liability shifts to issuer on 3DS success
        "approval_code": "AUTH-789XYZ",
    }
