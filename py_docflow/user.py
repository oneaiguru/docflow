from dataclasses import dataclass, field
from typing import List

@dataclass
class User:
    """Simple user representation with roles."""

    name: str
    roles: List[str] = field(default_factory=list)
