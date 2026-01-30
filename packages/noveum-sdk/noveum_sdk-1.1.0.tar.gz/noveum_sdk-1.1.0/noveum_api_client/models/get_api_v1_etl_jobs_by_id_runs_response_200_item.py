from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.get_api_v1_etl_jobs_by_id_runs_response_200_item_filter_config_type_0 import (
        GetApiV1EtlJobsByIdRunsResponse200ItemFilterConfigType0,
    )


T = TypeVar("T", bound="GetApiV1EtlJobsByIdRunsResponse200Item")


@_attrs_define
class GetApiV1EtlJobsByIdRunsResponse200Item:
    """
    Attributes:
        id (str):
        etl_job_id (str):
        dataset_slug (None | str):
        start_time (None | str):
        end_time (None | str):
        status (str):
        traces_processed (float):
        traces_failed (float):
        dataset_items_created (float):
        error (None | str):
        trace_ids (list[str]):
        filter_config (GetApiV1EtlJobsByIdRunsResponse200ItemFilterConfigType0 | None):
        created_at (str):
        updated_at (str):
    """

    id: str
    etl_job_id: str
    dataset_slug: None | str
    start_time: None | str
    end_time: None | str
    status: str
    traces_processed: float
    traces_failed: float
    dataset_items_created: float
    error: None | str
    trace_ids: list[str]
    filter_config: GetApiV1EtlJobsByIdRunsResponse200ItemFilterConfigType0 | None
    created_at: str
    updated_at: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.get_api_v1_etl_jobs_by_id_runs_response_200_item_filter_config_type_0 import (
            GetApiV1EtlJobsByIdRunsResponse200ItemFilterConfigType0,
        )

        id = self.id

        etl_job_id = self.etl_job_id

        dataset_slug: None | str
        dataset_slug = self.dataset_slug

        start_time: None | str
        start_time = self.start_time

        end_time: None | str
        end_time = self.end_time

        status = self.status

        traces_processed = self.traces_processed

        traces_failed = self.traces_failed

        dataset_items_created = self.dataset_items_created

        error: None | str
        error = self.error

        trace_ids = self.trace_ids

        filter_config: dict[str, Any] | None
        if isinstance(self.filter_config, GetApiV1EtlJobsByIdRunsResponse200ItemFilterConfigType0):
            filter_config = self.filter_config.to_dict()
        else:
            filter_config = self.filter_config

        created_at = self.created_at

        updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "etlJobId": etl_job_id,
                "datasetSlug": dataset_slug,
                "startTime": start_time,
                "endTime": end_time,
                "status": status,
                "tracesProcessed": traces_processed,
                "tracesFailed": traces_failed,
                "datasetItemsCreated": dataset_items_created,
                "error": error,
                "traceIds": trace_ids,
                "filterConfig": filter_config,
                "createdAt": created_at,
                "updatedAt": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_api_v1_etl_jobs_by_id_runs_response_200_item_filter_config_type_0 import (
            GetApiV1EtlJobsByIdRunsResponse200ItemFilterConfigType0,
        )

        d = dict(src_dict)
        id = d.pop("id")

        etl_job_id = d.pop("etlJobId")

        def _parse_dataset_slug(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        dataset_slug = _parse_dataset_slug(d.pop("datasetSlug"))

        def _parse_start_time(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        start_time = _parse_start_time(d.pop("startTime"))

        def _parse_end_time(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        end_time = _parse_end_time(d.pop("endTime"))

        status = d.pop("status")

        traces_processed = d.pop("tracesProcessed")

        traces_failed = d.pop("tracesFailed")

        dataset_items_created = d.pop("datasetItemsCreated")

        def _parse_error(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        error = _parse_error(d.pop("error"))

        trace_ids = cast(list[str], d.pop("traceIds"))

        def _parse_filter_config(data: object) -> GetApiV1EtlJobsByIdRunsResponse200ItemFilterConfigType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                filter_config_type_0 = GetApiV1EtlJobsByIdRunsResponse200ItemFilterConfigType0.from_dict(data)

                return filter_config_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(GetApiV1EtlJobsByIdRunsResponse200ItemFilterConfigType0 | None, data)

        filter_config = _parse_filter_config(d.pop("filterConfig"))

        created_at = d.pop("createdAt")

        updated_at = d.pop("updatedAt")

        get_api_v1_etl_jobs_by_id_runs_response_200_item = cls(
            id=id,
            etl_job_id=etl_job_id,
            dataset_slug=dataset_slug,
            start_time=start_time,
            end_time=end_time,
            status=status,
            traces_processed=traces_processed,
            traces_failed=traces_failed,
            dataset_items_created=dataset_items_created,
            error=error,
            trace_ids=trace_ids,
            filter_config=filter_config,
            created_at=created_at,
            updated_at=updated_at,
        )

        get_api_v1_etl_jobs_by_id_runs_response_200_item.additional_properties = d
        return get_api_v1_etl_jobs_by_id_runs_response_200_item

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
