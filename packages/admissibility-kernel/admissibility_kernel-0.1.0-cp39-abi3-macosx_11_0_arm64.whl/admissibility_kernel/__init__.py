"""
Admissibility Kernel - Deterministic context slicing for conversation DAGs.

This package provides Python bindings for the Admissibility Kernel,
a high-performance Rust library for deterministic context slicing.

## Quick Start

```python
from admissibility_kernel import (
    InMemoryGraphStore,
    ContextSlicer,
    SlicePolicy,
    TurnSnapshot,
    Edge,
    Role,
    Phase,
    EdgeType,
)

# Create a graph store
store = InMemoryGraphStore()

# Add turns
turn1 = TurnSnapshot(
    turn_id="550e8400-e29b-41d4-a716-446655440001",
    session_id="session_1",
    role=Role.User,
    phase=Phase.Exploration,
    salience=0.8,
    depth=1,
    sibling_index=0,
    homogeneity=0.5,
    temporal=0.5,
    complexity=1.0,
    created_at=1000,
)
store.add_turn(turn1)

# Add edges
edge = Edge(
    parent_id="550e8400-e29b-41d4-a716-446655440001",
    child_id="550e8400-e29b-41d4-a716-446655440002",
    edge_type=EdgeType.Reply,
)
store.add_edge(edge)

# Create a slicer with a policy
policy = SlicePolicy(max_nodes=100, max_radius=5)
slicer = ContextSlicer(store, policy)

# Get a slice
slice_export = slicer.slice("550e8400-e29b-41d4-a716-446655440001")
print(f"Slice contains {slice_export.num_turns} turns")
print(f"Turn IDs: {slice_export.turn_ids}")
```
"""

from typing import List, Optional

from ._admissibility_kernel_rs import (
    # Enums
    Role,
    Phase,
    EdgeType,
    # Types
    TurnSnapshot,
    Edge,
    PhaseWeights,
    SlicePolicy,
    SliceExport,
    # Store
    InMemoryGraphStore,
    # Core algorithm
    ContextSlicer,
    # Verification
    TokenVerifier,
    # Constants
    __version__,
    SCHEMA_VERSION,
)


class AdmissibilityKernel:
    """
    High-level interface for the Admissibility Kernel.

    Combines graph store, policy, and slicer for convenient usage.

    Args:
        hmac_secret: Secret for signing admissibility tokens
        max_nodes: Maximum turns in a slice (default: 256)
        max_radius: Maximum graph distance (default: 10)
        salience_weight: Weight for salience in priority (default: 0.3)
        distance_decay: Priority decay per hop (default: 0.9)
        include_siblings: Include sibling turns (default: True)
        max_siblings_per_node: Max siblings per parent (default: 5)

    Example:
        ```python
        kernel = AdmissibilityKernel(hmac_secret=b"my_secret_key")

        # Add turns
        kernel.add_turn(
            turn_id="...",
            session_id="session_1",
            role=Role.User,
            phase=Phase.Consolidation,
            salience=0.8,
        )

        # Add edges
        kernel.add_edge(parent_id="...", child_id="...", edge_type=EdgeType.Reply)

        # Get a slice
        slice_export = kernel.slice("anchor_turn_id")
        ```
    """

    def __init__(
        self,
        hmac_secret: Optional[bytes] = None,
        max_nodes: int = 256,
        max_radius: int = 10,
        salience_weight: float = 0.3,
        distance_decay: float = 0.9,
        include_siblings: bool = True,
        max_siblings_per_node: int = 5,
        phase_weights: Optional[PhaseWeights] = None,
    ):
        self._store = InMemoryGraphStore()
        self._policy = SlicePolicy(
            max_nodes=max_nodes,
            max_radius=max_radius,
            salience_weight=salience_weight,
            distance_decay=distance_decay,
            include_siblings=include_siblings,
            max_siblings_per_node=max_siblings_per_node,
            phase_weights=phase_weights,
        )
        self._hmac_secret = hmac_secret or b"default_secret"
        self._slicer: Optional[ContextSlicer] = None
        self._verifier: Optional[TokenVerifier] = None

    def _get_slicer(self) -> ContextSlicer:
        """Lazily create the slicer."""
        if self._slicer is None:
            self._slicer = ContextSlicer(
                self._store,
                self._policy,
                list(self._hmac_secret),
            )
        return self._slicer

    def _get_verifier(self) -> TokenVerifier:
        """Lazily create the verifier."""
        if self._verifier is None:
            self._verifier = TokenVerifier(list(self._hmac_secret))
        return self._verifier

    def add_turn(
        self,
        turn_id: str,
        session_id: str,
        role: Role = Role.User,
        phase: Phase = Phase.Consolidation,
        salience: float = 0.5,
        depth: int = 1,
        sibling_index: int = 0,
        homogeneity: float = 0.5,
        temporal: float = 0.5,
        complexity: float = 1.0,
        created_at: int = 0,
    ) -> TurnSnapshot:
        """
        Add a turn to the graph.

        Args:
            turn_id: UUID string for the turn
            session_id: Session identifier
            role: Role of the turn author
            phase: Trajectory phase
            salience: Salience score (0.0 to 1.0)
            depth: Depth in conversation tree
            sibling_index: Index among siblings
            homogeneity: Homogeneity score
            temporal: Temporal score
            complexity: Complexity score
            created_at: Unix timestamp

        Returns:
            The created TurnSnapshot
        """
        turn = TurnSnapshot(
            turn_id=turn_id,
            session_id=session_id,
            role=role,
            phase=phase,
            salience=salience,
            depth=depth,
            sibling_index=sibling_index,
            homogeneity=homogeneity,
            temporal=temporal,
            complexity=complexity,
            created_at=created_at,
        )
        self._store.add_turn(turn)
        # Invalidate slicer since store changed
        self._slicer = None
        return turn

    def add_edge(
        self,
        parent_id: str,
        child_id: str,
        edge_type: EdgeType = EdgeType.Reply,
    ) -> Edge:
        """
        Add an edge to the graph.

        Args:
            parent_id: UUID string for parent turn
            child_id: UUID string for child turn
            edge_type: Type of edge

        Returns:
            The created Edge
        """
        edge = Edge(parent_id=parent_id, child_id=child_id, edge_type=edge_type)
        self._store.add_edge(edge)
        # Invalidate slicer since store changed
        self._slicer = None
        return edge

    def slice(self, anchor_turn_id: str) -> SliceExport:
        """
        Create a context slice around an anchor turn.

        Args:
            anchor_turn_id: UUID string for the anchor turn

        Returns:
            SliceExport with admissible turn IDs
        """
        return self._get_slicer().slice(anchor_turn_id)

    def verify(self, slice_export: SliceExport) -> bool:
        """
        Verify a slice's admissibility token.

        Args:
            slice_export: The slice to verify

        Returns:
            True if the token is valid
        """
        return self._get_verifier().verify(slice_export)

    def is_admissible(self, slice_export: SliceExport, turn_id: str) -> bool:
        """
        Check if a turn is admissible in a verified slice.

        Args:
            slice_export: The verified slice
            turn_id: UUID string for the turn to check

        Returns:
            True if the turn is admissible
        """
        return self._get_verifier().is_turn_admissible(slice_export, turn_id)

    @property
    def num_turns(self) -> int:
        """Get the number of turns in the store."""
        return self._store.num_turns

    @property
    def num_edges(self) -> int:
        """Get the number of edges in the store."""
        return self._store.num_edges

    @property
    def policy(self) -> SlicePolicy:
        """Get the slice policy."""
        return self._policy


__all__ = [
    # Version
    "__version__",
    "SCHEMA_VERSION",
    # Enums
    "Role",
    "Phase",
    "EdgeType",
    # Types
    "TurnSnapshot",
    "Edge",
    "PhaseWeights",
    "SlicePolicy",
    "SliceExport",
    # Store
    "InMemoryGraphStore",
    # Core algorithm
    "ContextSlicer",
    # Verification
    "TokenVerifier",
    # High-level API
    "AdmissibilityKernel",
]
