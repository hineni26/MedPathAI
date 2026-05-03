import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

from fastapi import Header, HTTPException


JWT_SECRET = os.getenv("JWT_SECRET") or "dev-only-change-me"
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "86400"))
PFL_OFFICER_API_KEY = os.getenv("PFL_OFFICER_API_KEY")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: str) -> str:
    digest = hmac.new(JWT_SECRET.encode("utf-8"), message.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def create_access_token(user_id: str, role: str = "user") -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + JWT_TTL_SECONDS,
    }
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}"
    return f"{signing_input}.{_sign(signing_input)}"


def verify_access_payload(token: str) -> dict:
    try:
        encoded_header, encoded_payload, signature = token.split(".", 2)
        signing_input = f"{encoded_header}.{encoded_payload}"
        if not hmac.compare_digest(_sign(signing_input), signature):
            raise ValueError("bad signature")

        header = json.loads(_b64url_decode(encoded_header))
        payload = json.loads(_b64url_decode(encoded_payload))
        if header.get("alg") != "HS256":
            raise ValueError("unsupported alg")
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("expired")

        if not payload.get("sub"):
            raise ValueError("missing subject")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired session") from exc


def verify_access_token(token: str) -> str:
    payload = verify_access_payload(token)
    return str(payload["sub"])


def require_user(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = verify_access_payload(authorization.removeprefix("Bearer ").strip())
    if payload.get("role", "user") != "user":
        raise HTTPException(status_code=403, detail="Patient authentication required")
    return str(payload["sub"])


def require_officer(
    authorization: Optional[str] = Header(default=None),
    x_pfl_api_key: Optional[str] = Header(default=None),
) -> None:
    if PFL_OFFICER_API_KEY and x_pfl_api_key and hmac.compare_digest(x_pfl_api_key, PFL_OFFICER_API_KEY):
        return

    if authorization and authorization.startswith("Bearer "):
        payload = verify_access_payload(authorization.removeprefix("Bearer ").strip())
        if payload.get("role") == "officer":
            return

    raise HTTPException(status_code=401, detail="PFL officer authentication required")
