from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.application_metadata_working_version import ApplicationMetadataWorkingVersion


T = TypeVar("T", bound="ApplicationList")


@_attrs_define
class ApplicationList:
    """
    Attributes:
        applications (list['ApplicationMetadataWorkingVersion']):
    """

    applications: list["ApplicationMetadataWorkingVersion"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        applications = []
        for applications_item_data in self.applications:
            applications_item = applications_item_data.to_dict()
            applications.append(applications_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "applications": applications,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.application_metadata_working_version import ApplicationMetadataWorkingVersion

        d = dict(src_dict)
        applications = []
        _applications = d.pop("applications")
        for applications_item_data in _applications:
            applications_item = ApplicationMetadataWorkingVersion.from_dict(applications_item_data)

            applications.append(applications_item)

        application_list = cls(
            applications=applications,
        )

        application_list.additional_properties = d
        return application_list

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
