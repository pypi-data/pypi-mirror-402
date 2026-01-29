from functools import singledispatch

from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.generator.functions.concrete_types import ConcreteQuantumType
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.model.handle_binding import (
    FieldHandleBinding,
    HandleBinding,
    SlicedHandleBinding,
    SubscriptHandleBinding,
)
from classiq.interface.model.quantum_type import QuantumBitvector


def get_path_expr_range(
    var: HandleBinding, quantum_type: ConcreteQuantumType
) -> tuple[int, int]:
    start = 0
    stop = quantum_type.size_in_bits
    for var_prefix in var.prefixes()[1:]:
        start, stop, quantum_type = _pop_var_range(var_prefix, quantum_type, start)
    return start, stop


@singledispatch
def _pop_var_range(
    var_prefix: HandleBinding, quantum_type: ConcreteQuantumType, start: int
) -> tuple[int, int, ConcreteQuantumType]:
    raise ClassiqInternalExpansionError("Unexpected path expression")


@_pop_var_range.register
def _(
    var_prefix: SubscriptHandleBinding, quantum_type: ConcreteQuantumType, start: int
) -> tuple[int, int, ConcreteQuantumType]:
    if not isinstance(quantum_type, QuantumBitvector):
        raise ClassiqInternalExpansionError("Unexpected path expression")
    index = var_prefix.index.to_int_value()
    element_type = quantum_type.element_type
    start += element_type.size_in_bits * index
    stop = start + element_type.size_in_bits
    return start, stop, element_type


@_pop_var_range.register
def _(
    var_prefix: SlicedHandleBinding, quantum_type: ConcreteQuantumType, start: int
) -> tuple[int, int, ConcreteQuantumType]:
    if not isinstance(quantum_type, QuantumBitvector):
        raise ClassiqInternalExpansionError("Unexpected path expression")
    slice_start = var_prefix.start.to_int_value()
    slice_stop = var_prefix.end.to_int_value()
    stop = start + quantum_type.element_type.size_in_bits * slice_stop
    start += quantum_type.element_type.size_in_bits * slice_start
    return start, stop, quantum_type


@_pop_var_range.register
def _(
    var_prefix: FieldHandleBinding, quantum_type: ConcreteQuantumType, start: int
) -> tuple[int, int, ConcreteQuantumType]:
    if not isinstance(quantum_type, TypeName) or not quantum_type.has_fields:
        raise ClassiqInternalExpansionError("Unexpected path expression")
    for field, field_type in quantum_type.fields.items():
        if field == var_prefix.field:
            stop = start + field_type.size_in_bits
            return start, stop, field_type
        start += field_type.size_in_bits
    raise ClassiqInternalExpansionError("Unexpected path expression")
