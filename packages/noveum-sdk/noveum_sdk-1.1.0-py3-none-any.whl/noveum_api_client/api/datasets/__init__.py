"""Contains endpoint functions for accessing the Dataset API"""

# Import all dataset endpoint modules to make them accessible
from . import (
    delete_api_v1_datasets_by_dataset_slug_items,
    delete_api_v1_datasets_by_dataset_slug_items_by_item_id,
    delete_api_v1_datasets_by_slug,
    get_api_v1_datasets,
    get_api_v1_datasets_by_dataset_slug_items,
    get_api_v1_datasets_by_dataset_slug_items_by_item_id,
    get_api_v1_datasets_by_dataset_slug_versions,
    get_api_v1_datasets_by_dataset_slug_versions_by_version,
    get_api_v1_datasets_by_dataset_slug_versions_diff,
    get_api_v1_datasets_by_slug,
    post_api_v1_datasets,
    post_api_v1_datasets_by_dataset_slug_items,
    post_api_v1_datasets_by_dataset_slug_versions,
    post_api_v1_datasets_by_dataset_slug_versions_publish,
    put_api_v1_datasets_by_slug,
)

__all__ = [
    "delete_api_v1_datasets_by_dataset_slug_items",
    "delete_api_v1_datasets_by_dataset_slug_items_by_item_id",
    "delete_api_v1_datasets_by_slug",
    "get_api_v1_datasets",
    "get_api_v1_datasets_by_dataset_slug_items",
    "get_api_v1_datasets_by_dataset_slug_items_by_item_id",
    "get_api_v1_datasets_by_dataset_slug_versions",
    "get_api_v1_datasets_by_dataset_slug_versions_by_version",
    "get_api_v1_datasets_by_dataset_slug_versions_diff",
    "get_api_v1_datasets_by_slug",
    "post_api_v1_datasets",
    "post_api_v1_datasets_by_dataset_slug_items",
    "post_api_v1_datasets_by_dataset_slug_versions",
    "post_api_v1_datasets_by_dataset_slug_versions_publish",
    "put_api_v1_datasets_by_slug",
]
