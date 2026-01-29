import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="HardwareAsset")


@_attrs_define
class HardwareAsset:
    """
    Attributes:
        id (UUID):
        name (str):
        creation_date (datetime.datetime):
        last_modified_date (datetime.datetime):
    """

    id: UUID
    name: str
    creation_date: datetime.datetime
    last_modified_date: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        creation_date = self.creation_date.isoformat()

        last_modified_date = self.last_modified_date.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "creation_date": creation_date,
                "last_modified_date": last_modified_date,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        creation_date = isoparse(d.pop("creation_date"))

        last_modified_date = isoparse(d.pop("last_modified_date"))

        hardware_asset = cls(
            id=id,
            name=name,
            creation_date=creation_date,
            last_modified_date=last_modified_date,
        )

        hardware_asset.additional_properties = d
        return hardware_asset

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
