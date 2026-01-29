from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.component_lifecycle_transition_transition import ComponentLifecycleTransitionTransition

T = TypeVar("T", bound="ComponentLifecycleTransition")


@_attrs_define
class ComponentLifecycleTransition:
    """
    Attributes:
        component (str): The name of the component to reference
        transition (ComponentLifecycleTransitionTransition): The lifecycle transition to trigger
    """

    component: str
    transition: ComponentLifecycleTransitionTransition
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        component = self.component

        transition = self.transition.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "component": component,
                "transition": transition,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        component = d.pop("component")

        transition = ComponentLifecycleTransitionTransition(d.pop("transition"))

        component_lifecycle_transition = cls(
            component=component,
            transition=transition,
        )

        component_lifecycle_transition.additional_properties = d
        return component_lifecycle_transition

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
