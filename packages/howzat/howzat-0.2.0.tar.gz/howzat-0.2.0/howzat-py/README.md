# howzat (Python)

Python bindings for `howzat-cli` via PyO3.

## Install

From PyPI (once published):

```bash
python -m pip install howzat
```

Build from source (requires a Rust toolchain):

```bash
python -m pip install .
```

Force a local source build (even if wheels exist), and optionally enable CPU-native codegen:

```bash
RUSTFLAGS="-C target-cpu=native" python -m pip install --no-binary howzat howzat
```

Prebuilt wheels are compiled for a portable baseline CPU (not `target-cpu=native`).

## Usage

```python
import numpy as np
import howzat

verts = np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=np.float64)

res = howzat.solve(verts)  # cached default backend: "snap@howzat-dd:f64"
# res = howzat.Backend().solve(verts)  # same as above
# res = howzat.Backend("howzat-lrs:rug").solve(verts)  # explicit backend

print(res.facets, res.ridges)
print(res.facet_adjacency)
```

Input vertices must be a contiguous (C-order) `numpy.ndarray` of `float64` with shape `(n, d)`.

## Backend Specs

`howzat.Backend(spec)` accepts the same backend spec strings as `hirsch sandbox bench --backend`,
except the Python API does not accept the `^` / `%` prefix markers.

Syntax (high level): `[PURIFIER@]KIND[:SPEC]`

Common examples:
- `snap@howzat-dd:f64` (default)
- `howzat-dd:f64`
- `howzat-dd:f64[eps[1e-12]]`
- `cddlib:gmprational`
- `cddlib+hlbl:f64`
- `lrslib+hlbl` (defaults to `lrslib+hlbl:gmpint`)

## API

- `howzat.solve(vertices) -> SolveResult`  
  Uses a cached default backend (`snap@howzat-dd:f64`).
- `howzat.Backend(spec: str | None = None)`  
  Parses and stores a backend; `None` selects the cached default backend.
- `Backend.solve(vertices) -> SolveResult`  
  Runs the backend synchronously, single-threaded on the provided vertex set.

## SolveResult

`SolveResult` contains:
- `spec: str` backend spec actually used
- `dimension: int` ambient dimension `d`
- `vertices: int` number of vertices `n`
- `facets: int` number of facets
- `ridges: int` number of ridges (edges in the facet adjacency / FR graph)
- `total_seconds: float` time spent inside the backend (seconds)
- `vertex_positions: list[list[float]] | None` vertex coordinates if the backend returned baseline geometry
- `vertex_adjacency: list[list[int]]` vertex adjacency lists (length `vertices`)
- `facets_to_vertices: list[list[int]]` for each facet, the incident vertex indices
- `facet_adjacency: list[list[int]]` facet adjacency lists (FR graph)
- `fails: int` backend-specific failure count (pipeline dependent)
- `fallbacks: int` backend-specific fallback count (pipeline dependent)
