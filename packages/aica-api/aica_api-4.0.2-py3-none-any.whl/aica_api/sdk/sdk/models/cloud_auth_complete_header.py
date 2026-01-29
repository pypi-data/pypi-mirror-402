from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.cloud_auth_complete_header_version import CloudAuthCompleteHeaderVersion

T = TypeVar("T", bound="CloudAuthCompleteHeader")


@_attrs_define
class CloudAuthCompleteHeader:
    """
    Attributes:
        version (CloudAuthCompleteHeaderVersion): The formatting version (expected to be 1 at the moment)
        success (bool): Whether the authorization was successful
    """

    version: CloudAuthCompleteHeaderVersion
    success: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        version = self.version.value

        success = self.success

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "version": version,
                "success": success,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        version = CloudAuthCompleteHeaderVersion(d.pop("version"))

        success = d.pop("success")

        cloud_auth_complete_header = cls(
            version=version,
            success=success,
        )

        cloud_auth_complete_header.additional_properties = d
        return cloud_auth_complete_header

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
