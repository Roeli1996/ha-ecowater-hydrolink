"""Shared HTTP request helper used by both the Hydrolink and iQua coordinators."""

import asyncio
import logging

import async_timeout
from aiohttp.client_exceptions import ClientConnectorDNSError, ClientError

_LOGGER = logging.getLogger(__name__)


async def async_request_with_retry(session, method, url, *, max_retries=2, timeout=20, **kwargs):
    """Perform an HTTP request with automatic retries on DNS/network errors.

    Args:
        session: aiohttp.ClientSession to use.
        method: HTTP method (GET, POST, PUT, ...).
        url: Full URL.
        max_retries: Number of retries after the initial attempt.
        timeout: Per-attempt timeout in seconds.
        **kwargs: Additional arguments forwarded to session.request.

    Returns:
        aiohttp.ClientResponse on success.

    Raises:
        Exception if all retries fail.
    """
    for attempt in range(max_retries + 1):
        try:
            async with async_timeout.timeout(timeout):
                return await session.request(method, url, **kwargs)
        except (ClientConnectorDNSError, ClientError, asyncio.TimeoutError) as err:
            if attempt < max_retries:
                wait = 2 * (attempt + 1)
                _LOGGER.warning(
                    "Error on %s %s (attempt %d/%d): %s. Retrying in %s seconds.",
                    method, url, attempt + 1, max_retries + 1, err, wait
                )
                await asyncio.sleep(wait)
            else:
                _LOGGER.error("Max retries reached for %s %s", method, url)
                raise
        except Exception:
            _LOGGER.exception("Unexpected error on %s %s", method, url)
            raise
