from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.custom_component_code import CustomComponentCode
    from ..models.custom_component_description_field import CustomComponentDescriptionField
    from ..models.custom_component_metadata import CustomComponentMetadata


T = TypeVar("T", bound="CustomComponentCreate")


@_attrs_define
class CustomComponentCreate:
    """
    Attributes:
        description (CustomComponentDescriptionField):
        metadata (CustomComponentMetadata):
        code (CustomComponentCode):
        name (str):
        labels (Union[Unset, list[UUID]]):
    """

    description: "CustomComponentDescriptionField"
    metadata: "CustomComponentMetadata"
    code: "CustomComponentCode"
    name: str
    labels: Union[Unset, list[UUID]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        description = self.description.to_dict()

        metadata = self.metadata.to_dict()

        code = self.code.to_dict()

        name = self.name

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
                "description": description,
                "metadata": metadata,
                "code": code,
                "name": name,
            }
        )
        if labels is not UNSET:
            field_dict["labels"] = labels

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_component_code import CustomComponentCode
        from ..models.custom_component_description_field import CustomComponentDescriptionField
        from ..models.custom_component_metadata import CustomComponentMetadata

        d = dict(src_dict)
        description = CustomComponentDescriptionField.from_dict(d.pop("description"))

        metadata = CustomComponentMetadata.from_dict(d.pop("metadata"))

        code = CustomComponentCode.from_dict(d.pop("code"))

        name = d.pop("name")

        labels = []
        _labels = d.pop("labels", UNSET)
        for componentsschemas_labels_item_data in _labels or []:
            componentsschemas_labels_item = UUID(componentsschemas_labels_item_data)

            labels.append(componentsschemas_labels_item)

        custom_component_create = cls(
            description=description,
            metadata=metadata,
            code=code,
            name=name,
            labels=labels,
        )

        custom_component_create.additional_properties = d
        return custom_component_create

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
