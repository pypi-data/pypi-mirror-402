from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.sequence_lifecycle_transition_transition import SequenceLifecycleTransitionTransition

T = TypeVar("T", bound="SequenceLifecycleTransition")


@_attrs_define
class SequenceLifecycleTransition:
    """
    Attributes:
        sequence (str): The name of the sequence to transition
        transition (SequenceLifecycleTransitionTransition): The transition to perform on the sequence
    """

    sequence: str
    transition: SequenceLifecycleTransitionTransition
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        sequence = self.sequence

        transition = self.transition.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sequence": sequence,
                "transition": transition,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sequence = d.pop("sequence")

        transition = SequenceLifecycleTransitionTransition(d.pop("transition"))

        sequence_lifecycle_transition = cls(
            sequence=sequence,
            transition=transition,
        )

        sequence_lifecycle_transition.additional_properties = d
        return sequence_lifecycle_transition

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
