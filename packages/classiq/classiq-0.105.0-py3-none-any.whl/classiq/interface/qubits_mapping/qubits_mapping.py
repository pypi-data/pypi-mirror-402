import dataclasses
import itertools
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from typing import Any, Generic, TypeGuard, TypeVar, cast

from classiq.interface.exceptions import ClassiqInternalError
from classiq.interface.generator.functions.concrete_types import ConcreteQuantumType
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.visitor import RetType
from classiq.interface.model.allocate import Allocate
from classiq.interface.model.bind_operation import BindOperation
from classiq.interface.model.handle_binding import ConcreteHandleBinding, HandleBinding
from classiq.interface.model.model import Model
from classiq.interface.model.model_visitor import ModelStatementsVisitor
from classiq.interface.model.native_function_definition import NativeFunctionDefinition
from classiq.interface.model.quantum_function_call import QuantumFunctionCall
from classiq.interface.model.quantum_function_declaration import (
    NamedParamsQuantumFunctionDeclaration,
    QuantumFunctionDeclaration,
)
from classiq.interface.model.quantum_type import QuantumType
from classiq.interface.model.variable_declaration_statement import (
    VariableDeclarationStatement,
)

from .path_expr_range import get_path_expr_range
from .slices import Slices


@dataclasses.dataclass
class FunctionScope:
    variables: dict[str, ConcreteQuantumType] = dataclasses.field(default_factory=dict)
    allocated_variables: dict[str, Slices] = dataclasses.field(default_factory=dict)
    total_resources: int = dataclasses.field(default=0)

    def add_new_var(self, var_name: str, quantum_type: ConcreteQuantumType) -> None:
        self.variables[var_name] = quantum_type

    def allocate_new_var(self, var_name: str, var_size: int) -> None:
        new_total_resources = self.total_resources + var_size
        self.allocated_variables[var_name] = Slices(
            [(self.total_resources, new_total_resources)]
        )
        self.total_resources = new_total_resources

    def bind_slices_to_var(self, var_name: str, slices: Slices) -> None:
        self.allocated_variables[var_name] = slices


T = TypeVar("T", bound=FunctionScope)

FREE_NAME = "free"


class QubitsMapping(Generic[T], ModelStatementsVisitor):
    """
    Visitor that maps quantum variables to virtual qubit slices in a quantum model.

    This visitor traverses the model's quantum functions and tracks the mapping of
    quantum variables to their virtual qubit allocations. It maintains scopes for each
    function, tracks the call stack, and maps variables to slices representing ranges
    of qubits. This class assumes that the visited model is a compiled qmod, which mainly
    means that all allocations are in the main function, and the model does not contain within_apply.
    """

    def __init__(self, scope_type: type[FunctionScope] = FunctionScope) -> None:
        super().__init__()
        self._scope_type: type[T] = cast(type[T], scope_type)
        self.scopes: dict[str, T] = {}
        self._main_func_name: str
        self._current_function: str

    @property
    def _current_scope(self) -> T:
        return self.scopes[self._current_function]

    @contextmanager
    def _function_scoping(
        self, func_def: NamedParamsQuantumFunctionDeclaration
    ) -> Iterator[T]:
        func_name = func_def.name
        _previous_function = self._current_function
        self._current_function = func_name
        self.scopes[func_name] = self._initialize_function_scope(func_def)
        yield self.scopes[func_name]
        self._current_function = _previous_function

    def _is_entry_point(self, func_name: str) -> bool:
        return func_name == self._main_func_name

    def _is_free_function_call(self, call: QuantumFunctionCall) -> bool:
        return call.func_decl.name == FREE_NAME

    def _is_function_with_definition(
        self, func_decl: QuantumFunctionDeclaration
    ) -> TypeGuard[NativeFunctionDefinition]:
        return isinstance(func_decl, NativeFunctionDefinition)

    def visit_Model(self, model: Model) -> RetType | None:
        self._main_func_name = model.main_func.name
        self._current_function = self._main_func_name
        self.visit_BaseModel(model)
        return None

    def visit_NativeFunctionDefinition(
        self, func: NativeFunctionDefinition
    ) -> RetType | None:
        if func.name in self.scopes:
            return None
        with self._function_scoping(func):
            self.visit(func.body)
        return None

    def visit_Allocate(self, stat: Allocate) -> RetType | None:
        if not self._is_entry_point(self._current_function):
            raise ClassiqInternalError(
                "compiled qmod can't have allocation outside of main function"
            )
        var_name = stat.target.name
        var_type = self._current_scope.variables[var_name]
        self._current_scope.allocate_new_var(stat.target.name, var_type.size_in_bits)
        return None

    def visit_VariableDeclarationStatement(
        self, stat: VariableDeclarationStatement
    ) -> RetType | None:
        if isinstance(stat.qmod_type, QuantumType):
            self._current_scope.add_new_var(stat.name, stat.qmod_type)
        return None

    def _visit_free_function_call(self, stat: QuantumFunctionCall) -> None | Any:
        if not self._is_entry_point(self._current_function):
            raise ClassiqInternalError(
                "compiled qmod can't have free outside of main function"
            )
        input_name = stat.inputs[0].name
        self._current_scope.allocated_variables.pop(input_name)
        return None

    def _visit_quantum_function_call(self, stat: QuantumFunctionCall) -> None | Any:
        if self._is_free_function_call(stat):
            self._visit_free_function_call(stat)
            return None
        func_decl = stat.func_decl
        if not self._is_function_with_definition(func_decl):
            return None
        input_slices = self.get_call_input_slices(stat)
        end_call_scope = self.scopes[stat.func_decl.name]
        for port, handle in zip(func_decl.port_declarations, stat.ports):
            if port.direction == PortDeclarationDirection.Input:
                new_slices = Slices()
            else:
                relative_output = end_call_scope.allocated_variables[port.name]
                new_slices = input_slices.mapping_virtual_slices(relative_output)
            self._update_by_handle(handle, new_slices, port.direction)
        return None

    def visit_QuantumFunctionCall(self, stat: QuantumFunctionCall) -> RetType | None:
        if self._is_free_function_call(stat):
            self._visit_free_function_call(stat)
            return None
        self._visit_quantum_function_call(stat)
        return None

    def visit_BindOperation(self, stat: BindOperation) -> RetType | None:
        input_slices = self._handles_to_slices(stat.in_handles)
        for in_handle in stat.in_handles:
            self._current_scope.allocated_variables.pop(in_handle.name)
        start_index, end_index = 0, 0
        for out in stat.out_handles:
            out_var = self._current_scope.variables[out.name]
            end_index += out_var.size_in_bits
            new_slices = input_slices.get_virtual_slice(start_index, end_index)
            self._update_by_handle(out, new_slices, PortDeclarationDirection.Output)
            start_index = end_index
        return None

    def get_call_input_slices(self, stat: QuantumFunctionCall) -> Slices:
        input_handles = (
            handle
            for inp, handle in zip(stat.func_decl.port_declarations, stat.ports)
            if inp.direction.is_input
        )
        return self._handles_to_slices(input_handles)

    def _handles_to_slices(self, handles: Iterable[ConcreteHandleBinding]) -> Slices:
        return Slices(
            itertools.chain.from_iterable(
                self._handle_to_slices(handle) for handle in handles
            )
        )

    def _handle_to_slices(self, handle: HandleBinding) -> Slices:
        quantum_type = self._current_scope.variables[handle.name]
        var_mapping = self._current_scope.allocated_variables[handle.name]
        start, stop = get_path_expr_range(handle, quantum_type)
        return var_mapping.get_virtual_slice(start, stop)

    def _update_by_handle(
        self,
        handle: HandleBinding,
        new_slices: Slices,
        direction: PortDeclarationDirection,
    ) -> None:
        if direction == PortDeclarationDirection.Input:
            self._current_scope.allocated_variables.pop(handle.name)
        elif direction == PortDeclarationDirection.Output:
            pass
        else:
            quantum_type = self._current_scope.variables[handle.name]
            start, stop = get_path_expr_range(handle, quantum_type)
            var_mapping = self._current_scope.allocated_variables[handle.name].copy()
            var_mapping.update_virtual_slice(start, stop, new_slices)
            new_slices = var_mapping
        self._current_scope.bind_slices_to_var(handle.name, new_slices)

    def _initialize_function_scope(
        self, func_def: NamedParamsQuantumFunctionDeclaration
    ) -> T:
        function_variables = self._scope_type()
        ports = func_def.port_declarations
        for port in ports:
            function_variables.add_new_var(port.name, port.quantum_type)
            if port.direction != PortDeclarationDirection.Output:
                function_variables.allocate_new_var(
                    port.name, port.quantum_type.size_in_bits
                )
        return function_variables
