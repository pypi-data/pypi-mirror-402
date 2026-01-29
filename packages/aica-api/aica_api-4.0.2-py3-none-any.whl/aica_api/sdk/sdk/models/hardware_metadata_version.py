import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="HardwareMetadataVersion")


@_attrs_define
class HardwareMetadataVersion:
    """
    Attributes:
        id (UUID):
        creation_date (datetime.datetime):
        last_modified_date (datetime.datetime):
        tag (str):
        description (Union[Unset, str]):
        labels (Union[Unset, list[UUID]]):
    """

    id: UUID
    creation_date: datetime.datetime
    last_modified_date: datetime.datetime
    tag: str
    description: Union[Unset, str] = UNSET
    labels: Union[Unset, list[UUID]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        creation_date = self.creation_date.isoformat()

        last_modified_date = self.last_modified_date.isoformat()

        tag = self.tag

        description = self.description

        labels: Union[Unset, list[str]] = UNSET
        if not isinstance(self.labels, Unset):
            labels = []
            for componentsschemas_labels_item_data in self.labels:
                componentsschemas_labels_item = str(componentsschemas_labels_item_data)
                labels.append(componentsschemas_labels_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "creation_date": creation_date,
                "last_modified_date": last_modified_date,
                "tag": tag,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if labels is not UNSET:
            field_dict["labels"] = labels

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        creation_date = isoparse(d.pop("creation_date"))

        last_modified_date = isoparse(d.pop("last_modified_date"))

        tag = d.pop("tag")

        description = d.pop("description", UNSET)

        labels = []
        _labels = d.pop("labels", UNSET)
        for componentsschemas_labels_item_data in _labels or []:
            componentsschemas_labels_item = UUID(componentsschemas_labels_item_data)

            labels.append(componentsschemas_labels_item)

        hardware_metadata_version = cls(
            id=id,
            creation_date=creation_date,
            last_modified_date=last_modified_date,
            tag=tag,
            description=description,
            labels=labels,
        )

        hardware_metadata_version.additional_properties = d
        return hardware_metadata_version

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
