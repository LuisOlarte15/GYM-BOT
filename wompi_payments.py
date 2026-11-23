"""Integración Wompi Web Checkout para GYM BOT V16.
La firma de integridad se calcula en servidor. Nunca exponer secretos al navegador.
"""
from __future__ import annotations
import hashlib, hmac, os, secrets
from urllib.parse import urlencode

def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

def wompi_configured() -> bool:
    return all(_env(k) for k in ("WOMPI_PUBLIC_KEY", "WOMPI_INTEGRITY_SECRET", "GYMBOT_PUBLIC_BASE_URL"))

def create_checkout(reference: str, amount_cop: int, customer_email: str = "", customer_name: str = "") -> dict:
    public_key = _env("WOMPI_PUBLIC_KEY")
    integrity = _env("WOMPI_INTEGRITY_SECRET")
    base_url = _env("GYMBOT_PUBLIC_BASE_URL").rstrip("/")
    if not public_key or not integrity or not base_url:
        raise RuntimeError("Wompi no está configurado. Revisa las variables WOMPI_* y GYMBOT_PUBLIC_BASE_URL.")
    if not base_url.startswith("https://"):
        raise RuntimeError("La URL pública debe usar HTTPS para habilitar pagos reales y webhooks.")
    if not reference or amount_cop < 1:
        raise ValueError("Referencia o valor de pago inválido.")
    cents = int(amount_cop) * 100
    signature = hashlib.sha256(f"{reference}{cents}COP{integrity}".encode("utf-8")).hexdigest()
    params = {
        "public-key": public_key,
        "currency": "COP",
        "amount-in-cents": str(cents),
        "reference": reference,
        "signature:integrity": signature,
        "redirect-url": f"{base_url}/app?payment=return",
    }
    if customer_email:
        params["customer-data:email"] = customer_email
    if customer_name:
        params["customer-data:full-name"] = customer_name
    return {"checkout_url": "https://checkout.wompi.co/p/?" + urlencode(params), "amount_cop": int(amount_cop), "currency": "COP"}

def _nested(obj: dict, dotted: str):
    value = obj
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"Falta propiedad de firma: {dotted}")
        value = value[part]
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        raise ValueError(f"Propiedad de firma no escalar: {dotted}")
    return str(value)

def verify_event(event: dict, header_checksum: str = "") -> bool:
    secret = _env("WOMPI_EVENTS_SECRET")
    signature = event.get("signature") or {}
    checksum = header_checksum or signature.get("checksum", "")
    props = signature.get("properties") or []
    timestamp = event.get("timestamp")
    if not secret or not checksum or not props or timestamp is None:
        return False
    try:
        material = "".join(_nested(event.get("data") or {}, p) for p in props) + str(timestamp) + secret
        expected = hashlib.sha256(material.encode("utf-8")).hexdigest()
        return hmac.compare_digest(expected.lower(), str(checksum).lower())
    except (ValueError, TypeError):
        return False
