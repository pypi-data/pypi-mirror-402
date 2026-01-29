from enum import Enum


class CustomComponentMetadataInherits(str, Enum):
    MODULO_COMPONENTSCOMPONENT = "modulo_components::Component"
    MODULO_COMPONENTSLIFECYCLECOMPONENT = "modulo_components::LifecycleComponent"

    def __str__(self) -> str:
        return str(self.value)
