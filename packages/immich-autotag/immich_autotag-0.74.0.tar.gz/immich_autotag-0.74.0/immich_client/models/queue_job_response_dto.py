from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.job_name import JobName
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.queue_job_response_dto_data import QueueJobResponseDtoData


T = TypeVar("T", bound="QueueJobResponseDto")


@_attrs_define
class QueueJobResponseDto:
    """
    Attributes:
        data (QueueJobResponseDtoData):
        name (JobName):
        timestamp (int):
        id (str | Unset):
    """

    data: QueueJobResponseDtoData
    name: JobName
    timestamp: int
    id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data.to_dict()

        name = self.name.value

        timestamp = self.timestamp

        id = self.id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "name": name,
                "timestamp": timestamp,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_job_response_dto_data import QueueJobResponseDtoData

        d = dict(src_dict)
        data = QueueJobResponseDtoData.from_dict(d.pop("data"))

        name = JobName(d.pop("name"))

        timestamp = d.pop("timestamp")

        id = d.pop("id", UNSET)

        queue_job_response_dto = cls(
            data=data,
            name=name,
            timestamp=timestamp,
            id=id,
        )

        queue_job_response_dto.additional_properties = d
        return queue_job_response_dto

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
