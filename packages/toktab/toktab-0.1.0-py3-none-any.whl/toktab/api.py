"""TokTab API client."""

from typing import Any

import httpx

BASE_URL = "https://toktab.com/api"
TIMEOUT = 10.0


class TokTabError(Exception):
    """Base exception for TokTab API errors."""

    pass


class ModelNotFoundError(TokTabError):
    """Raised when a model is not found."""

    pass


class APIError(TokTabError):
    """Raised when the API returns an error."""

    pass


def get_model(slug: str) -> dict[str, Any]:
    """Fetch detailed information for a specific model.

    Args:
        slug: The model identifier (e.g., 'gemini-3-flash-preview')

    Returns:
        Dict containing model data including pricing and capabilities.

    Raises:
        ModelNotFoundError: If the model doesn't exist.
        APIError: If the API request fails.
    """
    url = f"{BASE_URL}/{slug}/"
    try:
        response = httpx.get(url, timeout=TIMEOUT, follow_redirects=True)
        if response.status_code == 404:
            raise ModelNotFoundError(f"Model '{slug}' not found")
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        raise APIError("Request timed out. Please try again.")
    except httpx.HTTPStatusError as e:
        raise APIError(f"API error: {e.response.status_code}")
    except httpx.RequestError as e:
        raise APIError(f"Network error: {e}")


def search(query: str, limit: int = 20) -> dict[str, Any]:
    """Search for models by name or provider.

    Args:
        query: Search term (supports partial matches and 'provider:' prefix)
        limit: Maximum number of results (default 20, max 50)

    Returns:
        Dict containing 'results', 'query', and 'count'.

    Raises:
        APIError: If the API request fails.
    """
    url = f"{BASE_URL}/search"
    params = {"q": query, "limit": min(limit, 50)}
    try:
        response = httpx.get(url, params=params, timeout=TIMEOUT, follow_redirects=True)
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        raise APIError("Request timed out. Please try again.")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            raise APIError("Invalid search query")
        raise APIError(f"API error: {e.response.status_code}")
    except httpx.RequestError as e:
        raise APIError(f"Network error: {e}")


