from classiq.interface.hardware import Provider

_PROVIDER_BACKEND_SEPARATOR = "/"

_PROVIDER_TO_CANONICAL_NAME: dict[Provider, str] = {
    Provider.IBM_QUANTUM: "ibm",
    Provider.AZURE_QUANTUM: "azure",
    Provider.AMAZON_BRAKET: "braket",
    Provider.IONQ: "ionq",
    Provider.CLASSIQ: "classiq",
    Provider.GOOGLE: "google",
    Provider.ALICE_AND_BOB: "alice&bob",
    Provider.OQC: "oqc",
    Provider.INTEL: "intel",
    Provider.AQT: "aqt",
    Provider.CINECA: "cineca",
    Provider.SOFTBANK: "softbank",
}

_CANONICAL_NAMES_TO_PROVIDER: dict[str, Provider] = {
    name: provider for provider, name in _PROVIDER_TO_CANONICAL_NAME.items()
}


def _error_suggested_provider(provider_name: str) -> Provider | None:
    """
    In the case that receive an incorrect provider name, return a possible suggestion.
    """
    provider_name = provider_name.strip().lower()
    for canonical_name in _CANONICAL_NAMES_TO_PROVIDER:
        if canonical_name in provider_name:
            return _CANONICAL_NAMES_TO_PROVIDER[canonical_name]
    # Special cases
    if "gcp" in provider_name:
        return Provider.GOOGLE
    if "microsoft" in provider_name:
        return Provider.AZURE_QUANTUM
    if "amazon" in provider_name or "aws" in provider_name:
        return Provider.AMAZON_BRAKET
    if "oxford" in provider_name:
        return Provider.OQC
    if "alice" in provider_name or "bob" in provider_name:
        return Provider.ALICE_AND_BOB
    if "alpine" in provider_name:
        return Provider.AQT

    return None


def _parse_provider_backend(spec: str) -> tuple[Provider, str]:
    """
    Parse a backend specification into (provider, backend). Provider is case-insensitive.
    Backend must NOT contain the separator. If provider is not specified, it defaults to
    Classiq.
    """
    if not spec.strip():
        raise ValueError("Backend specification must be a non-empty string")

    spec = spec.strip()

    if _PROVIDER_BACKEND_SEPARATOR not in spec:
        return Provider.CLASSIQ, spec

    provider_raw, backend = spec.split(_PROVIDER_BACKEND_SEPARATOR, 1)

    if _PROVIDER_BACKEND_SEPARATOR in backend:
        raise ValueError(
            f"Backend name must not contain '{_PROVIDER_BACKEND_SEPARATOR}': '{backend}'"
        )

    provider_key = provider_raw.strip().lower()
    backend = backend.strip()

    if not provider_key:
        raise ValueError("Provider name cannot be empty")
    if not backend:
        raise ValueError("Backend name cannot be empty")

    try:
        provider = _CANONICAL_NAMES_TO_PROVIDER[provider_key]
    except KeyError:
        error_message = f"Unrecognized provider '{provider_raw}'."
        suggested_provider = _error_suggested_provider(provider_key)
        if suggested_provider is not None:
            error_message += (
                f" Did you mean '{_PROVIDER_TO_CANONICAL_NAME[suggested_provider]}'?"
            )
        raise ValueError(error_message) from None

    return provider, backend
