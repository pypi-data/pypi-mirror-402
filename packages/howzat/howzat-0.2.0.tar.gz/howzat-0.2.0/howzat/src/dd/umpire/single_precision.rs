use crate::dd::DefaultNormalizer;
use crate::dd::diag;
use crate::dd::{Ray, RayClass, RayId};
use crate::matrix::{LpMatrix, Matrix};
use calculo::linalg;
use calculo::num::{CoerceFrom, Epsilon, Normalizer, Num, Sign};
use hullabaloo::types::{Representation, Row, RowSet};

use super::policies::{HalfspacePolicy, LexMin};
use super::{ConeCtx, Umpire};

pub trait Purifier<N: Num>: Clone {
    const ENABLED: bool = true;

    fn purify<E: Epsilon<N>>(
        &mut self,
        rows: &Matrix<N>,
        eps: &E,
        row: Row,
        ray1_zero_set: &RowSet,
        ray2_zero_set: &RowSet,
    ) -> Option<Vec<N>>;

    #[inline(always)]
    fn purify_from_zero_set<E: Epsilon<N>>(
        &mut self,
        _rows: &Matrix<N>,
        _eps: &E,
        _expected_zero: &RowSet,
    ) -> Option<Vec<N>> {
        None
    }
}

#[derive(Clone, Copy, Debug, Default)]
pub struct NoPurifier;

impl<N: Num> Purifier<N> for NoPurifier {
    const ENABLED: bool = false;

    #[inline(always)]
    fn purify<E: Epsilon<N>>(
        &mut self,
        _rows: &Matrix<N>,
        _eps: &E,
        _row: Row,
        _ray1_zero_set: &RowSet,
        _ray2_zero_set: &RowSet,
    ) -> Option<Vec<N>> {
        None
    }
}

#[derive(Clone, Debug)]
pub struct SnapPurifier {
    expected_zero: RowSet,
}

impl Default for SnapPurifier {
    fn default() -> Self {
        Self {
            expected_zero: RowSet::new(0),
        }
    }
}

impl<N: Num> Purifier<N> for SnapPurifier {
    fn purify<E: Epsilon<N>>(
        &mut self,
        rows: &Matrix<N>,
        eps: &E,
        row: Row,
        ray1_zero_set: &RowSet,
        ray2_zero_set: &RowSet,
    ) -> Option<Vec<N>> {
        self.expected_zero.copy_from(ray1_zero_set);
        self.expected_zero.intersection_inplace(ray2_zero_set);
        self.expected_zero.insert(row);
        rows.solve_nullspace_1d(&self.expected_zero, eps)
    }

    fn purify_from_zero_set<E: Epsilon<N>>(
        &mut self,
        rows: &Matrix<N>,
        eps: &E,
        expected_zero: &RowSet,
    ) -> Option<Vec<N>> {
        rows.solve_nullspace_1d(expected_zero, eps)
    }
}

#[derive(Clone, Debug)]
pub struct UpcastingSnapPurifier<M: Num, EM: Epsilon<M>> {
    expected_zero: RowSet,
    eps: EM,
    phantom: std::marker::PhantomData<M>,
}

impl<M: Num, EM: Epsilon<M>> UpcastingSnapPurifier<M, EM> {
    pub fn new(eps: EM) -> Self {
        Self {
            expected_zero: RowSet::new(0),
            eps,
            phantom: std::marker::PhantomData,
        }
    }
}

impl<N, M, EM> Purifier<N> for UpcastingSnapPurifier<M, EM>
where
    N: Num + CoerceFrom<M>,
    M: Num + CoerceFrom<N>,
    EM: Epsilon<M> + Clone,
{
    fn purify<E: Epsilon<N>>(
        &mut self,
        rows: &Matrix<N>,
        _eps: &E,
        row: Row,
        ray1_zero_set: &RowSet,
        ray2_zero_set: &RowSet,
    ) -> Option<Vec<N>> {
        self.expected_zero.copy_from(ray1_zero_set);
        self.expected_zero.intersection_inplace(ray2_zero_set);
        self.expected_zero.insert(row);

        let cols = rows.cols();
        if cols == 0 {
            return None;
        }

        let selected = self.expected_zero.cardinality();
        if selected == 0 {
            return None;
        }

        let mut data = Vec::with_capacity(selected * cols);
        for row_id in self.expected_zero.iter() {
            let src = &rows[row_id.as_index()];
            debug_assert_eq!(
                src.len(),
                cols,
                "matrix row width mismatch (row={}, got={}, expected={})",
                row_id.as_index(),
                src.len(),
                cols
            );
            for v in src.iter() {
                data.push(M::coerce_from(v).ok()?);
            }
        }

        let lifted = Matrix::from_flat(selected, cols, data);
        let lifted_rows = RowSet::all(selected);
        let purified = lifted.solve_nullspace_1d(&lifted_rows, &self.eps)?;
        purified.iter().map(|v| N::coerce_from(v).ok()).collect()
    }

    fn purify_from_zero_set<E: Epsilon<N>>(
        &mut self,
        rows: &Matrix<N>,
        _eps: &E,
        expected_zero: &RowSet,
    ) -> Option<Vec<N>> {
        self.expected_zero.copy_from(expected_zero);
        let cols = rows.cols();
        if cols == 0 {
            return None;
        }

        let selected = self.expected_zero.cardinality();
        if selected == 0 {
            return None;
        }

        let mut data = Vec::with_capacity(selected * cols);
        for row_id in self.expected_zero.iter() {
            let src = &rows[row_id.as_index()];
            debug_assert_eq!(
                src.len(),
                cols,
                "matrix row width mismatch (row={}, got={}, expected={})",
                row_id.as_index(),
                src.len(),
                cols
            );
            for v in src.iter() {
                data.push(M::coerce_from(v).ok()?);
            }
        }

        let lifted = Matrix::from_flat(selected, cols, data);
        let lifted_rows = RowSet::all(selected);
        let purified = lifted.solve_nullspace_1d(&lifted_rows, &self.eps)?;
        purified.iter().map(|v| N::coerce_from(v).ok()).collect()
    }
}

#[derive(Clone, Debug)]
pub struct SinglePrecisionUmpire<
    N: Num,
    E: Epsilon<N> = calculo::num::DynamicEpsilon<N>,
    NM: Normalizer<N> = <N as DefaultNormalizer>::Norm,
    H: HalfspacePolicy<N> = LexMin,
    P: Purifier<N> = NoPurifier,
> {
    eps: E,
    normalizer: NM,
    halfspace: H,
    purifier: P,
    phantom: std::marker::PhantomData<N>,
}

impl<N: Num + DefaultNormalizer, E: Epsilon<N>> SinglePrecisionUmpire<N, E> {
    pub fn new(eps: E) -> Self {
        Self::with_normalizer(eps, <N as DefaultNormalizer>::Norm::default())
    }
}

impl<N: Num, E: Epsilon<N>, NM: Normalizer<N>> SinglePrecisionUmpire<N, E, NM> {
    pub fn with_normalizer(eps: E, normalizer: NM) -> Self {
        Self {
            eps,
            normalizer,
            halfspace: LexMin,
            purifier: NoPurifier,
            phantom: std::marker::PhantomData,
        }
    }
}

impl<N: Num, E: Epsilon<N>, NM: Normalizer<N>, P: Purifier<N>>
    SinglePrecisionUmpire<N, E, NM, LexMin, P>
{
    pub fn with_purifier(eps: E, normalizer: NM, purifier: P) -> Self {
        Self {
            eps,
            normalizer,
            halfspace: LexMin,
            purifier,
            phantom: std::marker::PhantomData,
        }
    }
}

impl<N: Num + DefaultNormalizer, E: Epsilon<N>, H: HalfspacePolicy<N>>
    SinglePrecisionUmpire<N, E, <N as DefaultNormalizer>::Norm, H>
{
    pub fn with_halfspace_policy(eps: E, halfspace: H) -> Self {
        Self {
            eps,
            normalizer: <N as DefaultNormalizer>::Norm::default(),
            halfspace,
            purifier: NoPurifier,
            phantom: std::marker::PhantomData,
        }
    }
}

impl<N: Num, E: Epsilon<N>, NM: Normalizer<N>, H: HalfspacePolicy<N>, P: Purifier<N>>
    SinglePrecisionUmpire<N, E, NM, H, P>
{
    pub fn eps(&self) -> &E {
        &self.eps
    }

    pub fn normalizer(&mut self) -> &mut NM {
        &mut self.normalizer
    }

    pub fn eps_and_normalizer(&mut self) -> (&E, &mut NM) {
        (&self.eps, &mut self.normalizer)
    }

    #[inline(always)]
    fn normalize_vector(&mut self, vector: &mut [N]) -> bool {
        let (eps, normalizer) = self.eps_and_normalizer();
        normalizer.normalize(eps, vector)
    }
}

impl<
    N: Num,
    E: Epsilon<N>,
    NM: Normalizer<N>,
    H: HalfspacePolicy<N>,
    P: Purifier<N>,
    R: Representation,
> Umpire<N, R> for SinglePrecisionUmpire<N, E, NM, H, P>
{
    type Eps = E;
    type Normalizer = NM;
    type MatrixData = LpMatrix<N, R>;
    type RayData = Ray<N>;
    type HalfspacePolicy = H;

    #[inline(always)]
    fn ingest(&mut self, matrix: LpMatrix<N, R>) -> Self::MatrixData {
        matrix
    }

    fn eps(&self) -> &Self::Eps {
        &self.eps
    }

    fn normalizer(&mut self) -> &mut Self::Normalizer {
        &mut self.normalizer
    }

    fn eps_and_normalizer(&mut self) -> (&Self::Eps, &mut Self::Normalizer) {
        (&self.eps, &mut self.normalizer)
    }

    fn halfspace_policy(&mut self) -> &mut Self::HalfspacePolicy {
        &mut self.halfspace
    }

    fn wants_initial_purification(&self) -> bool {
        P::ENABLED
    }

    fn purify_vector_from_zero_set(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        expected_zero: &RowSet,
    ) -> Option<Vec<N>> {
        if !P::ENABLED {
            return None;
        }
        self.purifier
            .purify_from_zero_set(cone.matrix().rows(), &self.eps, expected_zero)
    }

    fn recompute_row_order_vector(
        &mut self,
        cone: &mut ConeCtx<N, R, Self::MatrixData>,
        strict_rows: &RowSet,
    ) {
        self.halfspace
            .recompute_row_order_vector(&self.eps, cone, strict_rows);
    }

    fn choose_next_halfspace(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        excluded: &RowSet,
        iteration: Row,
        active_rays: usize,
    ) -> Option<Row> {
        self.halfspace
            .choose_next_halfspace(cone, excluded, iteration, active_rays)
    }

    fn on_ray_removed(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &Self::RayData,
        _relaxed: bool,
    ) {
        let eps = &self.eps;
        let vector = ray_data.vector();
        self.halfspace.on_ray_removed(|negative_out| {
            let m = cone.matrix().row_count();
            negative_out.resize(m);
            negative_out.clear();
            for &row_idx in cone.order_vector.iter() {
                let row_vec = &cone.matrix().rows()[row_idx];
                let value = linalg::dot(row_vec, vector);
                diag::check_row_eval_sign(eps, row_idx, row_vec, vector, &value, "on_ray_removed");
                let sign = eps.sign(&value);
                if sign == Sign::Negative {
                    negative_out.insert(row_idx);
                }
            }
        });
    }

    fn classify_ray(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &mut Self::RayData,
        row: Row,
    ) -> Sign {
        if ray_data.class.last_eval_row == Some(row) {
            return ray_data.class.last_sign;
        }
        let row_vec = &cone.matrix().rows()[row];
        let value = linalg::dot(row_vec, &ray_data.vector);
        diag::check_row_eval_sign(&self.eps, row, row_vec, &ray_data.vector, &value, "classify_ray");
        let sign = self.eps.sign(&value);
        ray_data.class.last_eval_row = Some(row);
        ray_data.class.last_eval = value;
        ray_data.class.last_sign = sign;
        sign
    }

    fn classify_vector(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        vector: Vec<N>,
        relaxed: bool,
        last_row: Option<Row>,
        negative_out: &mut RowSet,
    ) -> Self::RayData {
        let m = cone.matrix().row_count();
        negative_out.resize(m);
        negative_out.clear();

        let mut zero_set = RowSet::new(m);
        let mut feasible = true;
        let mut weakly_feasible = true;
        let mut first_infeasible_row = None;
        let mut last_eval = None;

        for &row_idx in cone.order_vector.iter() {
            let row_vec = &cone.matrix().rows()[row_idx];
            let value = linalg::dot(row_vec, &vector);
            diag::check_row_eval_sign(
                &self.eps,
                row_idx,
                row_vec,
                &vector,
                &value,
                "classify_vector",
            );
            if Some(row_idx) == last_row {
                last_eval = Some(value.clone());
            }
            let sign = self.eps.sign(&value);
            if sign == Sign::Zero {
                zero_set.insert(row_idx);
            }
            if sign == Sign::Negative {
                negative_out.insert(row_idx);
            }
            let kind = cone.equality_kinds[row_idx];
            let weak_violation = kind.weakly_violates_sign(sign, relaxed);
            if weak_violation {
                if first_infeasible_row.is_none() {
                    first_infeasible_row = Some(row_idx);
                }
                weakly_feasible = false;
            }
            let strict_violation = kind.violates_sign(sign, relaxed);
            if strict_violation {
                feasible = false;
            }
        }

        if relaxed {
            feasible = weakly_feasible;
        }

        let last_eval_row = last_row;
        let last_eval = last_eval.unwrap_or_else(|| {
            last_eval_row
                .map(|row| cone.row_value(row, &vector))
                .unwrap_or_else(N::zero)
        });
        let last_sign = self.eps.sign(&last_eval);

        Ray {
            vector,
            class: RayClass {
                zero_set,
                first_infeasible_row,
                feasible,
                weakly_feasible,
                last_eval_row,
                last_eval,
                last_sign,
            },
        }
    }

    fn sign_sets_for_ray(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &Self::RayData,
        _relaxed: bool,
        force_infeasible: bool,
        negative_out: &mut RowSet,
    ) {
        let m = cone.matrix().row_count();
        negative_out.resize(m);
        negative_out.clear();

        let force_negative_row = ray_data
            .class
            .first_infeasible_row
            .filter(|_| force_infeasible && !ray_data.class.feasible);
        let floor_pos = force_negative_row
            .and_then(|r| cone.row_to_pos.get(r).copied())
            .filter(|pos| *pos < cone.order_vector.len());

        for (pos, &row_idx) in cone.order_vector.iter().enumerate() {
            let forced = floor_pos.map_or(false, |floor| pos >= floor);
            if forced {
                negative_out.insert(row_idx);
                continue;
            }
            let row_vec = &cone.matrix().rows()[row_idx];
            let value = linalg::dot(row_vec, &ray_data.vector);
            diag::check_row_eval_sign(
                &self.eps,
                row_idx,
                row_vec,
                &ray_data.vector,
                &value,
                "sign_sets_for_ray",
            );
            let sign = self.eps.sign(&value);
            if sign == Sign::Negative {
                negative_out.insert(row_idx);
            }
        }
    }

    fn update_first_infeasible_row(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &mut Self::RayData,
        relaxed: bool,
    ) {
        if ray_data.class.weakly_feasible {
            ray_data.class.first_infeasible_row = None;
            return;
        }

        let mut first = None;
        for &row_idx in cone.order_vector.iter() {
            let row_vec = &cone.matrix().rows()[row_idx];
            let value = linalg::dot(row_vec, &ray_data.vector);
            diag::check_row_eval_sign(
                &self.eps,
                row_idx,
                row_vec,
                &ray_data.vector,
                &value,
                "update_first_infeasible_row",
            );
            let sign = self.eps.sign(&value);
            let kind = cone.equality_kinds[row_idx];
            if kind.weakly_violates_sign(sign, relaxed) {
                first = Some(row_idx);
                break;
            }
        }
        ray_data.class.first_infeasible_row = first;
    }

    fn reclassify_ray(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &mut Self::RayData,
        relaxed: bool,
        negative_out: &mut RowSet,
    ) {
        let m = cone.matrix().row_count();
        negative_out.resize(m);
        negative_out.clear();

        let last_eval_row = ray_data.class.last_eval_row;
        let mut last_eval = ray_data.class.last_eval.clone();
        let mut last_sign = ray_data.class.last_sign;

        ray_data.class.zero_set.resize(m);
        ray_data.class.zero_set.clear();
        ray_data.class.first_infeasible_row = None;
        ray_data.class.feasible = true;
        ray_data.class.weakly_feasible = true;

        for &row_idx in cone.order_vector.iter() {
            let row_vec = &cone.matrix().rows()[row_idx];
            let value = linalg::dot(row_vec, &ray_data.vector);
            diag::check_row_eval_sign(
                &self.eps,
                row_idx,
                row_vec,
                &ray_data.vector,
                &value,
                "reclassify_ray",
            );
            let sign = self.eps.sign(&value);
            if Some(row_idx) == last_eval_row {
                last_eval = value.clone();
                last_sign = sign;
            }
            if sign == Sign::Zero {
                ray_data.class.zero_set.insert(row_idx);
            }
            if sign == Sign::Negative {
                negative_out.insert(row_idx);
            }

            let kind = cone.equality_kinds[row_idx];
            if kind.weakly_violates_sign(sign, relaxed) {
                if ray_data.class.first_infeasible_row.is_none() {
                    ray_data.class.first_infeasible_row = Some(row_idx);
                }
                ray_data.class.weakly_feasible = false;
            }
            if kind.violates_sign(sign, relaxed) {
                ray_data.class.feasible = false;
            }
        }

        if relaxed {
            ray_data.class.feasible = ray_data.class.weakly_feasible;
        }

        ray_data.class.last_eval_row = last_eval_row;
        ray_data.class.last_eval = last_eval;
        ray_data.class.last_sign = last_sign;
    }

    fn generate_new_ray(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        parents: (RayId, &Self::RayData, RayId, &Self::RayData),
        row: Row,
        relaxed: bool,
        negative_out: &mut RowSet,
    ) -> Option<Self::RayData> {
        let (_id1, ray1, _id2, ray2) = parents;
        let val1 = if ray1.class.last_eval_row == Some(row) {
            ray1.class.last_eval.clone()
        } else {
            let row_vec = &cone.matrix().rows()[row];
            let value = linalg::dot(row_vec, &ray1.vector);
            diag::check_row_eval_sign(
                &self.eps,
                row,
                row_vec,
                &ray1.vector,
                &value,
                "generate_new_ray.val1",
            );
            value
        };
        let val2 = if ray2.class.last_eval_row == Some(row) {
            ray2.class.last_eval.clone()
        } else {
            let row_vec = &cone.matrix().rows()[row];
            let value = linalg::dot(row_vec, &ray2.vector);
            diag::check_row_eval_sign(
                &self.eps,
                row,
                row_vec,
                &ray2.vector,
                &value,
                "generate_new_ray.val2",
            );
            value
        };

        let a1 = val1.abs();
        let a2 = val2.abs();

        let mut new_vector = vec![N::zero(); ray1.vector.len()];
        linalg::lin_comb2_into(&mut new_vector, &ray1.vector, &a2, &ray2.vector, &a1);
        if !self.normalize_vector(&mut new_vector) {
            return None;
        }

        if let Some(mut purified) = self.purifier.purify(
            cone.matrix().rows(),
            &self.eps,
            row,
            ray1.zero_set(),
            ray2.zero_set(),
        ) {
            if self.normalize_vector(&mut purified) {
                let align = linalg::dot(&purified, &new_vector);
                if self.eps.sign(&align) == Sign::Negative {
                    for v in &mut purified {
                        *v = v.ref_neg();
                    }
                }
                new_vector = purified;
            }
        }

        Some(self.classify_vector(cone, new_vector, relaxed, Some(row), negative_out))
    }
}

#[cfg(test)]
mod tests {
    use super::{SinglePrecisionUmpire, SnapPurifier, UpcastingSnapPurifier};
    use crate::dd::{ConeCtx, Ray, RayClass, RayId, Umpire};
    use crate::matrix::LpMatrix;
    use calculo::num::{DynamicEpsilon, Epsilon, NoNormalizer, Num, Sign};
    use hullabaloo::types::{Inequality, InequalityKind, RowSet};

    #[test]
    fn generate_new_ray_survives_no_normalizer() {
        let eps = DynamicEpsilon::new(0.0);
        let matrix =
            LpMatrix::<f64, Inequality>::from_rows(vec![vec![1.0, 0.0, 0.0], vec![0.0, 1.0, 0.0]]);
        let cone = ConeCtx {
            matrix,
            equality_kinds: vec![InequalityKind::Inequality; 2],
            order_vector: vec![0, 1],
            row_to_pos: vec![0, 1],
            _phantom: std::marker::PhantomData,
        };

        let mut zero = RowSet::new(cone.matrix().row_count());
        zero.insert(0);
        let class = RayClass {
            zero_set: zero.clone(),
            first_infeasible_row: None,
            feasible: true,
            weakly_feasible: true,
            last_eval_row: None,
            last_eval: 0.0,
            last_sign: Sign::Zero,
        };
        let ray1 = Ray {
            vector: vec![1e-3, -1.0, 1.0],
            class: class.clone(),
        };
        let ray2 = Ray {
            vector: vec![1e-3, 2.0, 1.0],
            class,
        };

        let mut umpire = SinglePrecisionUmpire::with_normalizer(eps, NoNormalizer);
        let mut negative = RowSet::new(cone.matrix().row_count());
        let new_ray = umpire.generate_new_ray(
            &cone,
            (RayId(0), &ray1, RayId(1), &ray2),
            1,
            false,
            &mut negative,
        );
        assert!(new_ray.is_some());
    }

    #[test]
    fn snap_purifier_reconstructs_ray_from_zero_sets() {
        let eps = f64::default_eps();
        let matrix =
            LpMatrix::<f64, Inequality>::from_rows(vec![vec![1.0, 0.0, 0.0], vec![0.0, 1.0, 0.0]]);
        let cone = ConeCtx {
            matrix,
            equality_kinds: vec![InequalityKind::Inequality; 2],
            order_vector: vec![0, 1],
            row_to_pos: vec![0, 1],
            _phantom: std::marker::PhantomData,
        };

        let mut zero = RowSet::new(cone.matrix().row_count());
        zero.insert(0);
        let class = RayClass {
            zero_set: zero.clone(),
            first_infeasible_row: None,
            feasible: true,
            weakly_feasible: true,
            last_eval_row: None,
            last_eval: 0.0,
            last_sign: Sign::Zero,
        };
        let ray1 = Ray {
            vector: vec![1e-3, -1.0, 1.0],
            class: class.clone(),
        };
        let ray2 = Ray {
            vector: vec![1e-3, 2.0, 1.0],
            class,
        };

        let mut umpire = SinglePrecisionUmpire::with_purifier(
            eps.clone(),
            NoNormalizer,
            SnapPurifier::default(),
        );
        let mut negative = RowSet::new(cone.matrix().row_count());
        let ray = umpire
            .generate_new_ray(
                &cone,
                (RayId(0), &ray1, RayId(1), &ray2),
                1,
                false,
                &mut negative,
            )
            .expect("ray should be generated");

        assert!(eps.is_zero(&ray.vector[0]));
        assert!(eps.is_zero(&ray.vector[1]));
        assert!(!eps.is_zero(&ray.vector[2]));
        assert!(ray.zero_set().contains(0));
        assert!(ray.zero_set().contains(1));
    }

    #[test]
    #[cfg(feature = "rug")]
    fn upcasting_snap_purifier_reconstructs_ray_from_zero_sets() {
        use calculo::num::RugRat;

        let eps = f64::default_eps();
        let matrix =
            LpMatrix::<f64, Inequality>::from_rows(vec![vec![1.0, 0.0, 0.0], vec![0.0, 1.0, 0.0]]);
        let cone = ConeCtx {
            matrix,
            equality_kinds: vec![InequalityKind::Inequality; 2],
            order_vector: vec![0, 1],
            row_to_pos: vec![0, 1],
            _phantom: std::marker::PhantomData,
        };

        let mut zero = RowSet::new(cone.matrix().row_count());
        zero.insert(0);
        let class = RayClass {
            zero_set: zero.clone(),
            first_infeasible_row: None,
            feasible: true,
            weakly_feasible: true,
            last_eval_row: None,
            last_eval: 0.0,
            last_sign: Sign::Zero,
        };
        let ray1 = Ray {
            vector: vec![1e-3, -1.0, 1.0],
            class: class.clone(),
        };
        let ray2 = Ray {
            vector: vec![1e-3, 2.0, 1.0],
            class,
        };

        let mut umpire = SinglePrecisionUmpire::with_purifier(
            eps.clone(),
            NoNormalizer,
            UpcastingSnapPurifier::new(DynamicEpsilon::new(RugRat::zero())),
        );
        let mut negative = RowSet::new(cone.matrix().row_count());
        let ray = umpire
            .generate_new_ray(
                &cone,
                (RayId(0), &ray1, RayId(1), &ray2),
                1,
                false,
                &mut negative,
            )
            .expect("ray should be generated");

        assert!(eps.is_zero(&ray.vector[0]));
        assert!(eps.is_zero(&ray.vector[1]));
        assert!(!eps.is_zero(&ray.vector[2]));
        assert!(ray.zero_set().contains(0));
        assert!(ray.zero_set().contains(1));
    }
}
