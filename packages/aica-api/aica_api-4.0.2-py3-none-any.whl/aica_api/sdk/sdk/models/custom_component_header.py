import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.custom_component_description_field import CustomComponentDescriptionField
    from ..models.custom_component_version_header import CustomComponentVersionHeader


T = TypeVar("T", bound="CustomComponentHeader")


@_attrs_define
class CustomComponentHeader:
    """
    Attributes:
        id (UUID):
        description (CustomComponentDescriptionField):
        creation_date (datetime.datetime):
        last_modified_date (datetime.datetime):
        name (str):
        versions (list['CustomComponentVersionHeader']):
        labels (Union[Unset, list[UUID]]):
    """

    id: UUID
    description: "CustomComponentDescriptionField"
    creation_date: datetime.datetime
    last_modified_date: datetime.datetime
    name: str
    versions: list["CustomComponentVersionHeader"]
    labels: Union[Unset, list[UUID]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        description = self.description.to_dict()

        creation_date = self.creation_date.isoformat()

        last_modified_date = self.last_modified_date.isoformat()

        name = self.name

        versions = []
        for versions_item_data in self.versions:
            versions_item = versions_item_data.to_dict()
            versions.append(versions_item)

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
                "description": description,
                "creation_date": creation_date,
                "last_modified_date": last_modified_date,
                "name": name,
                "versions": versions,
            }
        )
        if labels is not UNSET:
            field_dict["labels"] = labels

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_component_description_field import CustomComponentDescriptionField
        from ..models.custom_component_version_header import CustomComponentVersionHeader

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        description = CustomComponentDescriptionField.from_dict(d.pop("description"))

        creation_date = isoparse(d.pop("creation_date"))

        last_modified_date = isoparse(d.pop("last_modified_date"))

        name = d.pop("name")

        versions = []
        _versions = d.pop("versions")
        for versions_item_data in _versions:
            versions_item = CustomComponentVersionHeader.from_dict(versions_item_data)

            versions.append(versions_item)

        labels = []
        _labels = d.pop("labels", UNSET)
        for componentsschemas_labels_item_data in _labels or []:
            componentsschemas_labels_item = UUID(componentsschemas_labels_item_data)

            labels.append(componentsschemas_labels_item)

        custom_component_header = cls(
            id=id,
            description=description,
            creation_date=creation_date,
            last_modified_date=last_modified_date,
            name=name,
            versions=versions,
            labels=labels,
        )

        custom_component_header.additional_properties = d
        return custom_component_header

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
