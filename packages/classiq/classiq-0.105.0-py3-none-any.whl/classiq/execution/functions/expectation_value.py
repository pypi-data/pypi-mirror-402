from typing import Any

from classiq.interface.backend.backend_preferences import (
    BackendPreferencesTypes,
    ClassiqBackendPreferences,
)
from classiq.interface.backend.provider_config.provider_config import ProviderConfig
from classiq.interface.backend.quantum_backend_providers import (
    ClassiqSimulatorBackendNames,
)
from classiq.interface.executor.execution_preferences import ExecutionPreferences
from classiq.interface.generator.model.preferences import create_random_seed
from classiq.interface.generator.model.preferences.preferences import (
    TranspilationOption,
)
from classiq.interface.hardware import Provider

from classiq import (
    ExecutionParams,
    QuantumProgram,
)
from classiq.execution.execution_session import ExecutionSession
from classiq.execution.functions.util._logging import _logger
from classiq.execution.functions.util.backend_preferences import (
    _get_backend_preferences_from_specifier,
)
from classiq.execution.functions.util.constants import Verbosity
from classiq.execution.functions.util.parse_provider_backend import (
    _parse_provider_backend,
)
from classiq.qmod.builtins.structs import SparsePauliOp

_DEFAULT_BACKEND_NAME = "simulator"


def _get_backend_preferences(
    backend: str, estimate: bool, config: dict[str, Any] | ProviderConfig | None
) -> BackendPreferencesTypes:
    provider, backend_name = _parse_provider_backend(backend)
    backend_preferences: BackendPreferencesTypes
    if not estimate:
        if not (
            provider == Provider.CLASSIQ and backend_name.lower().strip() == "simulator"
        ):
            raise ValueError(
                "Calculating exact expectation value is supported only for the 'classiq/simulator' backend"
            )
        backend_preferences = ClassiqBackendPreferences(
            # This backend name is for exact simulation
            backend_name=ClassiqSimulatorBackendNames.SIMULATOR_STATEVECTOR
        )
    else:
        backend_preferences = _get_backend_preferences_from_specifier(
            backend, config or {}
        )
    return backend_preferences


def _get_expectation_value(
    qprog: QuantumProgram,
    observable: SparsePauliOp,
    backend: str | None = None,
    *,
    estimate: bool = True,
    parameters: ExecutionParams | None = None,
    config: dict[str, Any] | ProviderConfig | None = None,
    num_shots: int | None = None,
    random_seed: int | None = None,
    transpilation_option: TranspilationOption = TranspilationOption.DECOMPOSE,
    verbosity: Verbosity = Verbosity.INFO,
) -> complex:
    if backend is None:
        backend = _DEFAULT_BACKEND_NAME
    backend_preferences = _get_backend_preferences(backend, estimate, config)
    ep = ExecutionPreferences(
        backend_preferences=backend_preferences,
        num_shots=num_shots,
        random_seed=create_random_seed() if random_seed is None else random_seed,
        transpile_to_hardware=transpilation_option,
    )

    if verbosity != Verbosity.QUIET:
        _logger.info(f"Submitting job to {backend}")
    with ExecutionSession(qprog, execution_preferences=ep) as session:
        job = session.submit_estimate(hamiltonian=observable, parameters=parameters)
        if verbosity != Verbosity.QUIET:
            _logger.info(f"Job id: {job.id}")
        result = job.get_estimate_result()
        return result.value
