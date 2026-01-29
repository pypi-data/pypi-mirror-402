from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.hardware_asset import HardwareAsset


T = TypeVar("T", bound="HardwareContent")


@_attrs_define
class HardwareContent:
    """
    Attributes:
        urdf (str):
        assets (list['HardwareAsset']):
    """

    urdf: str
    assets: list["HardwareAsset"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        urdf = self.urdf

        assets = []
        for assets_item_data in self.assets:
            assets_item = assets_item_data.to_dict()
            assets.append(assets_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "urdf": urdf,
                "assets": assets,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hardware_asset import HardwareAsset

        d = dict(src_dict)
        urdf = d.pop("urdf")

        assets = []
        _assets = d.pop("assets")
        for assets_item_data in _assets:
            assets_item = HardwareAsset.from_dict(assets_item_data)

            assets.append(assets_item)

        hardware_content = cls(
            urdf=urdf,
            assets=assets,
        )

        hardware_content.additional_properties = d
        return hardware_content

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
