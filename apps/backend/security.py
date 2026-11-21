"""
Service-to-service authentication for the FastAPI backend.

Only the Next.js server calls this API. It sends ``Authorization: Bearer <token>``
(see ``apps/web/lib/fastApiClient.ts``), where the token is the shared secret
``FASTAPI_BEARER_TOKEN`` configured on both sides.

Behaviour by configuration:

* Token configured          → every request must present exactly that token (401 otherwise).
* Token unset on Cloud Run  → every request is refused (503). A deploy that forgot the
                              secret fails closed instead of exposing the paid LLM routes.
* Token unset locally       → requests are allowed, with a one-time warning, so the local
                              dev stack runs without extra setup.

Cloud Run is detected by ``K_SERVICE``, which the platform sets on every revision.
The environment is read per request (cheap) so tests and secret rotation need no restart.
"""

import os
import secrets

from fastapi import Header, HTTPException

from apps.utils.logging import get_logger

logger = get_logger(__name__)

TOKEN_ENV_VAR = "FASTAPI_BEARER_TOKEN"
CLOUD_RUN_ENV_VAR = "K_SERVICE"

_warned_unprotected = False


def _unauthorized(reason: str) -> HTTPException:
    logger.warning("auth_rejected | reason=%s", reason)
    return HTTPException(
        status_code=401,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_bearer_token(
    authorization: str | None = Header(default=None),
) -> None:
    """FastAPI dependency: enforce the shared bearer token (see module docstring)."""
    global _warned_unprotected

    expected = os.environ.get(TOKEN_ENV_VAR, "")
    if not expected:
        if os.environ.get(CLOUD_RUN_ENV_VAR):
            logger.error("auth_misconfigured | %s is not set on Cloud Run", TOKEN_ENV_VAR)
            raise HTTPException(status_code=503, detail="Service not configured")
        if not _warned_unprotected:
            logger.warning(
                "auth_disabled | %s is not set — API is unprotected (local dev only)",
                TOKEN_ENV_VAR,
            )
            _warned_unprotected = True
        return

    if not authorization:
        raise _unauthorized("missing_header")

    scheme, _, presented = authorization.partition(" ")
    if scheme.lower() != "bearer" or not presented:
        raise _unauthorized("malformed_header")

    # Constant-time comparison so the token can't be recovered by timing responses.
    if not secrets.compare_digest(presented.encode(), expected.encode()):
        raise _unauthorized("wrong_token")
