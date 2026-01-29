from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HardwareCreateVersion")


@_attrs_define
class HardwareCreateVersion:
    """
    Attributes:
        tag (str):
        urdf (str):
        description (Union[Unset, str]):
        labels (Union[Unset, list[UUID]]):
        assets (Union[Unset, list[UUID]]):
    """

    tag: str
    urdf: str
    description: Union[Unset, str] = UNSET
    labels: Union[Unset, list[UUID]] = UNSET
    assets: Union[Unset, list[UUID]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tag = self.tag

        urdf = self.urdf

        description = self.description

        labels: Union[Unset, list[str]] = UNSET
        if not isinstance(self.labels, Unset):
            labels = []
            for componentsschemas_labels_item_data in self.labels:
                componentsschemas_labels_item = str(componentsschemas_labels_item_data)
                labels.append(componentsschemas_labels_item)

        assets: Union[Unset, list[str]] = UNSET
        if not isinstance(self.assets, Unset):
            assets = []
            for assets_item_data in self.assets:
                assets_item = str(assets_item_data)
                assets.append(assets_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tag": tag,
                "urdf": urdf,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if labels is not UNSET:
            field_dict["labels"] = labels
        if assets is not UNSET:
            field_dict["assets"] = assets

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        tag = d.pop("tag")

        urdf = d.pop("urdf")

        description = d.pop("description", UNSET)

        labels = []
        _labels = d.pop("labels", UNSET)
        for componentsschemas_labels_item_data in _labels or []:
            componentsschemas_labels_item = UUID(componentsschemas_labels_item_data)

            labels.append(componentsschemas_labels_item)

        assets = []
        _assets = d.pop("assets", UNSET)
        for assets_item_data in _assets or []:
            assets_item = UUID(assets_item_data)

            assets.append(assets_item)

        hardware_create_version = cls(
            tag=tag,
            urdf=urdf,
            description=description,
            labels=labels,
            assets=assets,
        )

        hardware_create_version.additional_properties = d
        return hardware_create_version

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
