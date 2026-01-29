from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.licensing_status_signed_packages import LicensingStatusSignedPackages


T = TypeVar("T", bound="LicensingStatus")


@_attrs_define
class LicensingStatus:
    """
    Attributes:
        online (bool):
        signed_packages (LicensingStatusSignedPackages):
        entitlements (list[str]):
    """

    online: bool
    signed_packages: "LicensingStatusSignedPackages"
    entitlements: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        online = self.online

        signed_packages = self.signed_packages.to_dict()

        entitlements = self.entitlements

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "online": online,
                "signed_packages": signed_packages,
                "entitlements": entitlements,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.licensing_status_signed_packages import LicensingStatusSignedPackages

        d = dict(src_dict)
        online = d.pop("online")

        signed_packages = LicensingStatusSignedPackages.from_dict(d.pop("signed_packages"))

        entitlements = cast(list[str], d.pop("entitlements"))

        licensing_status = cls(
            online=online,
            signed_packages=signed_packages,
            entitlements=entitlements,
        )

        licensing_status.additional_properties = d
        return licensing_status

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
