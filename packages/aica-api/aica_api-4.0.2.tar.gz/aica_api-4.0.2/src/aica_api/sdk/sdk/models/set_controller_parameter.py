from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SetControllerParameter")


@_attrs_define
class SetControllerParameter:
    """
    Attributes:
        hardware (str): The name of the hardware to reference
        controller (str): The name of the controller to reference
        parameter (str): The name of the parameter to set
        value (Union[bool, float, int, list[bool], list[float], list[int], list[str], str]):
    """

    hardware: str
    controller: str
    parameter: str
    value: Union[bool, float, int, list[bool], list[float], list[int], list[str], str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hardware = self.hardware

        controller = self.controller

        parameter = self.parameter

        value: Union[bool, float, int, list[bool], list[float], list[int], list[str], str]
        if isinstance(self.value, list):
            value = self.value

        elif isinstance(self.value, list):
            value = self.value

        elif isinstance(self.value, list):
            value = self.value

        elif isinstance(self.value, list):
            value = self.value

        else:
            value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hardware": hardware,
                "controller": controller,
                "parameter": parameter,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        hardware = d.pop("hardware")

        controller = d.pop("controller")

        parameter = d.pop("parameter")

        def _parse_value(data: object) -> Union[bool, float, int, list[bool], list[float], list[int], list[str], str]:
            try:
                if not isinstance(data, list):
                    raise TypeError()
                value_type_4 = cast(list[bool], data)

                return value_type_4
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, list):
                    raise TypeError()
                value_type_5 = cast(list[int], data)

                return value_type_5
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, list):
                    raise TypeError()
                value_type_6 = cast(list[float], data)

                return value_type_6
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, list):
                    raise TypeError()
                value_type_7 = cast(list[str], data)

                return value_type_7
            except:  # noqa: E722
                pass
            return cast(Union[bool, float, int, list[bool], list[float], list[int], list[str], str], data)

        value = _parse_value(d.pop("value"))

        set_controller_parameter = cls(
            hardware=hardware,
            controller=controller,
            parameter=parameter,
            value=value,
        )

        set_controller_parameter.additional_properties = d
        return set_controller_parameter

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
