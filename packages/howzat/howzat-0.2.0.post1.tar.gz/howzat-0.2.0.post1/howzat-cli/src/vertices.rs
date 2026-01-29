use anyhow::ensure;

pub(crate) trait VerticesF64 {
    type Rows<'a>: Iterator<Item = &'a [f64]>
    where
        Self: 'a;

    fn vertex_count(&self) -> usize;
    fn dim(&self) -> usize;
    fn rows(&self) -> Self::Rows<'_>;

    fn as_vecvec(&self) -> Option<&[Vec<f64>]> {
        None
    }
}

#[derive(Clone, Copy)]
pub(crate) struct VerticesVecVec<'a> {
    vertices: &'a [Vec<f64>],
}

impl<'a> VerticesVecVec<'a> {
    pub(crate) fn new(vertices: &'a [Vec<f64>]) -> Self {
        Self { vertices }
    }
}

impl VerticesF64 for VerticesVecVec<'_> {
    type Rows<'a>
        = std::iter::Map<std::slice::Iter<'a, Vec<f64>>, fn(&'a Vec<f64>) -> &'a [f64]>
    where
        Self: 'a;

    fn vertex_count(&self) -> usize {
        self.vertices.len()
    }

    fn dim(&self) -> usize {
        self.vertices.first().map_or(0, |v| v.len())
    }

    fn rows(&self) -> Self::Rows<'_> {
        fn vec_as_slice(row: &Vec<f64>) -> &[f64] {
            row
        }

        self.vertices.iter().map(vec_as_slice)
    }

    fn as_vecvec(&self) -> Option<&[Vec<f64>]> {
        Some(self.vertices)
    }
}

#[derive(Clone, Copy)]
pub(crate) struct VerticesRowMajor<'a> {
    coords: &'a [f64],
    vertex_count: usize,
    dim: usize,
}

impl<'a> VerticesRowMajor<'a> {
    pub(crate) fn new(coords: &'a [f64], vertex_count: usize, dim: usize) -> Result<Self, anyhow::Error> {
        ensure!(vertex_count > 0, "need at least one vertex");
        ensure!(dim > 0, "need positive vertex dimension");
        ensure!(
            coords.len() == vertex_count.saturating_mul(dim),
            "expected {vertex_count}x{dim} coords but got {}",
            coords.len()
        );
        Ok(Self {
            coords,
            vertex_count,
            dim,
        })
    }
}

impl VerticesF64 for VerticesRowMajor<'_> {
    type Rows<'a> = std::slice::ChunksExact<'a, f64>
    where
        Self: 'a;

    fn vertex_count(&self) -> usize {
        self.vertex_count
    }

    fn dim(&self) -> usize {
        self.dim
    }

    fn rows(&self) -> Self::Rows<'_> {
        self.coords.chunks_exact(self.dim)
    }
}

