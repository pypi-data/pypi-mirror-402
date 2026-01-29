# lrslib-sys

Raw FFI bindings to [lrslib](https://cgm.cs.mcgill.ca/~avis/C/lrs.html), David
Avis' lexicographic reverse-search library for convex polyhedra. Builds a
static lrslib from vendored sources---no network access required.

## Features

| Feature | Description |
|---------|-------------|
| - | Fixed-width `LRSLONG` arithmetic (128-bit when supported)---faster but can overflow |
| `gmp` | Bundled `mini-gmp` backend for arbitrary-precision integers |

## License

GPL-2.0-or-later (inherited from lrslib). See `LICENSE` for details.
