from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.custom_component_metadata_inherits import CustomComponentMetadataInherits
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.custom_component_input import CustomComponentInput
    from ..models.custom_component_output import CustomComponentOutput
    from ..models.custom_component_parameter import CustomComponentParameter
    from ..models.custom_component_predicate import CustomComponentPredicate
    from ..models.custom_component_service import CustomComponentService


T = TypeVar("T", bound="CustomComponentMetadata")


@_attrs_define
class CustomComponentMetadata:
    """
    Attributes:
        inherits (CustomComponentMetadataInherits):
        parameters (Union[Unset, list['CustomComponentParameter']]):
        predicates (Union[Unset, list['CustomComponentPredicate']]):
        services (Union[Unset, list['CustomComponentService']]):
        inputs (Union[Unset, list['CustomComponentInput']]):
        outputs (Union[Unset, list['CustomComponentOutput']]):
    """

    inherits: CustomComponentMetadataInherits
    parameters: Union[Unset, list["CustomComponentParameter"]] = UNSET
    predicates: Union[Unset, list["CustomComponentPredicate"]] = UNSET
    services: Union[Unset, list["CustomComponentService"]] = UNSET
    inputs: Union[Unset, list["CustomComponentInput"]] = UNSET
    outputs: Union[Unset, list["CustomComponentOutput"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        inherits = self.inherits.value

        parameters: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = []
            for parameters_item_data in self.parameters:
                parameters_item = parameters_item_data.to_dict()
                parameters.append(parameters_item)

        predicates: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.predicates, Unset):
            predicates = []
            for predicates_item_data in self.predicates:
                predicates_item = predicates_item_data.to_dict()
                predicates.append(predicates_item)

        services: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.services, Unset):
            services = []
            for services_item_data in self.services:
                services_item = services_item_data.to_dict()
                services.append(services_item)

        inputs: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.inputs, Unset):
            inputs = []
            for inputs_item_data in self.inputs:
                inputs_item = inputs_item_data.to_dict()
                inputs.append(inputs_item)

        outputs: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.outputs, Unset):
            outputs = []
            for outputs_item_data in self.outputs:
                outputs_item = outputs_item_data.to_dict()
                outputs.append(outputs_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "inherits": inherits,
            }
        )
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if predicates is not UNSET:
            field_dict["predicates"] = predicates
        if services is not UNSET:
            field_dict["services"] = services
        if inputs is not UNSET:
            field_dict["inputs"] = inputs
        if outputs is not UNSET:
            field_dict["outputs"] = outputs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_component_input import CustomComponentInput
        from ..models.custom_component_output import CustomComponentOutput
        from ..models.custom_component_parameter import CustomComponentParameter
        from ..models.custom_component_predicate import CustomComponentPredicate
        from ..models.custom_component_service import CustomComponentService

        d = dict(src_dict)
        inherits = CustomComponentMetadataInherits(d.pop("inherits"))

        parameters = []
        _parameters = d.pop("parameters", UNSET)
        for parameters_item_data in _parameters or []:
            parameters_item = CustomComponentParameter.from_dict(parameters_item_data)

            parameters.append(parameters_item)

        predicates = []
        _predicates = d.pop("predicates", UNSET)
        for predicates_item_data in _predicates or []:
            predicates_item = CustomComponentPredicate.from_dict(predicates_item_data)

            predicates.append(predicates_item)

        services = []
        _services = d.pop("services", UNSET)
        for services_item_data in _services or []:
            services_item = CustomComponentService.from_dict(services_item_data)

            services.append(services_item)

        inputs = []
        _inputs = d.pop("inputs", UNSET)
        for inputs_item_data in _inputs or []:
            inputs_item = CustomComponentInput.from_dict(inputs_item_data)

            inputs.append(inputs_item)

        outputs = []
        _outputs = d.pop("outputs", UNSET)
        for outputs_item_data in _outputs or []:
            outputs_item = CustomComponentOutput.from_dict(outputs_item_data)

            outputs.append(outputs_item)

        custom_component_metadata = cls(
            inherits=inherits,
            parameters=parameters,
            predicates=predicates,
            services=services,
            inputs=inputs,
            outputs=outputs,
        )

        custom_component_metadata.additional_properties = d
        return custom_component_metadata

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
