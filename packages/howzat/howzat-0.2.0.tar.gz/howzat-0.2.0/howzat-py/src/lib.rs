use std::sync::OnceLock;

use howzat_cli::{BackendGeometry, BackendRunConfig};
use hullabaloo::types::RowSet;
use numpy::PyReadonlyArray2;
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;

const DEFAULT_BACKEND_SPEC: &str = "snap@howzat-dd:f64";
static DEFAULT_BACKEND: OnceLock<howzat_cli::Backend> = OnceLock::new();

fn default_backend() -> &'static howzat_cli::Backend {
    DEFAULT_BACKEND.get_or_init(|| {
        DEFAULT_BACKEND_SPEC
            .parse()
            .expect("default backend spec must parse")
    })
}

fn rowset_to_indices(set: &RowSet) -> Vec<usize> {
    let mut out = Vec::with_capacity(set.cardinality());
    out.extend(set.iter().map(|id| id.as_index()));
    out
}

fn rowsets_to_indices(sets: &[RowSet]) -> Vec<Vec<usize>> {
    sets.iter().map(rowset_to_indices).collect()
}

/// Result of a single backend solve.
///
/// Fields:
/// - `spec`: Backend spec actually used.
/// - `dimension`: Ambient dimension `d`.
/// - `vertices`: Number of vertices `n`.
/// - `facets`: Number of facets.
/// - `ridges`: Number of ridges (edges in the facet adjacency / FR graph).
/// - `total_seconds`: Time spent inside the backend (seconds).
/// - `vertex_positions`: Optional vertex coordinates if the backend returned baseline geometry.
/// - `vertex_adjacency`: Vertex adjacency lists.
/// - `facets_to_vertices`: For each facet, the incident vertex indices.
/// - `facet_adjacency`: Facet adjacency lists (FR graph).
/// - `fails`: Backend-specific failure count (pipeline dependent).
/// - `fallbacks`: Backend-specific fallback count (pipeline dependent).
#[pyclass(name = "SolveResult", module = "howzat")]
pub struct SolveResult {
    #[pyo3(get)]
    spec: String,
    #[pyo3(get)]
    dimension: usize,
    #[pyo3(get)]
    vertices: usize,
    #[pyo3(get)]
    facets: usize,
    #[pyo3(get)]
    ridges: usize,
    #[pyo3(get)]
    total_seconds: f64,
    #[pyo3(get)]
    vertex_positions: Option<Vec<Vec<f64>>>,
    vertex_adjacency_sets: Vec<RowSet>,
    facets_to_vertices_sets: Vec<RowSet>,
    facet_adjacency_sets: Vec<RowSet>,
    #[pyo3(get)]
    fails: usize,
    #[pyo3(get)]
    fallbacks: usize,
}

#[pymethods]
impl SolveResult {
    #[getter]
    fn vertex_adjacency(&self) -> Vec<Vec<usize>> {
        rowsets_to_indices(&self.vertex_adjacency_sets)
    }

    #[getter]
    fn facets_to_vertices(&self) -> Vec<Vec<usize>> {
        rowsets_to_indices(&self.facets_to_vertices_sets)
    }

    #[getter]
    fn facet_adjacency(&self) -> Vec<Vec<usize>> {
        rowsets_to_indices(&self.facet_adjacency_sets)
    }

    fn __repr__(&self) -> String {
        format!(
            "howzat.SolveResult(spec={:?}, facets={}, ridges={})",
            self.spec, self.facets, self.ridges
        )
    }
}

/// Opaque backend parsed from a backend spec string.
///
/// Backend spec syntax matches `hirsch sandbox bench --backend` (without `^` / `%` prefixes).
/// The default is `snap@howzat-dd:f64`.
#[pyclass(name = "Backend", module = "howzat")]
pub struct Backend {
    inner: howzat_cli::Backend,
}

fn solve_backend(
    py: Python<'_>,
    backend: &howzat_cli::Backend,
    vertices: PyReadonlyArray2<'_, f64>,
) -> PyResult<SolveResult> {
    let vertices = vertices.as_array();
    let vertex_count = vertices.shape()[0];
    let dim = vertices.shape()[1];
    if vertex_count == 0 || dim == 0 {
        return Err(PyValueError::new_err(
            "vertices must be a non-empty 2D float64 array",
        ));
    }

    let slice = vertices.as_slice().ok_or_else(|| {
        PyValueError::new_err("vertices must be a contiguous (C-order) 2D float64 numpy array")
    })?;

    let run = py
        .detach(|| backend.solve_row_major(slice, vertex_count, dim, &BackendRunConfig::default()))
        .map_err(|err| PyRuntimeError::new_err(err.to_string()))?;

    let howzat_cli::BackendRun {
        spec,
        stats,
        timing,
        geometry,
        fails,
        fallbacks,
        error,
        ..
    } = run;

    if let Some(err) = error {
        return Err(PyRuntimeError::new_err(err));
    }

    let (vertex_positions, vertex_adjacency_sets, facets_to_vertices_sets, facet_adjacency_sets) =
        match geometry {
            BackendGeometry::Baseline(b) => (
                Some(b.vertex_positions),
                b.vertex_adjacency,
                b.facets_to_vertices,
                b.facet_adjacency,
            ),
            BackendGeometry::Input(g) => (
                None,
                g.vertex_adjacency,
                g.facets_to_vertices,
                g.facet_adjacency,
            ),
        };

    Ok(SolveResult {
        spec: spec.to_string(),
        dimension: stats.dimension,
        vertices: stats.vertices,
        facets: stats.facets,
        ridges: stats.ridges,
        total_seconds: timing.total.as_secs_f64(),
        vertex_positions,
        vertex_adjacency_sets,
        facets_to_vertices_sets,
        facet_adjacency_sets,
        fails,
        fallbacks,
    })
}

/// Solve with the cached default backend (`snap@howzat-dd:f64`).
///
/// `vertices` must be a contiguous (C-order) `float64` NumPy array with shape `(n, d)`.
#[pyfunction]
fn solve(py: Python<'_>, vertices: PyReadonlyArray2<'_, f64>) -> PyResult<SolveResult> {
    solve_backend(py, default_backend(), vertices)
}

#[pymethods]
impl Backend {
    #[new]
    #[pyo3(signature = (spec=None))]
    /// Create a backend from a backend spec string.
    ///
    /// If `spec` is `None`, uses the cached default backend (`snap@howzat-dd:f64`).
    fn new(spec: Option<&str>) -> PyResult<Self> {
        let inner = match spec {
            Some(spec) => spec
                .parse()
                .map_err(|err: String| PyValueError::new_err(err))?,
            None => default_backend().clone(),
        };
        Ok(Self { inner })
    }

    fn __repr__(&self) -> String {
        format!("howzat.Backend({:?})", self.inner.to_string())
    }

    fn __str__(&self) -> String {
        self.inner.to_string()
    }

    /// Solve with this backend.
    ///
    /// `vertices` must be a contiguous (C-order) `float64` NumPy array with shape `(n, d)`.
    fn solve(&self, py: Python<'_>, vertices: PyReadonlyArray2<'_, f64>) -> PyResult<SolveResult> {
        solve_backend(py, &self.inner, vertices)
    }
}

/// High-performance polytope backend runner bindings (PyO3).
///
/// Entry points:
/// - `howzat.solve(vertices)` runs with a cached default backend (`snap@howzat-dd:f64`).
/// - `howzat.Backend(spec).solve(vertices)` runs with an explicit backend.
#[pymodule]
fn howzat(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    let _ = default_backend();
    m.add_class::<Backend>()?;
    m.add_class::<SolveResult>()?;
    m.add_function(wrap_pyfunction!(solve, m)?)?;
    Ok(())
}
