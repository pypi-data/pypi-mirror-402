import base64
import json
from datetime import datetime, timedelta
from typing import Tuple, Optional
from functools import lru_cache

import urllib3

from .files import get_pool
from .openapi import Configuration
from .versions import host_remove_version

# Get new token REFRESH_TIME_DELTA before it really expires.
REFRESH_TIME_DELTA = timedelta(minutes=5).total_seconds()
REQUEST_TIMEOUT = 5  # seconds


class AuthenticationError(Exception):
    pass


def send_json_request(method, url, **kwargs):
    """Helper function for sending a request and decoding the JSON response.

    The request body, if supplied, will be automatically JSON-encoded.

    The request has a default policy of 3 retries.

    Raises an AuthenticationError if the response is not successful. Optionally
    supply an 'error_msg' to change the message.
    """
    headers = kwargs.pop("headers", {})
    error_msg = kwargs.pop("error_msg", "Error sending request")
    headers["Accept"] = "application/json"
    if "body" in kwargs:
        assert not isinstance(kwargs["body"], (bytes, str))
        kwargs["body"] = json.dumps(kwargs["body"])
        headers["Content-Type"] = "application/json"
    resp = get_pool().request(
        method, url, headers=headers, timeout=REQUEST_TIMEOUT, **kwargs
    )
    if resp.status not in (200, 201):
        try:
            detail = json.loads(resp.data)
            if "detail" in detail:
                detail = detail["detail"]
            elif "error" in detail:
                detail = detail["error"]
        except Exception:
            detail = f"server responded with error code {resp.status}"
        raise AuthenticationError(f"{error_msg}: {detail}")
    return json.loads(resp.data.decode("ISO-8859-1"))


@lru_cache(1)
def decode_jwt(token):
    """Decode a JWT without checking its signature"""
    # JWT consists of {header}.{payload}.{signature}
    _, payload, _ = token.split(".")
    # JWT should be padded with = (base64.b64decode expects this)
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.b64decode(payload))


def is_token_usable(token: str) -> bool:
    if token is None:
        return False

    try:
        payload = decode_jwt(token)
    except Exception:
        return False

    expiry_dt = datetime.utcfromtimestamp(payload["exp"])
    sec_left = (expiry_dt - datetime.utcnow()).total_seconds()
    return sec_left >= REFRESH_TIME_DELTA


def get_issuer(token: str) -> Optional[str]:
    if token is None:
        return

    try:
        payload = decode_jwt(token)
    except Exception:
        return

    return payload.get("iss")


def get_client_id(token: str) -> Optional[str]:
    if token is None:
        return

    try:
        payload = decode_jwt(token)
    except Exception:
        return

    return payload.get("client_id")


def get_scope(token: str) -> Optional[str]:
    if token is None:
        return

    try:
        payload = decode_jwt(token)
    except Exception:
        return

    return payload.get("scope")


def refresh_api_key(config: Configuration):
    """Refreshes the access token if it is expired"""
    access_token = config.api_key.get("Authorization")
    if is_token_usable(access_token):
        return
    issuer = get_issuer(access_token)
    if issuer is None:
        access_token, refresh_token = refresh_simplejwt_token(config)
        config.api_key["refresh"] = refresh_token
    else:
        access_token = refresh_oauth2_token(
            issuer=get_issuer(access_token),
            client_id=get_client_id(access_token),
            scope=get_scope(access_token),
            client_secret=config.api_key.get("client_secret"),
            refresh_token=config.api_key.get("refresh"),
        )
    config.api_key["Authorization"] = access_token


def get_auth_token(username: str, password: str, api_host: str):
    return send_json_request(
        method="POST",
        url=f"{host_remove_version(api_host)}/v3/auth/token/",
        body={"username": username, "password": password},
        error_msg="Cannot fetch an access token",
    )


def refresh_simplejwt_token(config: Configuration) -> Tuple[str, str]:
    refresh_key = config.api_key.get("refresh")
    if is_token_usable(refresh_key):
        tokens = send_json_request(
            method="POST",
            url=f"{host_remove_version(config.host)}/v3/auth/refresh-token/",
            body={"refresh": refresh_key},
            error_msg="Cannot refresh the access token",
        )
    else:
        if not config.username or not config.password:
            raise AuthenticationError(
                "Cannot fetch a new access token because username/password were not supplied."
            )
        tokens = get_auth_token(config.username, config.password, config.host)
    return tokens["access"], tokens["refresh"]


def oauth2_autodiscovery(issuer: str):
    # use autodiscovery to fetch server details
    return send_json_request(
        method="GET",
        url=f"{issuer}/.well-known/openid-configuration",
        error_msg=f"Cannot discover the authorization server '{issuer}'",
    )


def refresh_oauth2_token(
    issuer: str,
    client_id: str,
    client_secret: Optional[str] = None,
    refresh_token: Optional[str] = None,
    scope: Optional[str] = None,
):
    """Refresh an OAuth2 access token.

    If no refresh_token is supplied, then the client credentials flow is taken. A client_secret
    is required in that case. Otherwise, just use the refresh token flow.

    The scope can be supplied when using the client credentials flow.
    """
    if refresh_token:
        grant_type = "refresh_token"
    else:
        grant_type = "client_credentials"

    if not client_secret and grant_type == "client_credentials":
        raise AuthenticationError(
            "Cannot fetch an access token because THREEDI_API_REFESH_TOKEN and/or "
            "THREEDI_API_CLIENT_SECRET where not supplied."
        )

    # send the refresh token request
    token_url = oauth2_autodiscovery(issuer)["token_endpoint"]
    fields = {"grant_type": grant_type}
    if grant_type == "refresh_token":
        fields["refresh_token"] = refresh_token

    # include client id and optionally secret in headers/body
    if client_secret:
        # Include id + secret in headers using basic auth
        headers = urllib3.make_headers(basic_auth=f"{client_id}:{client_secret}")
    else:
        # Include only id (in body)
        headers = {}
        fields["client_id"] = client_id

    # include scope (for client credentials only)
    if grant_type == "client_credentials" and scope:
        fields["scope"] = scope

    tokens = send_json_request(
        method="POST",
        url=token_url,
        fields=fields,
        headers=headers,
        encode_multipart=False,
        error_msg="Failed to refresh the access token",
    )
    return tokens["access_token"]
