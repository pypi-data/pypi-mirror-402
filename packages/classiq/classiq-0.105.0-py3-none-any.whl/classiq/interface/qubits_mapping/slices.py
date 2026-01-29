from collections import deque
from collections.abc import Iterable, Reversible
from itertools import chain

from typing_extensions import override


class Slices(deque[tuple[int, int]]):
    """A deque of slice objects that automatically merges adjacent slices.

    Slices represent a collection of non-overlapping, potentially non-contiguous
    slice ranges. When slices are appended or prepended, adjacent slices are
    automatically merged to maintain a compact representation. Methods use virtual
    notation, access the elements in the object as if all slices were explicitly
    written out contiguously.

    The class is primarily used for managing qubit allocations and mappings in
    quantum circuit synthesis, where it tracks which physical qubit ranges
    correspond to logical variable ranges.
    """

    @override
    def append(self, physical_slice: tuple[int, int]) -> None:
        if self and self[-1][1] == physical_slice[0]:
            last_physical_slice = self.pop()
            new_physical_slice = (last_physical_slice[0], physical_slice[1])
        else:
            new_physical_slice = physical_slice
        super().append(new_physical_slice)

    @override
    def appendleft(self, physical_slice: tuple[int, int]) -> None:
        if self and self[0][0] == physical_slice[1]:
            first_physical_slice = self.popleft()
            new_physical_slice = (physical_slice[0], first_physical_slice[1])
        else:
            new_physical_slice = physical_slice
        super().appendleft(new_physical_slice)

    def _multiple_appendleft(
        self, physical_slices: Reversible[tuple[int, int]]
    ) -> None:
        for physical_slice in reversed(physical_slices):
            self.appendleft(physical_slice)

    @override
    def extend(self, physical_slices: Iterable[tuple[int, int]]) -> None:
        for physical_slice in physical_slices:
            self.append(physical_slice)

    def pop_prefix_virtual_slice(self, virtual_end: int) -> "Slices":
        result = Slices()
        current_virtual_end, result_physical_end, physical_slice_end = 0, 0, 0
        while current_virtual_end < virtual_end:
            physical_slice_start, physical_slice_end = self.popleft()
            current_virtual_end += physical_slice_end - physical_slice_start
            overlap_virtual_end = min(virtual_end, current_virtual_end)
            result_physical_end = physical_slice_end + (
                overlap_virtual_end - current_virtual_end
            )
            result.append((physical_slice_start, result_physical_end))
        if result_physical_end != physical_slice_end:
            self.appendleft((result_physical_end, physical_slice_end))
        return result

    def get_virtual_slice(self, virtual_start: int, virtual_end: int) -> "Slices":
        result = Slices()
        current_virtual_start = 0
        for physical_slice in self:
            physical_slice_start, physical_slice_end = physical_slice
            current_virtual_end = current_virtual_start + (
                physical_slice_end - physical_slice_start
            )
            overlap_virtual_start = max(virtual_start, current_virtual_start)
            overlap_virtual_end = min(virtual_end, current_virtual_end)
            if overlap_virtual_start < overlap_virtual_end:
                new_physical_start = physical_slice_start + (
                    overlap_virtual_start - current_virtual_start
                )
                new_physical_end = physical_slice_end + (
                    overlap_virtual_end - current_virtual_end
                )
                result.append((new_physical_start, new_physical_end))
            if current_virtual_end >= virtual_end:
                break
            current_virtual_start = current_virtual_end
        return result

    def update_virtual_slice(
        self, virtual_start: int, virtual_end: int, new: "Slices"
    ) -> None:
        start = self.pop_prefix_virtual_slice(virtual_start)
        self.pop_prefix_virtual_slice(virtual_end - virtual_start)
        self._multiple_appendleft(new)
        self._multiple_appendleft(start)

    def mapping_virtual_slices(self, virtual_slices: "Slices") -> "Slices":
        mappings = Slices()
        for virtual_slice in virtual_slices:
            virtual_start, virtual_end = virtual_slice
            for mapped_slice in self.get_virtual_slice(virtual_start, virtual_end):
                mappings.append(mapped_slice)
        return mappings

    def size(self) -> int:
        return sum(_slice[1] - _slice[0] for _slice in self)

    @property
    def indices(self) -> tuple[int, ...]:
        return tuple(
            chain.from_iterable(range(_slice[0], _slice[1]) for _slice in self)
        )
