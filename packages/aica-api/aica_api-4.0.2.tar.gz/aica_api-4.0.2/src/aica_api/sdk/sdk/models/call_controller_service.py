from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CallControllerService")


@_attrs_define
class CallControllerService:
    """
    Attributes:
        hardware (str): The name of the hardware to reference
        controller (str): The name of the controller to reference
        service (str): The name of the service to call
        payload (Union[Unset, str]): The payload to send to the service
    """

    hardware: str
    controller: str
    service: str
    payload: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hardware = self.hardware

        controller = self.controller

        service = self.service

        payload = self.payload

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hardware": hardware,
                "controller": controller,
                "service": service,
            }
        )
        if payload is not UNSET:
            field_dict["payload"] = payload

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        hardware = d.pop("hardware")

        controller = d.pop("controller")

        service = d.pop("service")

        payload = d.pop("payload", UNSET)

        call_controller_service = cls(
            hardware=hardware,
            controller=controller,
            service=service,
            payload=payload,
        )

        call_controller_service.additional_properties = d
        return call_controller_service

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
