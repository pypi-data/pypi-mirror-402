from typing import TYPE_CHECKING

from classiq.interface.hardware import HardwareInformation, Provider

from classiq._internals import async_utils
from classiq._internals.api_wrapper import ApiWrapper
from classiq.execution.functions.util.parse_provider_backend import (
    _PROVIDER_TO_CANONICAL_NAME,
)

if TYPE_CHECKING:
    from pandas import DataFrame


def get_all_hardware_devices() -> list[HardwareInformation]:
    """
    Returns a list of all hardware devices known to Classiq.
    """
    return async_utils.run(ApiWrapper.call_get_all_hardware_devices())


def _extract_relevant_hardware_fields_for_user(info: HardwareInformation) -> tuple:
    return (
        _PROVIDER_TO_CANONICAL_NAME[info.provider],
        info.name,
        info.number_of_qubits,
        info.status.availability.is_available,
        info.status.pending_jobs,
        info.status.queue_time,
    )


_NON_DISPLAYED_DEVICES = [
    (Provider.CLASSIQ, "simulator_statevector"),
    (Provider.CLASSIQ, "nvidia_simulator_statevector"),
    (Provider.GOOGLE, "cuquantum_statevector"),
]


def get_backend_details() -> "DataFrame":
    """
    Returns a pandas DataFrame containing hardware devices known to Classiq.
    """
    from pandas import DataFrame

    devices = get_all_hardware_devices()
    displayed_devices = [
        device
        for device in devices
        if (device.provider, device.name) not in _NON_DISPLAYED_DEVICES
    ]
    # Remove "ibm_" prefix.
    for device in displayed_devices:
        if device.provider == Provider.IBM_QUANTUM and device.name.startswith("ibm_"):
            device.name = device.name[len("ibm_") :]
    tuples = [
        _extract_relevant_hardware_fields_for_user(info) for info in displayed_devices
    ]
    return DataFrame(
        tuples,
        columns=[
            "provider",
            "name",
            "number of qubits",
            "available",
            "pending jobs",
            "queue time",
        ],
    )
