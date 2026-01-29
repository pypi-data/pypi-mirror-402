from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.custom_component_code import CustomComponentCode
    from ..models.custom_component_description_field_optional import CustomComponentDescriptionFieldOptional
    from ..models.custom_component_metadata import CustomComponentMetadata


T = TypeVar("T", bound="CustomComponentUpdate")


@_attrs_define
class CustomComponentUpdate:
    """
    Attributes:
        name (str):
        description (CustomComponentDescriptionFieldOptional):
        labels (Union[Unset, list[UUID]]):
        metadata (Union[Unset, CustomComponentMetadata]):
        code (Union[Unset, CustomComponentCode]):
    """

    name: str
    description: "CustomComponentDescriptionFieldOptional"
    labels: Union[Unset, list[UUID]] = UNSET
    metadata: Union[Unset, "CustomComponentMetadata"] = UNSET
    code: Union[Unset, "CustomComponentCode"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description.to_dict()

        labels: Union[Unset, list[str]] = UNSET
        if not isinstance(self.labels, Unset):
            labels = []
            for componentsschemas_labels_item_data in self.labels:
                componentsschemas_labels_item = str(componentsschemas_labels_item_data)
                labels.append(componentsschemas_labels_item)

        metadata: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        code: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.code, Unset):
            code = self.code.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
            }
        )
        if labels is not UNSET:
            field_dict["labels"] = labels
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if code is not UNSET:
            field_dict["code"] = code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_component_code import CustomComponentCode
        from ..models.custom_component_description_field_optional import CustomComponentDescriptionFieldOptional
        from ..models.custom_component_metadata import CustomComponentMetadata

        d = dict(src_dict)
        name = d.pop("name")

        description = CustomComponentDescriptionFieldOptional.from_dict(d.pop("description"))

        labels = []
        _labels = d.pop("labels", UNSET)
        for componentsschemas_labels_item_data in _labels or []:
            componentsschemas_labels_item = UUID(componentsschemas_labels_item_data)

            labels.append(componentsschemas_labels_item)

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, CustomComponentMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = CustomComponentMetadata.from_dict(_metadata)

        _code = d.pop("code", UNSET)
        code: Union[Unset, CustomComponentCode]
        if isinstance(_code, Unset):
            code = UNSET
        else:
            code = CustomComponentCode.from_dict(_code)

        custom_component_update = cls(
            name=name,
            description=description,
            labels=labels,
            metadata=metadata,
            code=code,
        )

        custom_component_update.additional_properties = d
        return custom_component_update

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
