from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.queue_name import QueueName

if TYPE_CHECKING:
    from ..models.queue_statistics_dto import QueueStatisticsDto


T = TypeVar("T", bound="QueueResponseDto")


@_attrs_define
class QueueResponseDto:
    """
    Attributes:
        is_paused (bool):
        name (QueueName):
        statistics (QueueStatisticsDto):
    """

    is_paused: bool
    name: QueueName
    statistics: QueueStatisticsDto
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_paused = self.is_paused

        name = self.name.value

        statistics = self.statistics.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isPaused": is_paused,
                "name": name,
                "statistics": statistics,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_statistics_dto import QueueStatisticsDto

        d = dict(src_dict)
        is_paused = d.pop("isPaused")

        name = QueueName(d.pop("name"))

        statistics = QueueStatisticsDto.from_dict(d.pop("statistics"))

        queue_response_dto = cls(
            is_paused=is_paused,
            name=name,
            statistics=statistics,
        )

        queue_response_dto.additional_properties = d
        return queue_response_dto

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
