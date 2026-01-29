//! Python bindings for the Admissibility Kernel.
//!
//! Provides deterministic context slicing for conversation DAGs.

use pyo3::prelude::*;
use pyo3::exceptions::{PyValueError, PyRuntimeError};
use std::sync::Arc;
use parking_lot::RwLock;

use admissibility_kernel::{
    TurnId as RustTurnId,
    TurnSnapshot as RustTurnSnapshot,
    Edge as RustEdge,
    EdgeType as RustEdgeType,
    Role as RustRole,
    Phase as RustPhase,
    SlicePolicyV1 as RustSlicePolicyV1,
    PhaseWeights as RustPhaseWeights,
    SliceExport as RustSliceExport,
    ContextSlicer as RustContextSlicer,
    AdmissibleEvidenceBundle,
    store::InMemoryGraphStore as RustInMemoryGraphStore,
    TokenVerifier as RustTokenVerifier,
    VerificationMode as RustVerificationMode,
    CacheConfig as RustCacheConfig,
};

/// Role enum for turn authors.
#[pyclass(eq, eq_int)]
#[derive(Clone, Copy, PartialEq)]
pub enum Role {
    User,
    Assistant,
    System,
    Tool,
}

impl From<Role> for RustRole {
    fn from(role: Role) -> Self {
        match role {
            Role::User => RustRole::User,
            Role::Assistant => RustRole::Assistant,
            Role::System => RustRole::System,
            Role::Tool => RustRole::Tool,
        }
    }
}

impl From<RustRole> for Role {
    fn from(role: RustRole) -> Self {
        match role {
            RustRole::User => Role::User,
            RustRole::Assistant => Role::Assistant,
            RustRole::System => Role::System,
            RustRole::Tool => Role::Tool,
        }
    }
}

/// Phase enum for trajectory phases.
#[pyclass(eq, eq_int)]
#[derive(Clone, Copy, PartialEq)]
pub enum Phase {
    Exploration,
    Debugging,
    Planning,
    Consolidation,
    Synthesis,
}

impl From<Phase> for RustPhase {
    fn from(phase: Phase) -> Self {
        match phase {
            Phase::Exploration => RustPhase::Exploration,
            Phase::Debugging => RustPhase::Debugging,
            Phase::Planning => RustPhase::Planning,
            Phase::Consolidation => RustPhase::Consolidation,
            Phase::Synthesis => RustPhase::Synthesis,
        }
    }
}

impl From<RustPhase> for Phase {
    fn from(phase: RustPhase) -> Self {
        match phase {
            RustPhase::Exploration => Phase::Exploration,
            RustPhase::Debugging => Phase::Debugging,
            RustPhase::Planning => Phase::Planning,
            RustPhase::Consolidation => Phase::Consolidation,
            RustPhase::Synthesis => Phase::Synthesis,
        }
    }
}

/// Edge type enum.
#[pyclass(eq, eq_int)]
#[derive(Clone, Copy, PartialEq)]
pub enum EdgeType {
    Reply,
    Branch,
    Reference,
    Default,
}

impl From<EdgeType> for RustEdgeType {
    fn from(edge_type: EdgeType) -> Self {
        match edge_type {
            EdgeType::Reply => RustEdgeType::Reply,
            EdgeType::Branch => RustEdgeType::Branch,
            EdgeType::Reference => RustEdgeType::Reference,
            EdgeType::Default => RustEdgeType::Default,
        }
    }
}

impl From<RustEdgeType> for EdgeType {
    fn from(edge_type: RustEdgeType) -> Self {
        match edge_type {
            RustEdgeType::Reply => EdgeType::Reply,
            RustEdgeType::Branch => EdgeType::Branch,
            RustEdgeType::Reference => EdgeType::Reference,
            RustEdgeType::Default => EdgeType::Default,
        }
    }
}

/// A turn snapshot in the conversation graph.
#[pyclass]
#[derive(Clone)]
pub struct TurnSnapshot {
    inner: RustTurnSnapshot,
}

#[pymethods]
impl TurnSnapshot {
    /// Create a new turn snapshot.
    #[new]
    #[pyo3(signature = (turn_id, session_id, role, phase, salience, depth, sibling_index, homogeneity, temporal, complexity, created_at))]
    pub fn new(
        turn_id: &str,
        session_id: String,
        role: Role,
        phase: Phase,
        salience: f32,
        depth: u32,
        sibling_index: u32,
        homogeneity: f32,
        temporal: f32,
        complexity: f32,
        created_at: i64,
    ) -> PyResult<Self> {
        let rust_turn_id = RustTurnId::from_str(turn_id)
            .map_err(|e| PyValueError::new_err(format!("Invalid turn ID: {}", e)))?;

        Ok(Self {
            inner: RustTurnSnapshot::new(
                rust_turn_id,
                session_id,
                role.into(),
                phase.into(),
                salience,
                depth,           // trajectory_depth
                sibling_index,   // trajectory_sibling_order
                homogeneity,     // trajectory_homogeneity
                temporal,        // trajectory_temporal
                complexity,      // trajectory_complexity
                created_at,
            ),
        })
    }

    /// Get the turn ID as a string.
    #[getter]
    pub fn turn_id(&self) -> String {
        self.inner.id.to_string()
    }

    /// Get the session ID.
    #[getter]
    pub fn session_id(&self) -> String {
        self.inner.session_id.clone()
    }

    /// Get the role.
    #[getter]
    pub fn role(&self) -> Role {
        self.inner.role.into()
    }

    /// Get the phase.
    #[getter]
    pub fn phase(&self) -> Phase {
        self.inner.phase.into()
    }

    /// Get the salience score.
    #[getter]
    pub fn salience(&self) -> f32 {
        self.inner.salience
    }

    /// Get the depth in the conversation tree.
    #[getter]
    pub fn depth(&self) -> u32 {
        self.inner.trajectory_depth
    }

    /// Get the sibling index.
    #[getter]
    pub fn sibling_index(&self) -> u32 {
        self.inner.trajectory_sibling_order
    }

    /// Get the homogeneity score.
    #[getter]
    pub fn homogeneity(&self) -> f32 {
        self.inner.trajectory_homogeneity
    }

    /// Get the temporal score.
    #[getter]
    pub fn temporal(&self) -> f32 {
        self.inner.trajectory_temporal
    }

    /// Get the complexity score.
    #[getter]
    pub fn complexity(&self) -> f32 {
        self.inner.trajectory_complexity
    }

    /// Get the created_at timestamp.
    #[getter]
    pub fn created_at(&self) -> i64 {
        self.inner.created_at
    }

    fn __repr__(&self) -> String {
        format!(
            "TurnSnapshot(id={}, role={:?}, phase={:?}, salience={})",
            self.inner.id,
            self.inner.role,
            self.inner.phase,
            self.inner.salience
        )
    }
}

/// An edge in the conversation graph.
#[pyclass]
#[derive(Clone)]
pub struct Edge {
    inner: RustEdge,
}

#[pymethods]
impl Edge {
    /// Create a new edge.
    #[new]
    pub fn new(parent_id: &str, child_id: &str, edge_type: EdgeType) -> PyResult<Self> {
        let parent = RustTurnId::from_str(parent_id)
            .map_err(|e| PyValueError::new_err(format!("Invalid parent ID: {}", e)))?;
        let child = RustTurnId::from_str(child_id)
            .map_err(|e| PyValueError::new_err(format!("Invalid child ID: {}", e)))?;

        Ok(Self {
            inner: RustEdge::new(parent, child, edge_type.into()),
        })
    }

    /// Get the parent turn ID.
    #[getter]
    pub fn parent_id(&self) -> String {
        self.inner.parent.to_string()
    }

    /// Get the child turn ID.
    #[getter]
    pub fn child_id(&self) -> String {
        self.inner.child.to_string()
    }

    /// Get the edge type.
    #[getter]
    pub fn edge_type(&self) -> EdgeType {
        self.inner.edge_type.into()
    }

    fn __repr__(&self) -> String {
        format!(
            "Edge({} -> {}, type={:?})",
            self.inner.parent, self.inner.child, self.inner.edge_type
        )
    }
}

/// Phase weights for the slice policy.
#[pyclass]
#[derive(Clone)]
pub struct PhaseWeights {
    inner: RustPhaseWeights,
}

#[pymethods]
impl PhaseWeights {
    /// Create new phase weights.
    #[new]
    #[pyo3(signature = (exploration=0.3, debugging=0.5, consolidation=0.6, planning=0.9, synthesis=1.0))]
    pub fn new(
        exploration: f32,
        debugging: f32,
        consolidation: f32,
        planning: f32,
        synthesis: f32,
    ) -> Self {
        Self {
            inner: RustPhaseWeights {
                exploration,
                debugging,
                consolidation,
                planning,
                synthesis,
            },
        }
    }

    /// Create default phase weights.
    #[staticmethod]
    pub fn default() -> Self {
        Self {
            inner: RustPhaseWeights::default(),
        }
    }
}

/// Slice policy configuration.
#[pyclass]
#[derive(Clone)]
pub struct SlicePolicy {
    inner: RustSlicePolicyV1,
}

#[pymethods]
impl SlicePolicy {
    /// Create a new slice policy.
    #[new]
    #[pyo3(signature = (max_nodes=256, max_radius=10, salience_weight=0.3, distance_decay=0.9, include_siblings=true, max_siblings_per_node=5, phase_weights=None))]
    pub fn new(
        max_nodes: usize,
        max_radius: u32,
        salience_weight: f32,
        distance_decay: f32,
        include_siblings: bool,
        max_siblings_per_node: usize,
        phase_weights: Option<PhaseWeights>,
    ) -> Self {
        let mut policy = RustSlicePolicyV1::default();
        policy.max_nodes = max_nodes;
        policy.max_radius = max_radius;
        policy.salience_weight = salience_weight;
        policy.distance_decay = distance_decay;
        policy.include_siblings = include_siblings;
        policy.max_siblings_per_node = max_siblings_per_node;
        if let Some(weights) = phase_weights {
            policy.phase_weights = weights.inner;
        }
        Self { inner: policy }
    }

    /// Create a default policy.
    #[staticmethod]
    pub fn default() -> Self {
        Self {
            inner: RustSlicePolicyV1::default(),
        }
    }

    /// Get the policy ID.
    #[getter]
    pub fn policy_id(&self) -> String {
        self.inner.policy_id().to_string()
    }

    /// Get the params hash.
    #[getter]
    pub fn params_hash(&self) -> String {
        self.inner.params_hash()
    }

    #[getter]
    pub fn max_nodes(&self) -> usize {
        self.inner.max_nodes
    }

    #[getter]
    pub fn max_radius(&self) -> u32 {
        self.inner.max_radius
    }
}

/// Exported context slice.
#[pyclass]
pub struct SliceExport {
    inner: RustSliceExport,
}

#[pymethods]
impl SliceExport {
    /// Get the slice ID (fingerprint).
    #[getter]
    pub fn slice_id(&self) -> String {
        self.inner.slice_id.as_str().to_string()
    }

    /// Get the anchor turn ID.
    #[getter]
    pub fn anchor_turn_id(&self) -> String {
        self.inner.anchor_turn_id.to_string()
    }

    /// Get all turn IDs in the slice.
    #[getter]
    pub fn turn_ids(&self) -> Vec<String> {
        self.inner.turns.iter().map(|t| t.id.to_string()).collect()
    }

    /// Get the number of turns.
    #[getter]
    pub fn num_turns(&self) -> usize {
        self.inner.turns.len()
    }

    /// Get the policy ID used.
    #[getter]
    pub fn policy_id(&self) -> String {
        self.inner.policy_id.clone()
    }

    /// Get the policy params hash.
    #[getter]
    pub fn policy_params_hash(&self) -> String {
        self.inner.policy_params_hash.clone()
    }

    /// Get the graph snapshot hash.
    #[getter]
    pub fn graph_snapshot_hash(&self) -> String {
        self.inner.graph_snapshot_hash.as_str().to_string()
    }

    /// Get the admissibility token.
    #[getter]
    pub fn admissibility_token(&self) -> String {
        self.inner.admissibility_token.as_str().to_string()
    }

    /// Check if a turn ID is in this slice.
    pub fn contains_turn(&self, turn_id: &str) -> PyResult<bool> {
        let id = RustTurnId::from_str(turn_id)
            .map_err(|e| PyValueError::new_err(format!("Invalid turn ID: {}", e)))?;
        Ok(self.inner.contains_turn(&id))
    }

    /// Verify the admissibility token with a secret.
    pub fn verify_token(&self, secret: &[u8]) -> bool {
        self.inner.verify_token(secret)
    }

    fn __repr__(&self) -> String {
        format!(
            "SliceExport(slice_id={}, anchor={}, turns={})",
            self.inner.slice_id.as_str(),
            self.inner.anchor_turn_id,
            self.inner.turns.len()
        )
    }
}

/// In-memory graph store for testing and small graphs.
#[pyclass]
pub struct InMemoryGraphStore {
    inner: Arc<RwLock<RustInMemoryGraphStore>>,
}

#[pymethods]
impl InMemoryGraphStore {
    /// Create a new empty graph store.
    #[new]
    pub fn new() -> Self {
        Self {
            inner: Arc::new(RwLock::new(RustInMemoryGraphStore::new())),
        }
    }

    /// Add a turn to the store.
    pub fn add_turn(&self, turn: &TurnSnapshot) {
        self.inner.write().add_turn(turn.inner.clone());
    }

    /// Add an edge to the store.
    pub fn add_edge(&self, edge: &Edge) {
        self.inner.write().add_edge(edge.inner.clone());
    }

    /// Get the number of turns.
    #[getter]
    pub fn num_turns(&self) -> usize {
        self.inner.read().num_turns()
    }

    /// Get the number of edges.
    #[getter]
    pub fn num_edges(&self) -> usize {
        self.inner.read().num_edges()
    }

    fn __repr__(&self) -> String {
        let store = self.inner.read();
        format!(
            "InMemoryGraphStore(turns={}, edges={})",
            store.num_turns(),
            store.num_edges()
        )
    }
}

/// The context slicer - main algorithm for deterministic slicing.
#[pyclass]
pub struct ContextSlicer {
    store: Arc<RwLock<RustInMemoryGraphStore>>,
    policy: RustSlicePolicyV1,
    hmac_secret: Vec<u8>,
    runtime: tokio::runtime::Runtime,
}

#[pymethods]
impl ContextSlicer {
    /// Create a new context slicer.
    #[new]
    #[pyo3(signature = (store, policy, hmac_secret=None))]
    pub fn new(store: &InMemoryGraphStore, policy: &SlicePolicy, hmac_secret: Option<Vec<u8>>) -> PyResult<Self> {
        let secret = hmac_secret.unwrap_or_else(|| b"default_secret_for_testing".to_vec());
        let runtime = tokio::runtime::Runtime::new()
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to create runtime: {}", e)))?;

        Ok(Self {
            store: Arc::clone(&store.inner),
            policy: policy.inner.clone(),
            hmac_secret: secret,
            runtime,
        })
    }

    /// Create a context slice around an anchor turn.
    ///
    /// Returns a SliceExport with the admissible turn IDs.
    pub fn slice(&self, anchor_turn_id: &str) -> PyResult<SliceExport> {
        let anchor_id = RustTurnId::from_str(anchor_turn_id)
            .map_err(|e| PyValueError::new_err(format!("Invalid anchor turn ID: {}", e)))?;

        // Create a slicer with a snapshot of the store
        let store_snapshot = self.store.read().clone();
        let slicer = RustContextSlicer::new(
            Arc::new(store_snapshot),
            self.policy.clone(),
            self.hmac_secret.clone(),
        );

        let bundle: AdmissibleEvidenceBundle = self.runtime.block_on(async {
            slicer.slice(anchor_id).await
        }).map_err(|e| PyRuntimeError::new_err(format!("Slice error: {}", e)))?;

        // Extract the SliceExport from the AdmissibleEvidenceBundle
        Ok(SliceExport {
            inner: bundle.slice().clone(),
        })
    }

    /// Get the policy.
    #[getter]
    pub fn policy(&self) -> SlicePolicy {
        SlicePolicy {
            inner: self.policy.clone(),
        }
    }
}

/// Token verifier for validating admissibility tokens.
#[pyclass]
pub struct TokenVerifier {
    inner: RustTokenVerifier,
}

#[pymethods]
impl TokenVerifier {
    /// Create a new token verifier.
    #[new]
    #[pyo3(signature = (hmac_secret, cache_size=None, use_cache=true))]
    pub fn new(hmac_secret: Vec<u8>, cache_size: Option<usize>, use_cache: bool) -> Self {
        let mode = if use_cache {
            let config = RustCacheConfig {
                max_entries: cache_size.unwrap_or(10_000),
                enabled: true,
            };
            RustVerificationMode::Cached {
                secret: hmac_secret,
                config,
            }
        } else {
            RustVerificationMode::LocalSecret { secret: hmac_secret }
        };

        Self {
            inner: RustTokenVerifier::new(mode),
        }
    }

    /// Verify a slice's admissibility token.
    pub fn verify(&self, slice: &SliceExport) -> bool {
        self.inner.verify_slice(&slice.inner).is_valid
    }

    /// Check if a turn is admissible in a verified slice.
    pub fn is_turn_admissible(&self, slice: &SliceExport, turn_id: &str) -> PyResult<bool> {
        let id = RustTurnId::from_str(turn_id)
            .map_err(|e| PyValueError::new_err(format!("Invalid turn ID: {}", e)))?;

        let result = self.inner.verify_slice(&slice.inner);
        if result.is_valid {
            Ok(slice.inner.contains_turn(&id))
        } else {
            Ok(false)
        }
    }
}

/// The admissibility_kernel Python module.
#[pymodule]
fn _admissibility_kernel_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Enums
    m.add_class::<Role>()?;
    m.add_class::<Phase>()?;
    m.add_class::<EdgeType>()?;

    // Types
    m.add_class::<TurnSnapshot>()?;
    m.add_class::<Edge>()?;
    m.add_class::<PhaseWeights>()?;
    m.add_class::<SlicePolicy>()?;
    m.add_class::<SliceExport>()?;

    // Store
    m.add_class::<InMemoryGraphStore>()?;

    // Core algorithm
    m.add_class::<ContextSlicer>()?;

    // Verification
    m.add_class::<TokenVerifier>()?;

    // Version
    m.add("__version__", "0.1.0")?;
    m.add("SCHEMA_VERSION", admissibility_kernel::GRAPH_KERNEL_SCHEMA_VERSION)?;

    Ok(())
}
