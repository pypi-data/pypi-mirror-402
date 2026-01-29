from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.custom_component_parameter_type import CustomComponentParameterType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CustomComponentParameter")


@_attrs_define
class CustomComponentParameter:
    """
    Attributes:
        name (str):
        description (str):
        type_ (CustomComponentParameterType):
        default (Union[Unset, str]):
    """

    name: str
    description: str
    type_: CustomComponentParameterType
    default: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        default = self.default

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
            }
        )
        if default is not UNSET:
            field_dict["default"] = default

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = CustomComponentParameterType(d.pop("type"))

        default = d.pop("default", UNSET)

        custom_component_parameter = cls(
            name=name,
            description=description,
            type_=type_,
            default=default,
        )

        custom_component_parameter.additional_properties = d
        return custom_component_parameter

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
