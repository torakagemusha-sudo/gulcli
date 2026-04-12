"""
Jurisdiction Types - GUL v2.1

Authority boundaries and delegation hierarchies.
Implements jurisdiction scoping for policy decisions.

Mathematical Foundation:
    - Jurisdictions form a partial order under sub-jurisdiction relation
    - Delegation chains preserve authority bounds
    - Type system ensures well-formed jurisdiction combinations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class JurisdictionLevel(Enum):
    """
    Hierarchical jurisdiction levels.

    Ordered from broadest to narrowest scope:
    GLOBAL > REGIONAL > ORGANIZATIONAL > DEPARTMENTAL > PERSONAL
    """

    GLOBAL = "global"
    REGIONAL = "regional"
    ORGANIZATIONAL = "organizational"
    DEPARTMENTAL = "departmental"
    PERSONAL = "personal"

    def __lt__(self, other: "JurisdictionLevel") -> bool:
        """Compare levels (broader < narrower for containment)."""
        order = [
            JurisdictionLevel.GLOBAL,
            JurisdictionLevel.REGIONAL,
            JurisdictionLevel.ORGANIZATIONAL,
            JurisdictionLevel.DEPARTMENTAL,
            JurisdictionLevel.PERSONAL,
        ]
        return order.index(self) < order.index(other)

    def __le__(self, other: "JurisdictionLevel") -> bool:
        return self == other or self < other

    def contains(self, other: "JurisdictionLevel") -> bool:
        """Check if this level contains (is broader than) other."""
        return self <= other


@dataclass(frozen=True)
class JurisdictionId:
    """
    Unique identifier for a jurisdiction.

    Supports hierarchical structure via parent reference.

    Attributes:
        name: Unique name within parent scope
        parent: Optional parent jurisdiction (None = root)

    Examples:
        >>> global_j = JurisdictionId("global")
        >>> us_j = JurisdictionId("us", parent=global_j)
        >>> us_j.is_sub_jurisdiction(global_j)
        True
    """

    name: str
    parent: Optional["JurisdictionId"] = None

    def is_sub_jurisdiction(self, other: "JurisdictionId") -> bool:
        """
        Check j1 ⊆ⱽ j2 (sub-jurisdiction relation).

        A jurisdiction is a sub-jurisdiction of another if:
        - They are the same jurisdiction, OR
        - Its parent is a sub-jurisdiction of the other

        Args:
            other: Potential containing jurisdiction

        Returns:
            True if self is contained within other
        """
        if self == other:
            return True
        if self.parent is None:
            return False
        return self.parent.is_sub_jurisdiction(other)

    def depth(self) -> int:
        """Return depth in hierarchy (root = 0)."""
        if self.parent is None:
            return 0
        return 1 + self.parent.depth()

    def root(self) -> "JurisdictionId":
        """Return root jurisdiction."""
        if self.parent is None:
            return self
        return self.parent.root()

    def path(self) -> list["JurisdictionId"]:
        """Return path from root to self."""
        if self.parent is None:
            return [self]
        return self.parent.path() + [self]

    def fully_qualified_name(self) -> str:
        """Return dot-separated path from root."""
        return ".".join(j.name for j in self.path())

    def __repr__(self) -> str:
        return f"JurisdictionId({self.fully_qualified_name()})"


@dataclass
class Jurisdiction:
    """
    Full jurisdiction specification.

    Combines identity with metadata about authority scope.

    Attributes:
        id: Unique jurisdiction identifier
        level: Hierarchical level
        authority: Name of authorizing entity
        delegates: List of delegated authorities
        valid_since: Start of jurisdiction validity
        valid_until: End of jurisdiction validity (None = indefinite)
    """

    id: JurisdictionId
    level: JurisdictionLevel
    authority: str
    delegates: list[str] = field(default_factory=list)
    valid_since: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    def is_valid(self, at_time: Optional[datetime] = None) -> bool:
        """
        Check if jurisdiction is valid at given time.

        Args:
            at_time: Time to check (defaults to now)

        Returns:
            True if jurisdiction is valid
        """
        now = at_time or datetime.now()

        if self.valid_since is not None and now < self.valid_since:
            return False
        if self.valid_until is not None and now > self.valid_until:
            return False

        return True

    def can_delegate_to(self, delegate: str) -> bool:
        """Check if authority can delegate to given entity."""
        return delegate in self.delegates or self.authority == delegate

    def contains(self, other: "Jurisdiction") -> bool:
        """Check if this jurisdiction contains another."""
        return other.id.is_sub_jurisdiction(self.id)

    def __repr__(self) -> str:
        return (
            f"Jurisdiction({self.id.name}, level={self.level.value}, "
            f"authority={self.authority})"
        )


class JType(Enum):
    """
    Jurisdiction type constructors from GUL.lean.

    Used for type-level jurisdiction specification in policies.

    Values:
        UNRESTRICTED: No jurisdiction constraints
        LOCAL: Bound to specific jurisdiction
        UNION: Combined authority from multiple jurisdictions
        INTERSECTION: Requires all jurisdictions to agree
        DELEGATION: Authority delegated from another jurisdiction
    """

    UNRESTRICTED = "unrestricted"
    LOCAL = "local"
    UNION = "union"
    INTERSECTION = "intersection"
    DELEGATION = "delegation"


@dataclass
class JurisdictionConstraint:
    """
    Constraint on jurisdiction for policy evaluation.

    Specifies how jurisdiction should be checked in a policy.

    Attributes:
        jtype: Type of jurisdiction constraint
        jurisdictions: List of relevant jurisdiction IDs
        require_all: For intersection, require all to match
    """

    jtype: JType
    jurisdictions: list[JurisdictionId] = field(default_factory=list)
    require_all: bool = False

    def matches(self, j: JurisdictionId) -> bool:
        """
        Check if jurisdiction matches constraint.

        Args:
            j: Jurisdiction to check

        Returns:
            True if jurisdiction satisfies constraint
        """
        if self.jtype == JType.UNRESTRICTED:
            return True

        if self.jtype == JType.LOCAL:
            return any(j.is_sub_jurisdiction(target) for target in self.jurisdictions)

        if self.jtype == JType.UNION:
            return any(j.is_sub_jurisdiction(target) for target in self.jurisdictions)

        if self.jtype == JType.INTERSECTION:
            return all(j.is_sub_jurisdiction(target) for target in self.jurisdictions)

        if self.jtype == JType.DELEGATION:
            # Delegation requires being in the delegation chain
            return any(j.is_sub_jurisdiction(target) for target in self.jurisdictions)

        return False

    @classmethod
    def unrestricted(cls) -> "JurisdictionConstraint":
        """Create unrestricted constraint."""
        return cls(jtype=JType.UNRESTRICTED)

    @classmethod
    def local(cls, jurisdiction: JurisdictionId) -> "JurisdictionConstraint":
        """Create local constraint for single jurisdiction."""
        return cls(jtype=JType.LOCAL, jurisdictions=[jurisdiction])

    @classmethod
    def union(cls, *jurisdictions: JurisdictionId) -> "JurisdictionConstraint":
        """Create union constraint (any jurisdiction)."""
        return cls(jtype=JType.UNION, jurisdictions=list(jurisdictions))

    @classmethod
    def intersection(cls, *jurisdictions: JurisdictionId) -> "JurisdictionConstraint":
        """Create intersection constraint (all jurisdictions)."""
        return cls(
            jtype=JType.INTERSECTION,
            jurisdictions=list(jurisdictions),
            require_all=True,
        )
