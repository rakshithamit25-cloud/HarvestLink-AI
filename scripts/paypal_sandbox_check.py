#!/usr/bin/env python3
"""
PayPal Sandbox Verification Script
Checks PayPal Sandbox connectivity by authenticating and creating a $1.00 USD test order.
Never captures payments, never prints tokens or secrets.
"""

import base64
import json
import os
import sys
from pathlib import Path
import urllib.error
import urllib.request


def load_environment():
    """Load variables from .env if present without external dependencies."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Fallback to direct reading of .env from repo root if not already set
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.is_file():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key not in os.environ:
                    os.environ[key] = val


def main():
    load_environment()

    client_id = os.getenv("PAYPAL_CLIENT_ID", "").strip()
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret or client_id == "mock_client_id":
        print("Error: PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET must be configured in .env", file=sys.stderr)
        sys.exit(1)

    base_url = "https://api-m.sandbox.paypal.com"

    # Step 1: Obtain OAuth2 Bearer Token
    auth_bytes = f"{client_id}:{client_secret}".encode("utf-8")
    auth_header = f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"

    token_req = urllib.request.Request(
        f"{base_url}/v1/oauth2/token",
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": auth_header,
            "Accept": "application/json",
            "Accept-Language": "en_US",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(token_req, timeout=15) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))
            access_token = token_data.get("access_token")
    except urllib.error.HTTPError as e:
        print(f"HTTP Status: {e.code}")
        print("Error: Failed to obtain OAuth token from PayPal Sandbox.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("Error: Network or connection failure during authentication.", file=sys.stderr)
        sys.exit(1)

    if not access_token:
        print("Error: No access token received from PayPal Sandbox.", file=sys.stderr)
        sys.exit(1)

    # Step 2: Create a USD 1.00 Order (Intent: CAPTURE, without capturing)
    order_payload = json.dumps({
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": "1.00",
                }
            }
        ],
    }).encode("utf-8")

    order_req = urllib.request.Request(
        f"{base_url}/v2/checkout/orders",
        data=order_payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(order_req, timeout=15) as resp:
            status_code = resp.status
            order_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Status: {e.code}")
        print("Error: Failed to create order in PayPal Sandbox.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("Error: Network or connection failure during order creation.", file=sys.stderr)
        sys.exit(1)

    order_id = order_data.get("id")
    approval_url = None
    for link in order_data.get("links", []):
        if link.get("rel") == "approve":
            approval_url = link.get("href")
            break

    # Print ONLY the HTTP status, order ID, and approval URL
    print(f"HTTP Status: {status_code}")
    print(f"Order ID: {order_id}")
    print(f"Approval URL: {approval_url}")


if __name__ == "__main__":
    main()

