import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.custom_component_code import CustomComponentCode
    from ..models.custom_component_description_field import CustomComponentDescriptionField
    from ..models.custom_component_header import CustomComponentHeader
    from ..models.custom_component_metadata import CustomComponentMetadata


T = TypeVar("T", bound="CustomComponentVersion")


@_attrs_define
class CustomComponentVersion:
    """
    Attributes:
        id (UUID):
        description (CustomComponentDescriptionField):
        creation_date (datetime.datetime):
        last_modified_date (datetime.datetime):
        tag (str): Name of the version
        metadata (CustomComponentMetadata):
        code (CustomComponentCode):
        component (CustomComponentHeader):
        labels (Union[Unset, list[UUID]]):
    """

    id: UUID
    description: "CustomComponentDescriptionField"
    creation_date: datetime.datetime
    last_modified_date: datetime.datetime
    tag: str
    metadata: "CustomComponentMetadata"
    code: "CustomComponentCode"
    component: "CustomComponentHeader"
    labels: Union[Unset, list[UUID]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        description = self.description.to_dict()

        creation_date = self.creation_date.isoformat()

        last_modified_date = self.last_modified_date.isoformat()

        tag = self.tag

        metadata = self.metadata.to_dict()

        code = self.code.to_dict()

        component = self.component.to_dict()

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
                "tag": tag,
                "metadata": metadata,
                "code": code,
                "component": component,
            }
        )
        if labels is not UNSET:
            field_dict["labels"] = labels

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_component_code import CustomComponentCode
        from ..models.custom_component_description_field import CustomComponentDescriptionField
        from ..models.custom_component_header import CustomComponentHeader
        from ..models.custom_component_metadata import CustomComponentMetadata

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        description = CustomComponentDescriptionField.from_dict(d.pop("description"))

        creation_date = isoparse(d.pop("creation_date"))

        last_modified_date = isoparse(d.pop("last_modified_date"))

        tag = d.pop("tag")

        metadata = CustomComponentMetadata.from_dict(d.pop("metadata"))

        code = CustomComponentCode.from_dict(d.pop("code"))

        component = CustomComponentHeader.from_dict(d.pop("component"))

        labels = []
        _labels = d.pop("labels", UNSET)
        for componentsschemas_labels_item_data in _labels or []:
            componentsschemas_labels_item = UUID(componentsschemas_labels_item_data)

            labels.append(componentsschemas_labels_item)

        custom_component_version = cls(
            id=id,
            description=description,
            creation_date=creation_date,
            last_modified_date=last_modified_date,
            tag=tag,
            metadata=metadata,
            code=code,
            component=component,
            labels=labels,
        )

        custom_component_version.additional_properties = d
        return custom_component_version

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
