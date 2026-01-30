from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.queue_response_legacy_dto import QueueResponseLegacyDto


T = TypeVar("T", bound="QueuesResponseLegacyDto")


@_attrs_define
class QueuesResponseLegacyDto:
    """
    Attributes:
        background_task (QueueResponseLegacyDto):
        backup_database (QueueResponseLegacyDto):
        duplicate_detection (QueueResponseLegacyDto):
        face_detection (QueueResponseLegacyDto):
        facial_recognition (QueueResponseLegacyDto):
        library (QueueResponseLegacyDto):
        metadata_extraction (QueueResponseLegacyDto):
        migration (QueueResponseLegacyDto):
        notifications (QueueResponseLegacyDto):
        ocr (QueueResponseLegacyDto):
        search (QueueResponseLegacyDto):
        sidecar (QueueResponseLegacyDto):
        smart_search (QueueResponseLegacyDto):
        storage_template_migration (QueueResponseLegacyDto):
        thumbnail_generation (QueueResponseLegacyDto):
        video_conversion (QueueResponseLegacyDto):
        workflow (QueueResponseLegacyDto):
    """

    background_task: QueueResponseLegacyDto
    backup_database: QueueResponseLegacyDto
    duplicate_detection: QueueResponseLegacyDto
    face_detection: QueueResponseLegacyDto
    facial_recognition: QueueResponseLegacyDto
    library: QueueResponseLegacyDto
    metadata_extraction: QueueResponseLegacyDto
    migration: QueueResponseLegacyDto
    notifications: QueueResponseLegacyDto
    ocr: QueueResponseLegacyDto
    search: QueueResponseLegacyDto
    sidecar: QueueResponseLegacyDto
    smart_search: QueueResponseLegacyDto
    storage_template_migration: QueueResponseLegacyDto
    thumbnail_generation: QueueResponseLegacyDto
    video_conversion: QueueResponseLegacyDto
    workflow: QueueResponseLegacyDto
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        background_task = self.background_task.to_dict()

        backup_database = self.backup_database.to_dict()

        duplicate_detection = self.duplicate_detection.to_dict()

        face_detection = self.face_detection.to_dict()

        facial_recognition = self.facial_recognition.to_dict()

        library = self.library.to_dict()

        metadata_extraction = self.metadata_extraction.to_dict()

        migration = self.migration.to_dict()

        notifications = self.notifications.to_dict()

        ocr = self.ocr.to_dict()

        search = self.search.to_dict()

        sidecar = self.sidecar.to_dict()

        smart_search = self.smart_search.to_dict()

        storage_template_migration = self.storage_template_migration.to_dict()

        thumbnail_generation = self.thumbnail_generation.to_dict()

        video_conversion = self.video_conversion.to_dict()

        workflow = self.workflow.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "backgroundTask": background_task,
                "backupDatabase": backup_database,
                "duplicateDetection": duplicate_detection,
                "faceDetection": face_detection,
                "facialRecognition": facial_recognition,
                "library": library,
                "metadataExtraction": metadata_extraction,
                "migration": migration,
                "notifications": notifications,
                "ocr": ocr,
                "search": search,
                "sidecar": sidecar,
                "smartSearch": smart_search,
                "storageTemplateMigration": storage_template_migration,
                "thumbnailGeneration": thumbnail_generation,
                "videoConversion": video_conversion,
                "workflow": workflow,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_response_legacy_dto import QueueResponseLegacyDto

        d = dict(src_dict)
        background_task = QueueResponseLegacyDto.from_dict(d.pop("backgroundTask"))

        backup_database = QueueResponseLegacyDto.from_dict(d.pop("backupDatabase"))

        duplicate_detection = QueueResponseLegacyDto.from_dict(d.pop("duplicateDetection"))

        face_detection = QueueResponseLegacyDto.from_dict(d.pop("faceDetection"))

        facial_recognition = QueueResponseLegacyDto.from_dict(d.pop("facialRecognition"))

        library = QueueResponseLegacyDto.from_dict(d.pop("library"))

        metadata_extraction = QueueResponseLegacyDto.from_dict(d.pop("metadataExtraction"))

        migration = QueueResponseLegacyDto.from_dict(d.pop("migration"))

        notifications = QueueResponseLegacyDto.from_dict(d.pop("notifications"))

        ocr = QueueResponseLegacyDto.from_dict(d.pop("ocr"))

        search = QueueResponseLegacyDto.from_dict(d.pop("search"))

        sidecar = QueueResponseLegacyDto.from_dict(d.pop("sidecar"))

        smart_search = QueueResponseLegacyDto.from_dict(d.pop("smartSearch"))

        storage_template_migration = QueueResponseLegacyDto.from_dict(d.pop("storageTemplateMigration"))

        thumbnail_generation = QueueResponseLegacyDto.from_dict(d.pop("thumbnailGeneration"))

        video_conversion = QueueResponseLegacyDto.from_dict(d.pop("videoConversion"))

        workflow = QueueResponseLegacyDto.from_dict(d.pop("workflow"))

        queues_response_legacy_dto = cls(
            background_task=background_task,
            backup_database=backup_database,
            duplicate_detection=duplicate_detection,
            face_detection=face_detection,
            facial_recognition=facial_recognition,
            library=library,
            metadata_extraction=metadata_extraction,
            migration=migration,
            notifications=notifications,
            ocr=ocr,
            search=search,
            sidecar=sidecar,
            smart_search=smart_search,
            storage_template_migration=storage_template_migration,
            thumbnail_generation=thumbnail_generation,
            video_conversion=video_conversion,
            workflow=workflow,
        )

        queues_response_legacy_dto.additional_properties = d
        return queues_response_legacy_dto

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
