from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.auth_status import AuthStatus


T = TypeVar("T", bound="CloudStatus")


@_attrs_define
class CloudStatus:
    """
    Attributes:
        auth (AuthStatus):
        online (bool):
    """

    auth: "AuthStatus"
    online: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auth = self.auth.to_dict()

        online = self.online

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "auth": auth,
                "online": online,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.auth_status import AuthStatus

        d = dict(src_dict)
        auth = AuthStatus.from_dict(d.pop("auth"))

        online = d.pop("online")

        cloud_status = cls(
            auth=auth,
            online=online,
        )

        cloud_status.additional_properties = d
        return cloud_status

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
