# cddlib-sys

Raw FFI bindings to [cddlib](https://github.com/cddlib/cddlib) for convex
polyhedra via the double-description method. Builds a static cddlib (and
optionally GMP) from vendored sources---no network access required.

## Features

| Feature | Description |
|---------|-------------|
| `f64` | Build the f64 backend |
| `gmp` | Build the GMPFLOAT backend |
| `gmprational` | Build the GMPRATIONAL backend |
| `tools` | Build cddlib CLI tools alongside the library |

All numeric backends are enabled by default. Use `--no-default-features` to
select a subset.

## Modules

Bindings are exposed under backend-specific modules: `cddlib_sys::f64`,
`cddlib_sys::gmpfloat`, and `cddlib_sys::gmprational`.

## License

GPL-2.0-or-later (inherited from cddlib). See `LICENSE` for details.
