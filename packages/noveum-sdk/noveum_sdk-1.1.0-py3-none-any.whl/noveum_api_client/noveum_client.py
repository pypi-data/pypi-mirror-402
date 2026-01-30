"""
High-level Noveum client wrapper for convenience methods.

This module provides a user-friendly wrapper around the generated API client
with convenience methods for common operations like evaluation and result aggregation.
"""

from typing import Any

from .api.datasets import get_api_v1_datasets_by_dataset_slug_items
from .api.scorer_results import get_api_v1_scorers_results
from .client import Client
from .types import UNSET, Unset


class NoveumClient:
    """
    High-level Noveum client with convenience methods.

    This wraps the generated API client and provides higher-level methods
    for common operations like evaluation and result analysis.

    Example:
        ```python
        client = NoveumClient(api_key="nv_...")

        # List datasets
        datasets = client.list_datasets()

        # Get dataset items
        items = client.get_dataset_items("my-dataset")

        # Get evaluation results
        results = client.get_results()
        ```
    """

    def __init__(self, api_key: str, base_url: str = "https://api.noveum.ai"):
        """
        Initialize the Noveum client.

        Args:
            api_key: Your Noveum API key (from environment or explicit)
            base_url: Base URL for the API (default: production)
        """
        self.api_key = api_key
        self.base_url = base_url
        self._client = Client(base_url=base_url, headers={"Authorization": f"Bearer {api_key}"})

    @property
    def client(self) -> Client:
        """Get the underlying generated API client."""
        return self._client

    def list_datasets(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List all datasets.

        Args:
            limit: Number of datasets to return
            offset: Pagination offset

        Returns:
            Dictionary with datasets list and metadata
        """
        from .api.datasets import get_api_v1_datasets

        response = get_api_v1_datasets.sync_detailed(
            client=self._client,
            limit=limit,
            offset=offset,
        )
        return {
            "status_code": response.status_code,
            "data": response.parsed,
            "headers": dict(response.headers),
        }

    def get_dataset_items(
        self,
        dataset_slug: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get items from a dataset.

        Args:
            dataset_slug: The dataset slug
            limit: Number of items to return
            offset: Pagination offset

        Returns:
            Dictionary with items list and metadata
        """
        response = get_api_v1_datasets_by_dataset_slug_items.sync_detailed(
            dataset_slug=dataset_slug,
            client=self._client,
            limit=limit,
            offset=offset,
        )
        return {
            "status_code": response.status_code,
            "data": response.parsed,
            "headers": dict(response.headers),
        }

    def get_results(
        self,
        dataset_slug: str | None = None,
        item_id: str | None = None,
        scorer_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get evaluation results.

        Args:
            dataset_slug: Filter by dataset
            item_id: Filter by item
            scorer_id: Filter by scorer
            limit: Number of results to return
            offset: Pagination offset

        Returns:
            Dictionary with results list
        """
        # Convert None to UNSET for API compatibility
        dataset_slug_param: str | Unset = UNSET if dataset_slug is None else dataset_slug
        item_id_param: str | Unset = UNSET if item_id is None else item_id
        scorer_id_param: str | Unset = UNSET if scorer_id is None else scorer_id

        response = get_api_v1_scorers_results.sync_detailed(
            client=self._client,
            dataset_slug=dataset_slug_param,
            item_id=item_id_param,
            scorer_id=scorer_id_param,
            limit=limit,
            offset=offset,
        )
        return {
            "status_code": response.status_code,
            "data": response.parsed,
            "headers": dict(response.headers),
        }

    def close(self):
        """Close the underlying HTTP client."""
        if self._client._client:
            self._client._client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.close()


__all__ = ["NoveumClient"]
