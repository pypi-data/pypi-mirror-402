from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.custom_component_code_snippets import CustomComponentCodeSnippets
    from ..models.custom_component_metadata import CustomComponentMetadata


T = TypeVar("T", bound="CustomComponentWithSnippets")


@_attrs_define
class CustomComponentWithSnippets:
    """
    Attributes:
        name (str):
        metadata (CustomComponentMetadata):
        code (CustomComponentCodeSnippets):
    """

    name: str
    metadata: "CustomComponentMetadata"
    code: "CustomComponentCodeSnippets"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        metadata = self.metadata.to_dict()

        code = self.code.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "metadata": metadata,
                "code": code,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_component_code_snippets import CustomComponentCodeSnippets
        from ..models.custom_component_metadata import CustomComponentMetadata

        d = dict(src_dict)
        name = d.pop("name")

        metadata = CustomComponentMetadata.from_dict(d.pop("metadata"))

        code = CustomComponentCodeSnippets.from_dict(d.pop("code"))

        custom_component_with_snippets = cls(
            name=name,
            metadata=metadata,
            code=code,
        )

        custom_component_with_snippets.additional_properties = d
        return custom_component_with_snippets

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
