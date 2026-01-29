# howzat

Dynamic double-description method for convex cones and polytopes. Small API,
pluggable numeric backends, predictable behavior.

## Features

- **Cone/polytope primitives**: Adjacency queries, tableau-based convex hull routines.
- **Backend-agnostic**: Works with `rug` (GMP) or `dashu` (pure-Rust) arbitrary precision.
- **Minimal footprint**: Few dependencies, optional tracing for debugging.

## Example

```rust
use howzat::dd::Cone;

let generators = vec![vec![1, 0], vec![0, 1], vec![1, 1]];
let cone = Cone::from_generators(&generators)?;
let adjacency = cone.vertex_adjacency()?;

assert_eq!(adjacency.num_vertices(), 3);
```

## License

AGPL-3.0-only. See `LICENSE` for details.
