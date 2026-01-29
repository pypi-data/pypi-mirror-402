from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.label import Label


T = TypeVar("T", bound="AllLabels")


@_attrs_define
class AllLabels:
    """
    Attributes:
        labels (list['Label']):
    """

    labels: list["Label"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        labels = []
        for componentsschemas_label_list_item_data in self.labels:
            componentsschemas_label_list_item = componentsschemas_label_list_item_data.to_dict()
            labels.append(componentsschemas_label_list_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "labels": labels,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.label import Label

        d = dict(src_dict)
        labels = []
        _labels = d.pop("labels")
        for componentsschemas_label_list_item_data in _labels:
            componentsschemas_label_list_item = Label.from_dict(componentsschemas_label_list_item_data)

            labels.append(componentsschemas_label_list_item)

        all_labels = cls(
            labels=labels,
        )

        all_labels.additional_properties = d
        return all_labels

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
