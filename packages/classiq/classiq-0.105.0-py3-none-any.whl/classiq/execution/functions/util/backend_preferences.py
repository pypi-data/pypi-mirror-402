from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from classiq.interface.backend.backend_preferences import (
    AliceBobBackendPreferences,
    AQTBackendPreferences,
    AwsBackendPreferences,
    AzureBackendPreferences,
    AzureCredential,
    BackendPreferencesTypes,
    ClassiqBackendPreferences,
    GCPBackendPreferences,
    IBMBackendPreferences,
    IntelBackendPreferences,
    IonqBackendPreferences,
)
from classiq.interface.backend.provider_config.provider_config import ProviderConfig
from classiq.interface.backend.provider_config.providers.alice_bob import AliceBobConfig
from classiq.interface.backend.provider_config.providers.aqt import AQTConfig
from classiq.interface.backend.provider_config.providers.azure import AzureConfig
from classiq.interface.backend.provider_config.providers.braket import BraketConfig
from classiq.interface.backend.provider_config.providers.ibm import IBMConfig
from classiq.interface.backend.provider_config.providers.ionq import IonQConfig
from classiq.interface.backend.quantum_backend_providers import (
    ClassiqNvidiaBackendNames,
    ClassiqSimulatorBackendNames,
)
from classiq.interface.hardware import Provider

from classiq.execution.functions.util.parse_provider_backend import (
    _PROVIDER_TO_CANONICAL_NAME,
    _parse_provider_backend,
)


@dataclass
class _ProviderConfigToBackendPrefSpec:
    backend_preferences_class: type[BackendPreferencesTypes]
    config_class: type[ProviderConfig] | None = None
    # Maps the config dict (either passed in directly or dumped from config class) to a
    # dict that we can load into the given BackendPreferences class. This is in case
    # we need to rename fields or change structure.
    config_dict_to_backend_preferences_dict: (
        Callable[[dict[str, Any]], dict[str, Any]] | None
    ) = None
    # Maps from SDK names to names our backend recognizes, raising a useful error
    # if the name is unrecognized.
    backend_name_mapper: Callable[[str], str] | None = None


def _classiq_backend_name_mapper(backend_name: str) -> str:
    backend_name = backend_name.lower()
    if backend_name in [
        ClassiqSimulatorBackendNames.SIMULATOR,
        ClassiqSimulatorBackendNames.SIMULATOR_MATRIX_PRODUCT_STATE,
        ClassiqSimulatorBackendNames.SIMULATOR_DENSITY_MATRIX,
    ]:
        return backend_name
    if backend_name == "nvidia_simulator":
        return ClassiqNvidiaBackendNames.SIMULATOR
    if any(keyword in backend_name for keyword in ["gpu", "nvidia"]):
        suggested_backend_name = "nvidia_simulator"
    else:
        suggested_backend_name = "simulator"
    raise ValueError(
        f"Unsupported backend name {backend_name}. Did you mean '{suggested_backend_name}'?"
    )


def _ibm_backend_name_mapper(backend_name: str) -> str:
    ibm_prefix: Literal["ibm_"] = "ibm_"
    backend_name = backend_name.lower()
    if backend_name.startswith(ibm_prefix):
        backend_name_no_prefix = backend_name.removeprefix(ibm_prefix)
        raise ValueError(
            f"IBM backend names shouldn't start with ibm_. Try 'ibm/{backend_name_no_prefix}'."
        )
    return ibm_prefix + backend_name


def _azure_config_dict_to_backend_preferences_dict(
    config_dict: dict[str, Any],
) -> dict[str, Any]:
    if "location" not in config_dict:
        raise ValueError("Azure config must have 'location' property")
    credentials = None
    if all(
        config_dict.get(key) is not None
        for key in ["tenant_id", "client_id", "client_secret", "resource_id"]
    ):
        credentials = AzureCredential.model_validate(
            {
                "tenant_id": config_dict["tenant_id"],
                "client_id": config_dict["client_id"],
                "client_secret": config_dict["client_secret"],
                "resource_id": config_dict["resource_id"],
            }
        )
    return {
        "location": config_dict["location"],
        "credentials": credentials,
        "ionq_error_mitigation_flag": config_dict.get("ionq_error_mitigation"),
    }


def _braket_config_dict_to_backend_preferences_dict(
    config_dict: dict[str, Any],
) -> dict[str, Any]:
    config_dict["aws_access_key_id"] = config_dict.pop("braket_access_key_id", None)
    config_dict["aws_secret_access_key"] = config_dict.pop(
        "braket_secret_access_key", None
    )
    return config_dict


_PROVIDER_CONFIG_TO_BACKEND_PREFERENCES_SPEC = {
    Provider.CLASSIQ: _ProviderConfigToBackendPrefSpec(
        backend_preferences_class=ClassiqBackendPreferences,
        backend_name_mapper=_classiq_backend_name_mapper,
    ),
    Provider.GOOGLE: _ProviderConfigToBackendPrefSpec(
        backend_preferences_class=GCPBackendPreferences
    ),
    Provider.INTEL: _ProviderConfigToBackendPrefSpec(
        backend_preferences_class=IntelBackendPreferences
    ),
    Provider.IBM_QUANTUM: _ProviderConfigToBackendPrefSpec(
        backend_preferences_class=IBMBackendPreferences,
        config_class=IBMConfig,
        backend_name_mapper=_ibm_backend_name_mapper,
    ),
    Provider.AMAZON_BRAKET: _ProviderConfigToBackendPrefSpec(
        backend_preferences_class=AwsBackendPreferences,
        config_dict_to_backend_preferences_dict=_braket_config_dict_to_backend_preferences_dict,
        config_class=BraketConfig,
    ),
    Provider.IONQ: _ProviderConfigToBackendPrefSpec(
        backend_preferences_class=IonqBackendPreferences,
        config_class=IonQConfig,
    ),
    Provider.ALICE_AND_BOB: _ProviderConfigToBackendPrefSpec(
        backend_preferences_class=AliceBobBackendPreferences,
        config_class=AliceBobConfig,
    ),
    Provider.AQT: _ProviderConfigToBackendPrefSpec(
        backend_preferences_class=AQTBackendPreferences,
        config_class=AQTConfig,
    ),
    Provider.AZURE_QUANTUM: _ProviderConfigToBackendPrefSpec(
        backend_preferences_class=AzureBackendPreferences,
        config_dict_to_backend_preferences_dict=_azure_config_dict_to_backend_preferences_dict,
        config_class=AzureConfig,
    ),
}


def _get_backend_preferences_from_specifier(
    backend_spec: str, config: dict[str, Any] | ProviderConfig
) -> BackendPreferencesTypes:
    provider, backend_name = _parse_provider_backend(backend_spec)

    if provider not in _PROVIDER_CONFIG_TO_BACKEND_PREFERENCES_SPEC:
        raise NotImplementedError(
            f"Unsupported provider '{_PROVIDER_TO_CANONICAL_NAME.get(provider) or provider}'"
        )

    provider_spec = _PROVIDER_CONFIG_TO_BACKEND_PREFERENCES_SPEC[provider]
    if isinstance(config, ProviderConfig):
        if provider_spec.config_class is None:
            raise ValueError(
                f"This provider does not support any ProviderConfig classes. Received '{config.__class__.__name__}'"
            )
        if not isinstance(config, provider_spec.config_class):
            raise ValueError(
                f"{_PROVIDER_TO_CANONICAL_NAME[provider]} devices require {provider_spec.config_class.__name__}, got {config.__class__.__name__}"
            )
        config_dict = config.model_dump()
    else:
        config_dict = config
    if provider_spec.backend_name_mapper is not None:
        backend_name = provider_spec.backend_name_mapper(backend_name)

    if provider_spec.config_dict_to_backend_preferences_dict is not None:
        config_dict = provider_spec.config_dict_to_backend_preferences_dict(config_dict)

    config_dict["backend_name"] = backend_name
    return provider_spec.backend_preferences_class.model_validate(config_dict)
