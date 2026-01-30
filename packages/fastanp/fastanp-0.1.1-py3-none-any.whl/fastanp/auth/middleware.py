"""DID-WBA 认证中间件。"""

import fnmatch
import logging
from collections.abc import Callable
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

from anp.authentication.did_wba_verifier import (
    DidWbaVerifier,
    DidWbaVerifierConfig,
    DidWbaVerifierError,
)

logger = logging.getLogger(__name__)

EXEMPT_PATHS = [
    "/favicon.ico",
    "/health",
    "/docs",
    "*/ad.json",
    "/info/*",
]


def _get_and_validate_domain(
    request: Request, allowed_domains: Optional[list[str]]
) -> str:
    host = request.headers.get("host", "")
    domain = host.split(":")[0]

    if allowed_domains and domain not in allowed_domains:
        raise HTTPException(
            status_code=403, detail=f"Domain {domain} is not in the allowed domains list"
        )
    return domain


async def verify_auth_header(
    request: Request,
    verifier: DidWbaVerifier,
    allowed_domains: Optional[list[str]] = None,
) -> Dict[str, Any]:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    domain = _get_and_validate_domain(request, allowed_domains)
    try:
        return await verifier.verify_auth_header(auth_header, domain)
    except DidWbaVerifierError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


async def authenticate_request(
    request: Request,
    verifier: DidWbaVerifier,
    allowed_domains: Optional[list[str]] = None,
) -> Optional[Dict[str, Any]]:
    logger.info("Authenticating request to path: %s", request.url.path)

    for exempt_path in EXEMPT_PATHS:
        if fnmatch.fnmatch(request.url.path, exempt_path):
            logger.info(
                "Path %s is exempt from authentication (matched: %s)",
                request.url.path,
                exempt_path,
            )
            return None

    logger.info("Path %s requires authentication", request.url.path)
    return await verify_auth_header(request, verifier, allowed_domains)


async def auth_middleware(
    request: Request,
    call_next: Callable,
    verifier: DidWbaVerifier,
    allowed_domains: Optional[list[str]] = None,
) -> Response:
    try:
        response_auth = await authenticate_request(request, verifier, allowed_domains)
        request.state.auth_result = response_auth
        request.state.did = response_auth.get("did") if response_auth else None

        response = await call_next(request)

        if response_auth and response_auth.get("token_type") == "bearer":
            response.headers["authorization"] = "bearer " + response_auth["access_token"]

        return response
    except HTTPException as exc:
        logger.error("Authentication error: %s", exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    except Exception as exc:
        logger.error("Unexpected auth middleware error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


def create_auth_middleware(config: DidWbaVerifierConfig) -> Callable:
    verifier = DidWbaVerifier(config)
    allowed_domains = config.allowed_domains

    async def middleware(request: Request, call_next: Callable) -> Response:
        return await auth_middleware(request, call_next, verifier, allowed_domains)

    return middleware
