from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.hardware_metadata_working_version import HardwareMetadataWorkingVersion


T = TypeVar("T", bound="HardwareList")


@_attrs_define
class HardwareList:
    """
    Attributes:
        hardware (list['HardwareMetadataWorkingVersion']):
    """

    hardware: list["HardwareMetadataWorkingVersion"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hardware = []
        for hardware_item_data in self.hardware:
            hardware_item = hardware_item_data.to_dict()
            hardware.append(hardware_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hardware": hardware,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hardware_metadata_working_version import HardwareMetadataWorkingVersion

        d = dict(src_dict)
        hardware = []
        _hardware = d.pop("hardware")
        for hardware_item_data in _hardware:
            hardware_item = HardwareMetadataWorkingVersion.from_dict(hardware_item_data)

            hardware.append(hardware_item)

        hardware_list = cls(
            hardware=hardware,
        )

        hardware_list.additional_properties = d
        return hardware_list

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
