from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pandas import DataFrame

from classiq.interface.backend.backend_preferences import (
    BackendPreferencesTypes,
    ClassiqBackendPreferences,
    GCPBackendPreferences,
)
from classiq.interface.backend.quantum_backend_providers import (
    ClassiqNvidiaBackendNames,
    ClassiqSimulatorBackendNames,
    GoogleNvidiaBackendNames,
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
from classiq.execution import ExecutionSession
from classiq.execution.functions.util._logging import _logger
from classiq.execution.functions.util.constants import Verbosity
from classiq.execution.functions.util.parse_provider_backend import (
    _PROVIDER_TO_CANONICAL_NAME,
    _parse_provider_backend,
)

_DEFAULT_STATE_VECTOR_BACKEND_NAME = "simulator"


def _calculate_state_vector(
    qprog: QuantumProgram,
    backend: str | None = None,
    *,
    parameters: ExecutionParams | None = None,
    filters: dict[str, Any] | None = None,
    random_seed: int | None = None,
    transpilation_option: TranspilationOption = TranspilationOption.DECOMPOSE,
    verbosity: Verbosity = Verbosity.INFO,
) -> "DataFrame":
    """
    Calculate the state vector of a quantum program.

    Args:
        qprog: The quantum program
        backend: The simulator on which to simulate the quantum program. Specified as "provider/device_id"
        parameters: The classical parameters for the quantum program
        filters: Only states where the variables match these values will be included in the state vector.
        random_seed: The random seed used for transpilation and simulation
        transpilation_option: Advanced configuration for hardware-specific transpilation
        verbosity: What level of information should be logged

    Returns: A dataframe containing the state vector
    """
    if backend is None:
        backend = _DEFAULT_STATE_VECTOR_BACKEND_NAME

    provider, raw_backend_name = _parse_provider_backend(backend)
    backend_name_lower = raw_backend_name.lower()
    backend_preferences: BackendPreferencesTypes

    if provider == Provider.CLASSIQ:
        if backend_name_lower == "simulator":
            backend_name = str(ClassiqSimulatorBackendNames.SIMULATOR_STATEVECTOR)
        elif backend_name_lower == "nvidia_simulator":
            backend_name = str(ClassiqNvidiaBackendNames.SIMULATOR_STATEVECTOR)
        else:
            raise ValueError(
                f"Unsupported backend '{backend}'. "
                "Under the Classiq provider, only 'classiq/simulator' and 'classiq/nvidia_simulator' are supported."
            )
        backend_preferences = ClassiqBackendPreferences(backend_name=backend_name)
    elif provider == Provider.GOOGLE:
        if backend_name_lower == "cuquantum":
            backend_name = str(GoogleNvidiaBackendNames.CUQUANTUM_STATEVECTOR)
        else:
            raise ValueError(
                f"Unsupported backend '{backend}'. "
                "Under the Google provider, only 'google/cuquantum' is supported."
            )
        backend_preferences = GCPBackendPreferences(backend_name=backend_name)
    else:
        raise ValueError(
            f"Provider '{_PROVIDER_TO_CANONICAL_NAME.get(provider) or provider}' does not support this operation."
        )

    ep = ExecutionPreferences(
        backend_preferences=backend_preferences,
        random_seed=create_random_seed() if random_seed is None else random_seed,
        transpile_to_hardware=transpilation_option,
    )
    if verbosity != Verbosity.QUIET:
        _logger.info(f"Submitting job to {backend}")
    with ExecutionSession(qprog, execution_preferences=ep) as session:
        if filters is not None:
            for output_name, value in filters.items():
                session.set_measured_state_filter(
                    output_name, lambda state, val=value: state == val
                )
        job = session.submit_sample(parameters)
        if verbosity != Verbosity.QUIET:
            _logger.info(f"Job id: {job.id}")
        result = job.get_sample_result()

    df = result.dataframe
    return df
