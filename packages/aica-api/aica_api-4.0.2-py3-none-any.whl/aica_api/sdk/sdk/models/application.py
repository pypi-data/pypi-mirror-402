import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.application_metadata_version import ApplicationMetadataVersion
    from ..models.cloud_application import CloudApplication


T = TypeVar("T", bound="Application")


@_attrs_define
class Application:
    """
    Attributes:
        id (UUID):
        creation_date (datetime.datetime):
        last_modified_date (datetime.datetime):
        name (str):
        versions (list['ApplicationMetadataVersion']):
        yaml (str):
        description (Union[Unset, str]):
        labels (Union[Unset, list[UUID]]):
        cloud (Union[Unset, CloudApplication]):
    """

    id: UUID
    creation_date: datetime.datetime
    last_modified_date: datetime.datetime
    name: str
    versions: list["ApplicationMetadataVersion"]
    yaml: str
    description: Union[Unset, str] = UNSET
    labels: Union[Unset, list[UUID]] = UNSET
    cloud: Union[Unset, "CloudApplication"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        creation_date = self.creation_date.isoformat()

        last_modified_date = self.last_modified_date.isoformat()

        name = self.name

        versions = []
        for versions_item_data in self.versions:
            versions_item = versions_item_data.to_dict()
            versions.append(versions_item)

        yaml = self.yaml

        description = self.description

        labels: Union[Unset, list[str]] = UNSET
        if not isinstance(self.labels, Unset):
            labels = []
            for componentsschemas_labels_item_data in self.labels:
                componentsschemas_labels_item = str(componentsschemas_labels_item_data)
                labels.append(componentsschemas_labels_item)

        cloud: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.cloud, Unset):
            cloud = self.cloud.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "creation_date": creation_date,
                "last_modified_date": last_modified_date,
                "name": name,
                "versions": versions,
                "yaml": yaml,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if labels is not UNSET:
            field_dict["labels"] = labels
        if cloud is not UNSET:
            field_dict["cloud"] = cloud

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.application_metadata_version import ApplicationMetadataVersion
        from ..models.cloud_application import CloudApplication

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        creation_date = isoparse(d.pop("creation_date"))

        last_modified_date = isoparse(d.pop("last_modified_date"))

        name = d.pop("name")

        versions = []
        _versions = d.pop("versions")
        for versions_item_data in _versions:
            versions_item = ApplicationMetadataVersion.from_dict(versions_item_data)

            versions.append(versions_item)

        yaml = d.pop("yaml")

        description = d.pop("description", UNSET)

        labels = []
        _labels = d.pop("labels", UNSET)
        for componentsschemas_labels_item_data in _labels or []:
            componentsschemas_labels_item = UUID(componentsschemas_labels_item_data)

            labels.append(componentsschemas_labels_item)

        _cloud = d.pop("cloud", UNSET)
        cloud: Union[Unset, CloudApplication]
        if isinstance(_cloud, Unset):
            cloud = UNSET
        else:
            cloud = CloudApplication.from_dict(_cloud)

        application = cls(
            id=id,
            creation_date=creation_date,
            last_modified_date=last_modified_date,
            name=name,
            versions=versions,
            yaml=yaml,
            description=description,
            labels=labels,
            cloud=cloud,
        )

        application.additional_properties = d
        return application

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
