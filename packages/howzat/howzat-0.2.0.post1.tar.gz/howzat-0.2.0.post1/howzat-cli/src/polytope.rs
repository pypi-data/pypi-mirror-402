use ::hullabaloo::types::RowSet;

pub mod cddlib {
    use anyhow::{anyhow, ensure};
    use cddlib_rs::{
        CddNumber, Matrix as CddMatrix, NumberType, Polyhedron as CddPolyhedron,
        Representation as CddRepr,
    };

    use crate::vertices::{VerticesF64, VerticesVecVec};

    pub fn vertex_positions_from_generators<N: CddNumber>(
        matrix: &CddMatrix<N>,
    ) -> Result<Vec<Vec<f64>>, anyhow::Error> {
        ensure!(
            matrix.representation() == CddRepr::Generator,
            "expected generator representation when extracting vertices"
        );

        let cols = matrix.cols();
        ensure!(cols >= 2, "generator matrix has too few columns");

        let mut vertices = Vec::with_capacity(matrix.rows());
        for row in 0..matrix.rows() {
            let generator_type = matrix.get_real(row, 0);
            ensure!(
                (generator_type - 1.0).abs() <= 1e-9,
                "generator row {row} is not a vertex (type={generator_type})"
            );

            let mut coords = Vec::with_capacity(cols - 1);
            for col in 1..cols {
                coords.push(matrix.get_real(row, col));
            }
            vertices.push(coords);
        }
        Ok(vertices)
    }

    fn build_polyhedron<N: CddNumber, V: VerticesF64>(
        vertices: &V,
        number_type: NumberType,
    ) -> Result<CddPolyhedron<N>, anyhow::Error> {
        ensure!(vertices.vertex_count() > 0, "cddlib needs at least one vertex");
        let dim = vertices.dim();
        ensure!(dim > 0, "cddlib vertices must have positive dimension");
        ensure!(
            vertices.rows().all(|v| v.len() == dim),
            "cddlib vertices must have consistent dimension"
        );

        let mut matrix: CddMatrix<N> =
            CddMatrix::new(vertices.vertex_count(), dim + 1, CddRepr::Generator, number_type)?;
        for (row, coords) in vertices.rows().enumerate() {
            matrix.set_generator_type(row, true);
            for (col, &v) in coords.iter().enumerate() {
                ensure!(v.is_finite(), "non-finite vertex coordinate {v}");
                matrix.set_real(row, col + 1, v);
            }
        }

        CddPolyhedron::from_generators_matrix(&matrix).map_err(Into::into)
    }

    pub(crate) fn build_polyhedron_f64_vertices<V: VerticesF64>(
        vertices: &V,
    ) -> Result<CddPolyhedron<f64>, anyhow::Error> {
        build_polyhedron::<f64, V>(vertices, NumberType::Real)
    }

    pub fn build_polyhedron_f64(vertices: &[Vec<f64>]) -> Result<CddPolyhedron<f64>, anyhow::Error> {
        build_polyhedron_f64_vertices(&VerticesVecVec::new(vertices))
    }

    pub(crate) fn build_polyhedron_gmp_vertices<V: VerticesF64>(
        vertices: &V,
    ) -> Result<CddPolyhedron<cddlib_rs::CddFloat>, anyhow::Error> {
        build_polyhedron::<cddlib_rs::CddFloat, V>(vertices, NumberType::Real)
    }

    pub fn build_polyhedron_gmp(vertices: &[Vec<f64>]) -> Result<CddPolyhedron<cddlib_rs::CddFloat>, anyhow::Error> {
        build_polyhedron_gmp_vertices(&VerticesVecVec::new(vertices))
    }

    pub(crate) fn build_polyhedron_rational_vertices<V: VerticesF64>(
        vertices: &V,
    ) -> Result<CddPolyhedron<cddlib_rs::CddRational>, anyhow::Error> {
        build_polyhedron::<cddlib_rs::CddRational, V>(vertices, NumberType::Rational)
    }

    pub fn build_polyhedron_rational(
        vertices: &[Vec<f64>],
    ) -> Result<CddPolyhedron<cddlib_rs::CddRational>, anyhow::Error> {
        build_polyhedron_rational_vertices(&VerticesVecVec::new(vertices))
    }

    pub fn drum_width_rational(
        poly: &CddPolyhedron<cddlib_rs::CddRational>,
        vertices: &[Vec<f64>],
    ) -> Result<usize, anyhow::Error> {
        let cols = vertices
            .first()
            .map(|v| v.len())
            .ok_or_else(|| anyhow!("need at least one vertex"))?;
        ensure!(cols >= 1, "vertices must have positive dimension");
        let height_col = cols - 1;

        let mut top = Vec::new();
        let mut bot = Vec::new();
        for (idx, v) in vertices.iter().enumerate() {
            let h = v
                .get(height_col)
                .copied()
                .ok_or_else(|| anyhow!("vertex {idx} missing height coordinate"))?;
            if h > 0.5 {
                top.push(idx);
            } else {
                bot.push(idx);
            }
        }
        ensure!(
            !top.is_empty() && !bot.is_empty(),
            "expected both top and bot vertices"
        );

        let adjacency = poly.adjacency()?.to_adjacency_lists();
        let facets_to_vertices = poly.incidence()?.to_adjacency_lists();

        let num_vertices = vertices.len();
        let mut is_top = vec![false; num_vertices];
        let mut is_bot = vec![false; num_vertices];
        for &v in &top {
            is_top[v] = true;
        }
        for &v in &bot {
            is_bot[v] = true;
        }

        let mut top_facet = None;
        let mut bot_facet = None;
        for (facet_idx, verts) in facets_to_vertices.iter().enumerate() {
            if verts.len() == top.len() && verts.iter().all(|&v| is_top[v]) {
                ensure!(
                    top_facet.replace(facet_idx).is_none(),
                    "multiple top base facets"
                );
            }
            if verts.len() == bot.len() && verts.iter().all(|&v| is_bot[v]) {
                ensure!(
                    bot_facet.replace(facet_idx).is_none(),
                    "multiple bot base facets"
                );
            }
        }

        let top_facet = top_facet.ok_or_else(|| anyhow!("failed to locate drum top base facet"))?;
        let bot_facet = bot_facet.ok_or_else(|| anyhow!("failed to locate drum bot base facet"))?;

        let g = hullabaloo::Graph { adjacency };
        g.distance(top_facet, bot_facet)
            .ok_or_else(|| anyhow!("disconnected graph"))
    }
}

pub mod howzat {
    use anyhow::{anyhow, ensure};
    use calculo::num::Num;
    use howzat::dd::ConeOptions;
    use howzat::dd::DefaultNormalizer;

    use crate::vertices::{VerticesF64, VerticesVecVec};

    type HowzatPoly<N> = howzat::polyhedron::PolyhedronOutput<N, hullabaloo::types::Generator>;
    type HowzatMatrix<N> = howzat::matrix::LpMatrix<N, hullabaloo::types::Generator>;

    pub(crate) fn build_poly_dd_vertices<N: Num + DefaultNormalizer, V: VerticesF64>(
        vertices: &V,
        options: &ConeOptions,
        poly_options: howzat::polyhedron::PolyhedronOptions,
    ) -> Result<HowzatPoly<N>, anyhow::Error> {
        let eps = N::default_eps();
        let matrix = build_generator_matrix_vertices::<N, V>(vertices)?;

        HowzatPoly::<N>::from_matrix_dd_with_options_and_eps(matrix, options.clone(), poly_options, eps)
            .map_err(|e| anyhow!("howzat-dd conversion failed: {e:?}"))
    }

    pub fn build_poly_dd<N: Num + DefaultNormalizer>(
        vertices: &[Vec<f64>],
        options: &ConeOptions,
        poly_options: howzat::polyhedron::PolyhedronOptions,
    ) -> Result<HowzatPoly<N>, anyhow::Error> {
        build_poly_dd_vertices(&VerticesVecVec::new(vertices), options, poly_options)
    }

    pub(crate) fn build_generator_matrix_vertices<N: Num, V: VerticesF64>(
        vertices: &V,
    ) -> Result<HowzatMatrix<N>, anyhow::Error> {
        ensure!(vertices.vertex_count() > 0, "howzat needs at least one vertex");

        let mut generator_rows = Vec::with_capacity(vertices.vertex_count());
        for coords in vertices.rows() {
            let mut row = Vec::with_capacity(coords.len() + 1);
                row.push(N::one());
                for &value in coords {
                    let value =
                        N::try_from_f64(value).ok_or_else(|| anyhow!("non-finite vertex coordinate {value}"))?;
                    row.push(value);
                }
            generator_rows.push(row);
        }

        Ok(
            howzat::matrix::LpMatrixBuilder::<N, hullabaloo::types::Generator>::from_rows(generator_rows)
                .build(),
        )
    }

    pub fn build_generator_matrix<N: Num>(
        vertices: &[Vec<f64>],
    ) -> Result<HowzatMatrix<N>, anyhow::Error> {
        build_generator_matrix_vertices(&VerticesVecVec::new(vertices))
    }
}

pub fn rowset_from_list(capacity: usize, members: &[usize]) -> RowSet {
    let mut set = RowSet::new(capacity);
    for &m in members {
        set.insert(m);
    }
    set
}

pub fn rowsets_from_adjacency_lists(adjacency: &[Vec<usize>], capacity: usize) -> Vec<RowSet> {
    adjacency
        .iter()
        .map(|neighbors| rowset_from_list(capacity, neighbors))
        .collect()
}
