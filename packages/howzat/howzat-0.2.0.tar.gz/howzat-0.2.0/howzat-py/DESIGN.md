# howzat-py

`howzat-py` is a small PyO3 extension module exposing `howzat` backends to Python via `howzat-cli`.

- Python surface area is intentionally minimal: `howzat.Backend(spec).solve(vertices)`.
- `solve()` accepts a contiguous `numpy.ndarray` of `float64` with shape `(n, d)`.
- Timing detail is not exposed from Python.

