from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SwitchControllersRequest")


@_attrs_define
class SwitchControllersRequest:
    """
    Attributes:
        hardware (str): The name of the hardware to reference
        activate (list[str]): List of controllers to activate
        deactivate (list[str]): List of controllers to deactivate
    """

    hardware: str
    activate: list[str]
    deactivate: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hardware = self.hardware

        activate = self.activate

        deactivate = self.deactivate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hardware": hardware,
                "activate": activate,
                "deactivate": deactivate,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        hardware = d.pop("hardware")

        activate = cast(list[str], d.pop("activate"))

        deactivate = cast(list[str], d.pop("deactivate"))

        switch_controllers_request = cls(
            hardware=hardware,
            activate=activate,
            deactivate=deactivate,
        )

        switch_controllers_request.additional_properties = d
        return switch_controllers_request

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
