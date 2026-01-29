from typing import TYPE_CHECKING, Any

from classiq.execution.functions.util.backend_preferences import (
    _get_backend_preferences_from_specifier,
)

if TYPE_CHECKING:
    from pandas import DataFrame

from classiq.interface.backend.provider_config.provider_config import ProviderConfig
from classiq.interface.executor.execution_preferences import ExecutionPreferences
from classiq.interface.generator.model.preferences import create_random_seed
from classiq.interface.generator.model.preferences.preferences import (
    TranspilationOption,
)

from classiq import (
    ExecutionParams,
    QuantumProgram,
)
from classiq.execution import ExecutionSession
from classiq.execution.functions.util._logging import _logger
from classiq.execution.functions.util.constants import Verbosity

_DEFAULT_BACKEND_NAME = "simulator"


def _new_sample(
    qprog: QuantumProgram,
    backend: str | None = None,
    *,
    parameters: ExecutionParams | None = None,
    config: dict[str, Any] | ProviderConfig | None = None,
    num_shots: int | None = None,
    random_seed: int | None = None,
    transpilation_option: TranspilationOption = TranspilationOption.DECOMPOSE,
    verbosity: Verbosity = Verbosity.INFO,
) -> "DataFrame":
    """
    Sample a quantum program.

    Args:
        qprog: The quantum program
        backend: The device (hardware or simulator) on which to run the quantum program. Specified as "provider/device_id". Use the `get_backend_details` function to see supported devices.
        parameters: The classical parameters for the quantum program
        config: Provider-specific configuration, such as api keys
        num_shots: The number of times to sample
        random_seed: The random seed used for transpilation and simulation
        transpilation_option: Advanced configuration for hardware-specific transpilation
        verbosity: What level of information should be logged

    Returns: A dataframe containing the histogram
    """
    if num_shots is not None and num_shots < 1:
        raise ValueError(f"Argument num_shots must be greater than 0, got {num_shots}")
    if config is None:
        config = {}
    if backend is None:
        backend = _DEFAULT_BACKEND_NAME
    backend_preferences = _get_backend_preferences_from_specifier(backend, config)
    ep = ExecutionPreferences(
        backend_preferences=backend_preferences,
        num_shots=num_shots,
        random_seed=create_random_seed() if random_seed is None else random_seed,
        transpile_to_hardware=transpilation_option,
    )
    if verbosity != Verbosity.QUIET:
        _logger.info(f"Submitting job to {backend}")
    with ExecutionSession(qprog, execution_preferences=ep) as session:
        job = session.submit_sample(parameters)
        if verbosity != Verbosity.QUIET:
            _logger.info(f"Job id: {job.id}")
        result = job.get_sample_result()

    df = result.dataframe
    return df
