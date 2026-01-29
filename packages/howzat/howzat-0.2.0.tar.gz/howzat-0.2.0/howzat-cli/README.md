# howzat-cli

`howzat-cli` is a small Rust library providing:
- parsing backend specifications from their string encoding, and
- running the chosen backend synchronously on `f64` vertex data.

This crate is shared by `kompute-hirsch` (`hirsch sandbox bench`) and the Python bindings crate.

## Backend Specs

Backend specs are strings like:
- `snap@howzat-dd:f64` (default)
- `howzat-dd:f64`
- `cddlib:gmprational`
- `lrslib+hlbl`

For CLI-style parsing (supporting `^` / `%` prefixes), use `BackendArg`:

```rust
use howzat_cli::BackendArg;

let arg: BackendArg = "^snap@howzat-dd:f64".parse().unwrap();
assert!(arg.authoritative);
```

For parsing only the backend itself, use `Backend`:

```rust
use howzat_cli::Backend;

let backend = Backend::parse("snap@howzat-dd:f64").unwrap();
```

## Running

The core entrypoint is `Backend::solve_row_major`, which accepts a contiguous row-major buffer of
`f64` coordinates.

```rust
use howzat_cli::{Backend, BackendRunConfig};

let backend = Backend::parse("snap@howzat-dd:f64").unwrap();
let config = BackendRunConfig::default();

let coords = [
    0.0, 0.0,
    1.0, 0.0,
    0.0, 1.0,
];
let run = backend.solve_row_major(&coords, 3, 2, &config).unwrap();
println!("{}", run.spec);
println!("{:?}", run.stats);
```
