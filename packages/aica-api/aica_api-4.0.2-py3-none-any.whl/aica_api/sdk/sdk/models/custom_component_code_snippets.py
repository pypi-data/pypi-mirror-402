from collections.abc import Mapping
from typing import Any, Literal, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CustomComponentCodeSnippets")


@_attrs_define
class CustomComponentCodeSnippets:
    """
    Attributes:
        type_ (Literal['snippets']):
        globals_ (Union[Unset, str]):
        initialize (Union[Unset, str]):
        on_configure (Union[Unset, str]):
        on_execute (Union[Unset, str]):
        on_activate (Union[Unset, str]):
        on_deactivate (Union[Unset, str]):
        on_cleanup (Union[Unset, str]):
        on_step (Union[Unset, str]):
        on_validate_parameter (Union[Unset, str]):
        on_input (Union[Unset, str]):
        on_predicate (Union[Unset, str]):
        on_service (Union[Unset, str]):
        extra_methods (Union[Unset, str]):
    """

    type_: Literal["snippets"]
    globals_: Union[Unset, str] = UNSET
    initialize: Union[Unset, str] = UNSET
    on_configure: Union[Unset, str] = UNSET
    on_execute: Union[Unset, str] = UNSET
    on_activate: Union[Unset, str] = UNSET
    on_deactivate: Union[Unset, str] = UNSET
    on_cleanup: Union[Unset, str] = UNSET
    on_step: Union[Unset, str] = UNSET
    on_validate_parameter: Union[Unset, str] = UNSET
    on_input: Union[Unset, str] = UNSET
    on_predicate: Union[Unset, str] = UNSET
    on_service: Union[Unset, str] = UNSET
    extra_methods: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        globals_ = self.globals_

        initialize = self.initialize

        on_configure = self.on_configure

        on_execute = self.on_execute

        on_activate = self.on_activate

        on_deactivate = self.on_deactivate

        on_cleanup = self.on_cleanup

        on_step = self.on_step

        on_validate_parameter = self.on_validate_parameter

        on_input = self.on_input

        on_predicate = self.on_predicate

        on_service = self.on_service

        extra_methods = self.extra_methods

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if globals_ is not UNSET:
            field_dict["globals"] = globals_
        if initialize is not UNSET:
            field_dict["initialize"] = initialize
        if on_configure is not UNSET:
            field_dict["on_configure"] = on_configure
        if on_execute is not UNSET:
            field_dict["on_execute"] = on_execute
        if on_activate is not UNSET:
            field_dict["on_activate"] = on_activate
        if on_deactivate is not UNSET:
            field_dict["on_deactivate"] = on_deactivate
        if on_cleanup is not UNSET:
            field_dict["on_cleanup"] = on_cleanup
        if on_step is not UNSET:
            field_dict["on_step"] = on_step
        if on_validate_parameter is not UNSET:
            field_dict["on_validate_parameter"] = on_validate_parameter
        if on_input is not UNSET:
            field_dict["on_input"] = on_input
        if on_predicate is not UNSET:
            field_dict["on_predicate"] = on_predicate
        if on_service is not UNSET:
            field_dict["on_service"] = on_service
        if extra_methods is not UNSET:
            field_dict["extra_methods"] = extra_methods

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = cast(Literal["snippets"], d.pop("type"))
        if type_ != "snippets":
            raise ValueError(f"type must match const 'snippets', got '{type_}'")

        globals_ = d.pop("globals", UNSET)

        initialize = d.pop("initialize", UNSET)

        on_configure = d.pop("on_configure", UNSET)

        on_execute = d.pop("on_execute", UNSET)

        on_activate = d.pop("on_activate", UNSET)

        on_deactivate = d.pop("on_deactivate", UNSET)

        on_cleanup = d.pop("on_cleanup", UNSET)

        on_step = d.pop("on_step", UNSET)

        on_validate_parameter = d.pop("on_validate_parameter", UNSET)

        on_input = d.pop("on_input", UNSET)

        on_predicate = d.pop("on_predicate", UNSET)

        on_service = d.pop("on_service", UNSET)

        extra_methods = d.pop("extra_methods", UNSET)

        custom_component_code_snippets = cls(
            type_=type_,
            globals_=globals_,
            initialize=initialize,
            on_configure=on_configure,
            on_execute=on_execute,
            on_activate=on_activate,
            on_deactivate=on_deactivate,
            on_cleanup=on_cleanup,
            on_step=on_step,
            on_validate_parameter=on_validate_parameter,
            on_input=on_input,
            on_predicate=on_predicate,
            on_service=on_service,
            extra_methods=extra_methods,
        )

        custom_component_code_snippets.additional_properties = d
        return custom_component_code_snippets

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
