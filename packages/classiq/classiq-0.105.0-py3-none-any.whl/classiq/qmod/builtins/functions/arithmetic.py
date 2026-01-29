from typing import Literal

from classiq.qmod.cparam import CInt
from classiq.qmod.qfunc import qfunc, qperm
from classiq.qmod.qmod_parameter import CArray, CBool, CReal
from classiq.qmod.qmod_variable import (
    Const,
    Input,
    Output,
    QArray,
    QBit,
    QNum,
)


@qfunc(external=True)
def unitary(
    elements: CArray[CArray[CReal]],
    target: QArray[QBit, Literal["log(elements[0].len, 2)"]],
) -> None:
    """
    [Qmod core-library function]

    Applies a unitary matrix on a quantum state.

    Args:
        elements:  A 2d array of complex numbers representing the unitary matrix. This matrix must be unitary.
        target: The quantum state to apply the unitary on. Should be of corresponding size.
    """
    pass


@qperm(external=True)
def add(
    left: Const[QNum],
    right: Const[QNum],
    result: Output[
        QNum[
            Literal["result_size"],
            Literal["result_is_signed"],
            Literal["result_fraction_places"],
        ]
    ],
    result_size: CReal,
    result_is_signed: CBool,
    result_fraction_places: CReal,
) -> None:
    pass


@qperm(external=True)
def add_inplace_right(
    left: Const[QNum],
    right: Input[QNum],
    result: Output[
        QNum[
            Literal["result_size"],
            Literal["result_is_signed"],
            Literal["result_fraction_places"],
        ]
    ],
    result_size: CReal,
    result_is_signed: CBool,
    result_fraction_places: CReal,
) -> None:
    pass


@qperm(external=True)
def canonical_add(
    left: Const[QArray],
    extend_left: CBool,
    right: QArray,
) -> None:
    """
    [Qmod core-library function]

    Adds two quantum variables representing integers (signed or unsigned), storing the
    result in the second variable (in-place):

    $$
        \\left|\\text{left}\\right\\rangle \\left|\\text{right}\\right\\rangle
        \\mapsto
        \\left|\\text{left}\\right\\rangle \\left|\\left(\\text{right} +
        \\text{left}\\right) \\bmod 2^{\\text{right.size}} \\right\\rangle
    $$

    Args:
        left: The out-of-place argument for the addition.
        extend_left: Whether to sign-extend the left argument.
        right: The in-place argument for the addition, holds the final result.
    """
    pass


@qperm(external=True)
def modular_add(left: Const[QArray[QBit]], right: QArray[QBit]) -> None:
    pass


@qperm(external=True)
def modular_add_constant(left: CReal, right: QNum) -> None:
    pass


@qperm(external=True)
def integer_xor(left: Const[QArray[QBit]], right: QArray[QBit]) -> None:
    pass


@qperm(external=True)
def real_xor_constant(left: CReal, right: QNum) -> None:
    pass


@qperm(external=True)
def multiply(left: Const[QNum], right: Const[QNum], result: Output[QNum]) -> None:
    """
    [Qmod core-library function]

    Multiplies two quantum numeric variables:

    $$
        \\left|\\text{left}\\right\\rangle \\left|\\text{right}\\right\\rangle
        \\mapsto
        \\left|\\text{left}\\right\\rangle \\left|\\text{right}\\right\\rangle
        \\left|\\text{left} \\cdot \\text{right} \\right\\rangle
    $$

    Args:
        left: The first argument for the multiplication.
        right: The second argument for the multiplication.
        result: The quantum variable to hold the multiplication result.
    """
    pass


@qperm(external=True)
def multiply_constant(left: CReal, right: Const[QNum], result: Output[QNum]) -> None:
    """
    [Qmod core-library function]

    Multiplies a quantum numeric variable with a constant:

    $$
        \\left|\\text{right}\\right\\rangle
        \\mapsto
        \\left|\\text{right}\\right\\rangle
        \\left|\\text{left} \\cdot \\text{right} \\right\\rangle
    $$

    Args:
        left: The constant argument for the multiplication.
        right: The variable argument for the multiplication.
        result: The quantum variable to hold the multiplication result.
    """
    pass


@qperm(external=True)
def canonical_multiply(
    left: Const[QArray],
    extend_left: CBool,
    right: Const[QArray],
    extend_right: CBool,
    result: QArray,
    trim_result_lsb: CBool,
) -> None:
    """
    [Qmod core-library function]

    Multiplies two quantum variables representing integers (signed or unsigned) into the
    result variable which is assumed to start in the $|0\\rangle$ state.

    If `trim_result_lsb` is `False`, applies the transformation:

    $$
        \\left|\\text{left}\\right\\rangle \\left|\\text{right}\\right\\rangle
        \\left|0\\right\\rangle \\mapsto \\left|\\text{left}\\right\\rangle
        \\left|\\text{right}\\right\\rangle \\left|\\left( \\text{left} \\cdot
        \\text{right} \\right) \\bmod 2^{\\text{result.size}} \\right\\rangle
    $$

    If `trim_result_lsb` is `True`, the function avoids computing the result's LSB and
    applies the transformation:

    $$
        \\left|\\text{left}\\right\\rangle \\left|\\text{right}\\right\\rangle
        \\left|0\\right\\rangle \\mapsto \\left|\\text{left}\\right\\rangle
        \\left|\\text{right}\\right\\rangle \\left|\\left( \\text{left} \\cdot
        \\text{right} \\right) \\gg 1 \\bmod 2^{\\text{result.size}} \\right\\rangle
    $$

    Args:
        left: The first argument for the multiplication.
        extend_left: Whether to sign-extend the left argument.
        right: The second argument for the multiplication.
        extend_right: Whether to sign-extend the right argument.
        result: The quantum variable to hold the multiplication result.
        trim_result_lsb: Whether to avoid computing the result's LSB.
    """
    pass


@qperm(external=True)
def canonical_multiply_constant(
    left: CInt,
    right: Const[QArray],
    extend_right: CBool,
    result: QArray,
    trim_result_lsb: CBool,
) -> None:
    """
    [Qmod core-library function]

    Multiplies a quantum variable representing an integer (signed or unsigned) with a
    constant, into the result variable which is assumed to start in the $|0\\rangle$ state.

    If `trim_result_lsb` is `False`, applies the transformation:

    $$
        \\left|\\text{right}\\right\\rangle \\left|0\\right\\rangle \\mapsto
        \\left|\\text{right}\\right\\rangle \\left|\\left( \\text{left} \\cdot
        \\text{right} \\right) \\bmod 2^{\\text{result.size}} \\right\\rangle
    $$

    If `trim_result_lsb` is `True`, the function avoids computing the result's LSB and
    applies the transformation:

    $$
        \\left|\\text{right}\\right\\rangle \\left|0\\right\\rangle \\mapsto
        \\left|\\text{right}\\right\\rangle \\left|\\left( \\text{left} \\cdot
        \\text{right} \\right) \\gg 1 \\bmod 2^{\\text{result.size}} \\right\\rangle
    $$

    Args:
        left: The constant argument for the multiplication.
        right: The variable argument for the multiplication.
        extend_right: Whether to sign-extend the right argument.
        result: The quantum variable to hold the multiplication result.
        trim_result_lsb: Whether to avoid computing the result's LSB.
    """
    pass
