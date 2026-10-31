"""
Thin PayPal Orders API (v2) client for the sandbox.

Only what the demo needs: get an access token, create an order, capture an
order. If credentials are missing/placeholder, the app runs in MOCK mode
(see app.py) and this client is not called -- so the whole UI is testable
before you have sandbox keys.
"""

import os
import requests

SANDBOX_BASE = "https://api-m.sandbox.paypal.com"
LIVE_BASE = "https://api-m.paypal.com"


def _base() -> str:
    return LIVE_BASE if os.getenv("PAYPAL_ENV", "sandbox") == "live" else SANDBOX_BASE


def _creds():
    return os.getenv("PAYPAL_CLIENT_ID", ""), os.getenv("PAYPAL_CLIENT_SECRET", "")


def credentials_present() -> bool:
    cid, secret = _creds()
    if not cid or not secret:
        return False
    # treat the shipped placeholder as "not set"
    return "your_sandbox" not in cid and "your_sandbox" not in secret


def get_access_token() -> str:
    cid, secret = _creds()
    resp = requests.post(
        f"{_base()}/v1/oauth2/token",
        auth=(cid, secret),
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_order(amount: float, currency: str = "USD") -> dict:
    token = get_access_token()
    resp = requests.post(
        f"{_base()}/v2/checkout/orders",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json={
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {"currency_code": currency, "value": f"{amount:.2f}"}
            }],
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def capture_order(order_id: str) -> dict:
    token = get_access_token()
    resp = requests.post(
        f"{_base()}/v2/checkout/orders/{order_id}/capture",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()
