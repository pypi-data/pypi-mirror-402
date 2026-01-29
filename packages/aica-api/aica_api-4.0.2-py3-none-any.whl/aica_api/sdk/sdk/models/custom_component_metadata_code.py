from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.custom_component_code import CustomComponentCode
    from ..models.custom_component_metadata import CustomComponentMetadata


T = TypeVar("T", bound="CustomComponentMetadataCode")


@_attrs_define
class CustomComponentMetadataCode:
    """
    Attributes:
        metadata (CustomComponentMetadata):
        code (CustomComponentCode):
    """

    metadata: "CustomComponentMetadata"
    code: "CustomComponentCode"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metadata = self.metadata.to_dict()

        code = self.code.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "metadata": metadata,
                "code": code,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_component_code import CustomComponentCode
        from ..models.custom_component_metadata import CustomComponentMetadata

        d = dict(src_dict)
        metadata = CustomComponentMetadata.from_dict(d.pop("metadata"))

        code = CustomComponentCode.from_dict(d.pop("code"))

        custom_component_metadata_code = cls(
            metadata=metadata,
            code=code,
        )

        custom_component_metadata_code.additional_properties = d
        return custom_component_metadata_code

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
