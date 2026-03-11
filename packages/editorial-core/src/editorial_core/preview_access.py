from __future__ import annotations


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower()
    return normalized in {"127.0.0.1", "::1", "localhost"}


def ensure_preview_access_configuration(*, host: str, preview_token: str | None) -> None:
    if _is_loopback_host(host):
        return
    if preview_token and preview_token.strip():
        return
    raise ValueError("preview_token is required when binding review_web beyond localhost")


def is_preview_request_authorized(
    *,
    client_host: str,
    authorization_header: str | None,
    preview_token: str | None,
    path: str,
) -> bool:
    if path == "/healthz":
        return True
    if not preview_token:
        return True
    if _is_loopback_host(client_host):
        return True
    if not authorization_header:
        return False
    header = authorization_header.strip()
    return header == f"Bearer {preview_token}"
