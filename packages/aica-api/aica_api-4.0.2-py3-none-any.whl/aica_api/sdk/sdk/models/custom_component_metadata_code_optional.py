from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.custom_component_code import CustomComponentCode
    from ..models.custom_component_metadata import CustomComponentMetadata


T = TypeVar("T", bound="CustomComponentMetadataCodeOptional")


@_attrs_define
class CustomComponentMetadataCodeOptional:
    """
    Attributes:
        metadata (Union[Unset, CustomComponentMetadata]):
        code (Union[Unset, CustomComponentCode]):
    """

    metadata: Union[Unset, "CustomComponentMetadata"] = UNSET
    code: Union[Unset, "CustomComponentCode"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metadata: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        code: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.code, Unset):
            code = self.code.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if code is not UNSET:
            field_dict["code"] = code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_component_code import CustomComponentCode
        from ..models.custom_component_metadata import CustomComponentMetadata

        d = dict(src_dict)
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

        custom_component_metadata_code_optional = cls(
            metadata=metadata,
            code=code,
        )

        custom_component_metadata_code_optional.additional_properties = d
        return custom_component_metadata_code_optional

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
