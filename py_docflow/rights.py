from dataclasses import dataclass
from typing import Dict, Iterable


class BitSet:
    """Simple integer-backed bit set."""

    def __init__(self, value: int = 0):
        self.value = int(value)

    def set(self, index: int, flag: bool = True) -> 'BitSet':
        if flag:
            self.value |= 1 << index
        else:
            self.value &= ~(1 << index)
        return self

    def get(self, index: int) -> bool:
        return (self.value >> index) & 1 == 1

    def and_(self, other: 'BitSet') -> 'BitSet':
        return BitSet(self.value & other.value)

    def or_(self, other: 'BitSet') -> 'BitSet':
        return BitSet(self.value | other.value)

    def subtract(self, other: 'BitSet') -> 'BitSet':
        return BitSet(self.value & ~other.value)

    def invert(self, size: int) -> 'BitSet':
        mask = (1 << size) - 1
        return BitSet(~self.value & mask)

    def is_empty(self) -> bool:
        return self.value == 0

    def to_list(self) -> Iterable[int]:
        idx = 0
        value = self.value
        while value:
            if value & 1:
                yield idx
            value >>= 1
            idx += 1

    def __repr__(self) -> str:
        return f"BitSet({self.value})"


@dataclass
class RolesRegistry:
    """Assign incremental bit indexes to roles."""

    mapping: Dict[str, int] = None

    def __post_init__(self):
        if self.mapping is None:
            self.mapping = {}

    def index(self, role: str) -> int:
        if role not in self.mapping:
            self.mapping[role] = len(self.mapping)
        return self.mapping[role]

    def mask(self, roles: Iterable[str]) -> BitSet:
        bs = BitSet()
        for role in roles:
            bs.set(self.index(role))
        return bs
