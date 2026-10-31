"""
PayDrishti backend — FastAPI.

Puts the AI risk check at the chokepoint in PayPal's payment flow:

    create order  ->  [PayPal approval]  ->  RISK CHECK  ->  capture
                                               |
                                      high risk -> interstitial
                                      (user decides: cancel / pay anyway)

Runs in two modes, chosen automatically:
  - LIVE  : real PayPal sandbox Orders API (when .env has sandbox credentials)
  - MOCK  : no PayPal calls, fake order ids (so the UI + interstitial are
            fully testable before you have sandbox keys)

Run:  uvicorn app:app --reload --port 8000   (from the backend/ folder)
  or: python app.py
"""

import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import paypal_client as pp
from risk_engine import RiskEngine
from explainer import explain, active_provider

load_dotenv()

HERE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(HERE, "..", "frontend")

app = FastAPI(title="PayDrishti")
engine = RiskEngine()

MOCK = not pp.credentials_present()
CURRENCY = "USD"

# in-memory order store: order_id -> {payee_id, amount}
ORDERS: dict[str, dict] = {}


# ---------- request models ----------
class CreateOrderReq(BaseModel):
    payee_id: str
    amount: float
    payee_label: str = "this payee"


class OrderRef(BaseModel):
    order_id: str


# ---------- config + demo data ----------
@app.get("/api/config")
def config():
    return {
        "mode": "mock" if MOCK else "live",
        "client_id": os.getenv("PAYPAL_CLIENT_ID", "") if not MOCK else "",
        "currency": CURRENCY,
        "explainer": active_provider(),  # "none" | "ollama" | "anthropic" | "openai"
    }


@app.get("/api/payees")
def payees():
    """Representative demo payees pulled from the generated profiles."""
    store = engine.payees
    def first(kind):
        return next((k for k, v in store.items() if v["kind"] == kind), None)

    presets = [
        {"id": first("legit"), "label": "Ria's Craft Store",
         "note": "established merchant", "expected": "safe"},
        {"id": first("front"), "label": "QuickHire Jobs (deposit)",
         "note": "new account, 'job fee'", "expected": "risky"},
        {"id": first("core"), "label": "GlobalPay Settlements",
         "note": "cash-out account", "expected": "risky"},
        {"id": "unknown_payee_777", "label": "A friend (new payee)",
         "note": "no history on file", "expected": "safe"},
    ]
    return [p for p in presets if p["id"]]


# ---------- payment flow ----------
@app.post("/api/create-order")
def create_order(req: CreateOrderReq):
    if req.amount <= 0:
        raise HTTPException(400, "amount must be positive")

    if MOCK:
        oid = f"MOCK-{uuid.uuid4().hex[:10].upper()}"
    else:
        try:
            order = pp.create_order(req.amount, CURRENCY)
            oid = order["id"]
        except Exception as e:
            raise HTTPException(502, f"PayPal create-order failed: {e}")

    ORDERS[oid] = {"payee_id": req.payee_id, "amount": req.amount,
                   "payee_label": req.payee_label}
    return {"id": oid, "mode": "mock" if MOCK else "live"}


@app.post("/api/risk-check")
def risk_check(req: OrderRef):
    order = ORDERS.get(req.order_id)
    if not order:
        raise HTTPException(404, "unknown order")
    r = engine.score("checkout_user", order["payee_id"], order["amount"])
    result = r.to_dict()
    if r.show_interstitial:
        result["warning_text"] = explain(
            r.score, r.band, r.reasons, order["amount"],
            order.get("payee_label", "this payee"))
    return result


@app.post("/api/capture")
def capture(req: OrderRef):
    order = ORDERS.get(req.order_id)
    if not order:
        raise HTTPException(404, "unknown order")

    if MOCK:
        ORDERS.pop(req.order_id, None)
        return {"status": "COMPLETED", "mode": "mock", "amount": order["amount"]}

    try:
        res = pp.capture_order(req.order_id)
    except Exception as e:
        raise HTTPException(502, f"PayPal capture failed: {e}")
    ORDERS.pop(req.order_id, None)
    return {"status": res.get("status", "UNKNOWN"), "mode": "live", "raw": res}


# ---------- static frontend ----------
@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND, "index.html"))


app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    print(f"PayDrishti running in {'MOCK' if MOCK else 'LIVE (PayPal sandbox)'} mode")
    uvicorn.run(app, host="127.0.0.1", port=8000)
