from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TransformFrame")


@_attrs_define
class TransformFrame:
    """
    Attributes:
        parent (str):
        broadcaster (str):
        rate (float): The rate at which the transform is broadcasted, in Hz.
        most_recent_transform (float): A timestamp represented as a floating point number, where the integer part is
            seconds and the fractional part is a fractional second.
        oldest_transform (float): A timestamp represented as a floating point number, where the integer part is seconds
            and the fractional part is a fractional second.
        buffer_length (float): The length of the transform buffer, in seconds.
        transform_delay (Union[Unset, float]): The delay of the transform, in seconds.
    """

    parent: str
    broadcaster: str
    rate: float
    most_recent_transform: float
    oldest_transform: float
    buffer_length: float
    transform_delay: Union[Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        parent = self.parent

        broadcaster = self.broadcaster

        rate = self.rate

        most_recent_transform = self.most_recent_transform

        oldest_transform = self.oldest_transform

        buffer_length = self.buffer_length

        transform_delay = self.transform_delay

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "parent": parent,
                "broadcaster": broadcaster,
                "rate": rate,
                "most_recent_transform": most_recent_transform,
                "oldest_transform": oldest_transform,
                "buffer_length": buffer_length,
            }
        )
        if transform_delay is not UNSET:
            field_dict["transform_delay"] = transform_delay

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        parent = d.pop("parent")

        broadcaster = d.pop("broadcaster")

        rate = d.pop("rate")

        most_recent_transform = d.pop("most_recent_transform")

        oldest_transform = d.pop("oldest_transform")

        buffer_length = d.pop("buffer_length")

        transform_delay = d.pop("transform_delay", UNSET)

        transform_frame = cls(
            parent=parent,
            broadcaster=broadcaster,
            rate=rate,
            most_recent_transform=most_recent_transform,
            oldest_transform=oldest_transform,
            buffer_length=buffer_length,
            transform_delay=transform_delay,
        )

        transform_frame.additional_properties = d
        return transform_frame

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
