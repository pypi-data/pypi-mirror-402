use crate::dd::DefaultNormalizer;
use crate::dd::{Ray, RayClass, RayId};
use crate::matrix::LpMatrix;
use calculo::linalg;
use calculo::num::{CoerceFrom, Epsilon, Normalizer, Num, Sign};
use hullabaloo::types::{Representation, Row, RowSet};

use super::multi_precision::{CachedRay, ShadowedMatrix};
use super::policies::{HalfspacePolicy, LexMin};
use super::{ConeCtx, Umpire};
use std::cmp::Ordering;

const MAX_NEAR_ZERO_ROWS: usize = 64;

/// Adaptive-precision umpire: use fast `N` signs unless "near zero", then consult a shadow `M`.
///
/// This is intended to close the gap between `SinglePrecisionUmpire` and `MultiPrecisionUmpire`
/// by paying the shadow cost only for ambiguous evaluations.
#[derive(Clone, Debug)]
pub struct AdaptivePrecisionUmpire<
    N: Num,
    M: Num,
    E: Epsilon<N> = calculo::num::DynamicEpsilon<N>,
    ET: Epsilon<N> = calculo::num::DynamicEpsilon<N>,
    EM: Epsilon<M> = calculo::num::DynamicEpsilon<M>,
    NM: Normalizer<N> = <N as DefaultNormalizer>::Norm,
    H: HalfspacePolicy<N> = LexMin,
> {
    eps: E,
    trigger_eps: ET,
    shadow_eps: EM,
    normalizer: NM,
    halfspace: H,
    _phantom: std::marker::PhantomData<(N, M)>,
}

impl<
    N: Num + DefaultNormalizer,
    M: Num + CoerceFrom<N>,
    E: Epsilon<N>,
    ET: Epsilon<N>,
    EM: Epsilon<M>,
> AdaptivePrecisionUmpire<N, M, E, ET, EM>
{
    pub fn new(eps: E, trigger_eps: ET, shadow_eps: EM) -> Self {
        Self::with_halfspace_policy(eps, trigger_eps, shadow_eps, LexMin)
    }
}

impl<
    N: Num,
    M: Num + CoerceFrom<N>,
    E: Epsilon<N>,
    ET: Epsilon<N>,
    EM: Epsilon<M>,
    NM: Normalizer<N>,
> AdaptivePrecisionUmpire<N, M, E, ET, EM, NM>
{
    pub fn with_normalizer(eps: E, trigger_eps: ET, shadow_eps: EM, normalizer: NM) -> Self {
        Self {
            eps,
            trigger_eps,
            shadow_eps,
            normalizer,
            halfspace: LexMin,
            _phantom: std::marker::PhantomData,
        }
    }
}

impl<
    N: Num + DefaultNormalizer,
    M: Num + CoerceFrom<N>,
    E: Epsilon<N>,
    ET: Epsilon<N>,
    EM: Epsilon<M>,
    H: HalfspacePolicy<N>,
> AdaptivePrecisionUmpire<N, M, E, ET, EM, <N as DefaultNormalizer>::Norm, H>
{
    pub fn with_halfspace_policy(eps: E, trigger_eps: ET, shadow_eps: EM, halfspace: H) -> Self {
        Self {
            eps,
            trigger_eps,
            shadow_eps,
            normalizer: <N as DefaultNormalizer>::Norm::default(),
            halfspace,
            _phantom: std::marker::PhantomData,
        }
    }
}

impl<
    N: Num,
    M: Num + CoerceFrom<N>,
    E: Epsilon<N>,
    ET: Epsilon<N>,
    EM: Epsilon<M>,
    NM: Normalizer<N>,
    H: HalfspacePolicy<N>,
> AdaptivePrecisionUmpire<N, M, E, ET, EM, NM, H>
{
    #[inline(always)]
    fn shadow_sign(&self, value: &M) -> Sign {
        self.shadow_eps.sign(value)
    }

    #[inline(always)]
    fn should_consult_shadow(&self, base_value: &N, base_sign: Sign) -> bool {
        base_sign == Sign::Zero || self.trigger_eps.is_zero(base_value)
    }

    #[inline(always)]
    fn adaptive_sign<R: Representation>(
        &self,
        cone: &ConeCtx<N, R, ShadowedMatrix<N, M, R>>,
        shadow_vec: &[M],
        row: Row,
        base_value: &N,
        base_sign: Sign,
    ) -> Sign {
        if !self.should_consult_shadow(base_value, base_sign) {
            return base_sign;
        }
        self.shadow_sign(&cone.matrix.shadow_row_value(row, shadow_vec))
    }

    fn build_ray_from_shadow<R: Representation>(
        &mut self,
        cone: &ConeCtx<N, R, ShadowedMatrix<N, M, R>>,
        standard_vector: Vec<N>,
        shadow: Vec<M>,
        relaxed: bool,
        last_row: Option<Row>,
        negative_out: &mut RowSet,
    ) -> CachedRay<N, M> {
        let m = cone.matrix().row_count();
        negative_out.resize(m);
        negative_out.clear();

        let mut zero_set = RowSet::new(m);
        let mut feasible = true;
        let mut weakly_feasible = true;
        let mut first_infeasible_row = None;

        let mut standard_last_eval: Option<N> = None;
        let mut shadow_last_eval_row: Option<Row> = None;
        let mut shadow_last_eval = M::zero();
        let mut shadow_last_sign = Sign::Zero;
        let mut last_sign = Sign::Zero;

        let mut near_zero_rows: Vec<Row> = Vec::new();
        let mut near_zero_truncated = false;

        for &row_idx in &cone.order_vector {
            let base_value = cone.row_value(row_idx, &standard_vector);
            if Some(row_idx) == last_row {
                standard_last_eval = Some(base_value.clone());
            }

            let base_sign = self.eps.sign(&base_value);
            let consulted_shadow = self.should_consult_shadow(&base_value, base_sign);
            let sign = if consulted_shadow {
                let shadow_value = cone.matrix.shadow_row_value(row_idx, &shadow);
                let sign = self.shadow_sign(&shadow_value);
                if Some(row_idx) == last_row {
                    shadow_last_eval_row = Some(row_idx);
                    shadow_last_eval = shadow_value.clone();
                    shadow_last_sign = sign;
                }
                sign
            } else {
                base_sign
            };
            if consulted_shadow {
                if near_zero_rows.len() < MAX_NEAR_ZERO_ROWS {
                    near_zero_rows.push(row_idx);
                } else {
                    near_zero_truncated = true;
                }
            }
            if Some(row_idx) == last_row {
                last_sign = sign;
            }

            if sign == Sign::Zero {
                zero_set.insert(row_idx);
            }
            if sign == Sign::Negative {
                negative_out.insert(row_idx);
            }

            let kind = cone.equality_kinds[row_idx];
            if kind.weakly_violates_sign(sign, relaxed) {
                if first_infeasible_row.is_none() {
                    first_infeasible_row = Some(row_idx);
                }
                weakly_feasible = false;
            }
            if kind.violates_sign(sign, relaxed) {
                feasible = false;
            }
        }

        if relaxed {
            feasible = weakly_feasible;
        }

        let standard_last_eval = match last_row {
            Some(row_idx) => {
                standard_last_eval.unwrap_or_else(|| cone.row_value(row_idx, &standard_vector))
            }
            None => N::zero(),
        };

        let standard = Ray {
            vector: standard_vector,
            class: RayClass {
                zero_set,
                first_infeasible_row,
                feasible,
                weakly_feasible,
                last_eval_row: last_row,
                last_eval: standard_last_eval,
                last_sign,
            },
        };

        CachedRay {
            standard,
            shadow,
            shadow_last_eval_row,
            shadow_last_eval,
            shadow_last_sign,
            near_zero_rows,
            near_zero_truncated,
        }
    }
}

impl<
    N: Num,
    M: Num + CoerceFrom<N>,
    E: Epsilon<N>,
    ET: Epsilon<N>,
    EM: Epsilon<M>,
    NM: Normalizer<N>,
    H: HalfspacePolicy<N>,
    R: Representation,
> Umpire<N, R> for AdaptivePrecisionUmpire<N, M, E, ET, EM, NM, H>
{
    type Eps = E;
    type Normalizer = NM;
    type MatrixData = ShadowedMatrix<N, M, R>;
    type RayData = CachedRay<N, M>;
    type HalfspacePolicy = H;

    fn ingest(&mut self, matrix: LpMatrix<N, R>) -> Self::MatrixData {
        let cols = matrix.col_count();
        let rows = matrix.row_count();
        let mut shadow = Vec::with_capacity(rows * cols);
        for row in matrix.rows() {
            for v in row {
                shadow.push(M::coerce_from(v).expect("matrix entries must be convertible"));
            }
        }
        ShadowedMatrix {
            base: matrix,
            shadow,
        }
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

    #[inline(always)]
    fn near_zero_rows_on_ray<'a>(&self, ray_data: &'a Self::RayData) -> Option<&'a [Row]> {
        Some(ray_data.near_zero_rows())
    }

    #[inline(always)]
    fn near_zero_rows_truncated_on_ray(&self, ray_data: &Self::RayData) -> bool {
        ray_data.near_zero_truncated()
    }

    fn rays_equivalent(&mut self, a: &Self::RayData, b: &Self::RayData) -> bool {
        let eps = &self.eps;
        let va = a.as_ref().vector();
        let vb = b.as_ref().vector();
        if va.len() != vb.len()
            || va
                .iter()
                .zip(vb.iter())
                .any(|(lhs, rhs)| eps.cmp(lhs, rhs) != Ordering::Equal)
        {
            return false;
        }

        a.shadow().len() == b.shadow().len()
            && a.shadow()
                .iter()
                .zip(b.shadow().iter())
                .all(|(lhs, rhs)| self.shadow_eps.cmp(lhs, rhs) == Ordering::Equal)
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
        let trigger = &self.trigger_eps;
        let shadow_eps = &self.shadow_eps;
        let standard_vec = ray_data.as_ref().vector();
        let shadow_vec = ray_data.shadow();

        self.halfspace.on_ray_removed(|negative_out| {
            let m = cone.matrix().row_count();
            negative_out.resize(m);
            negative_out.clear();
            for &row_idx in &cone.order_vector {
                let base_value = cone.row_value(row_idx, standard_vec);
                let base_sign = eps.sign(&base_value);
                let sign = if base_sign != Sign::Zero && !trigger.is_zero(&base_value) {
                    base_sign
                } else {
                    shadow_eps.sign(&cone.matrix.shadow_row_value(row_idx, shadow_vec))
                };
                if sign == Sign::Negative {
                    negative_out.insert(row_idx);
                }
            }
        });
    }

    #[inline(always)]
    fn sign_for_row_on_ray(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray: &Self::RayData,
        row: Row,
    ) -> Sign {
        let ray_ref = ray.as_ref();
        if ray_ref.class.last_eval_row == Some(row) {
            return ray_ref.class.last_sign;
        }
        if let Some(sign) = ray.cached_shadow_sign(row) {
            return sign;
        }

        let base_value = cone.row_value(row, ray_ref.vector());
        let base_sign = self.eps.sign(&base_value);
        self.adaptive_sign(cone, ray.shadow(), row, &base_value, base_sign)
    }

    fn classify_ray(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &mut Self::RayData,
        row: Row,
    ) -> Sign {
        ray_data.ensure_shadow_matches_standard();

        if ray_data.standard.class.last_eval_row == Some(row) {
            return ray_data.standard.class.last_sign;
        }

        let base_value = cone.row_value(row, ray_data.standard.vector());
        let base_sign = self.eps.sign(&base_value);
        let consulted_shadow = self.should_consult_shadow(&base_value, base_sign);
        let sign = if consulted_shadow {
            let shadow_value = cone
                .matrix
                .shadow_row_value(row, ray_data.shadow.as_slice());
            let sign = self.shadow_sign(&shadow_value);
            ray_data.shadow_last_eval_row = Some(row);
            ray_data.shadow_last_eval = shadow_value;
            ray_data.shadow_last_sign = sign;
            sign
        } else {
            base_sign
        };
        if consulted_shadow {
            if ray_data.near_zero_rows.len() < MAX_NEAR_ZERO_ROWS {
                if !ray_data.near_zero_rows.contains(&row) {
                    ray_data.near_zero_rows.push(row);
                }
            } else {
                ray_data.near_zero_truncated = true;
            }
        }

        ray_data.standard.class.last_eval_row = Some(row);
        ray_data.standard.class.last_eval = base_value;
        ray_data.standard.class.last_sign = sign;
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
        let shadow = vector
            .iter()
            .map(|v| M::coerce_from(v).expect("ray vectors must be convertible"))
            .collect::<Vec<_>>();
        self.build_ray_from_shadow(cone, vector, shadow, relaxed, last_row, negative_out)
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
            .as_ref()
            .class
            .first_infeasible_row
            .filter(|_| force_infeasible && !ray_data.as_ref().class.feasible);
        let floor_pos = force_negative_row
            .and_then(|r| cone.row_to_pos.get(r).copied())
            .filter(|pos| *pos < cone.order_vector.len());

        let standard_vec = ray_data.as_ref().vector();
        let shadow_vec = ray_data.shadow();

        for (pos, &row_idx) in cone.order_vector.iter().enumerate() {
            let forced = floor_pos.map_or(false, |floor| pos >= floor);
            if forced {
                negative_out.insert(row_idx);
                continue;
            }

            let base_value = cone.row_value(row_idx, standard_vec);
            let base_sign = self.eps.sign(&base_value);
            let sign = self.adaptive_sign(cone, shadow_vec, row_idx, &base_value, base_sign);
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
        ray_data.ensure_shadow_matches_standard();

        if ray_data.standard.class.weakly_feasible {
            ray_data.standard.class.first_infeasible_row = None;
            return;
        }

        let mut first = None;
        let standard_vec = ray_data.standard.vector();
        let shadow_vec = ray_data.shadow.as_slice();
        for &row_idx in &cone.order_vector {
            let base_value = cone.row_value(row_idx, standard_vec);
            let base_sign = self.eps.sign(&base_value);
            let sign = self.adaptive_sign(cone, shadow_vec, row_idx, &base_value, base_sign);
            let kind = cone.equality_kinds[row_idx];
            if kind.weakly_violates_sign(sign, relaxed) {
                first = Some(row_idx);
                break;
            }
        }
        ray_data.standard.class.first_infeasible_row = first;
    }

    fn reclassify_ray(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &mut Self::RayData,
        relaxed: bool,
        negative_out: &mut RowSet,
    ) {
        ray_data.ensure_shadow_matches_standard();
        ray_data.near_zero_rows.clear();
        ray_data.near_zero_truncated = false;

        let m = cone.matrix().row_count();
        negative_out.resize(m);
        negative_out.clear();

        let last_eval_row = ray_data.standard.class.last_eval_row;
        let mut last_eval = ray_data.standard.class.last_eval.clone();
        let mut last_sign = ray_data.standard.class.last_sign;

        let shadow_vec = ray_data.shadow.as_slice();

        ray_data.standard.class.zero_set.resize(m);
        ray_data.standard.class.zero_set.clear();
        ray_data.standard.class.first_infeasible_row = None;
        ray_data.standard.class.feasible = true;
        ray_data.standard.class.weakly_feasible = true;

        for &row_idx in &cone.order_vector {
            let base_value = cone.row_value(row_idx, ray_data.standard.vector());
            let base_sign = self.eps.sign(&base_value);
            let consulted_shadow = self.should_consult_shadow(&base_value, base_sign);
            let sign = if consulted_shadow {
                let shadow_value = cone.matrix.shadow_row_value(row_idx, shadow_vec);
                let sign = self.shadow_sign(&shadow_value);
                if Some(row_idx) == last_eval_row {
                    ray_data.shadow_last_eval_row = Some(row_idx);
                    ray_data.shadow_last_eval = shadow_value;
                    ray_data.shadow_last_sign = sign;
                }
                sign
            } else {
                base_sign
            };
            if consulted_shadow {
                if ray_data.near_zero_rows.len() < MAX_NEAR_ZERO_ROWS {
                    ray_data.near_zero_rows.push(row_idx);
                } else {
                    ray_data.near_zero_truncated = true;
                }
            }

            if Some(row_idx) == last_eval_row {
                last_eval = base_value.clone();
                last_sign = sign;
            }

            if sign == Sign::Zero {
                ray_data.standard.class.zero_set.insert(row_idx);
            }
            if sign == Sign::Negative {
                negative_out.insert(row_idx);
            }

            let kind = cone.equality_kinds[row_idx];
            if kind.weakly_violates_sign(sign, relaxed) {
                if ray_data.standard.class.first_infeasible_row.is_none() {
                    ray_data.standard.class.first_infeasible_row = Some(row_idx);
                }
                ray_data.standard.class.weakly_feasible = false;
            }
            if kind.violates_sign(sign, relaxed) {
                ray_data.standard.class.feasible = false;
            }
        }

        if relaxed {
            ray_data.standard.class.feasible = ray_data.standard.class.weakly_feasible;
        }

        ray_data.standard.class.last_eval_row = last_eval_row;
        ray_data.standard.class.last_eval = last_eval;
        ray_data.standard.class.last_sign = last_sign;
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

        let val1 = if ray1.as_ref().class.last_eval_row == Some(row) {
            ray1.as_ref().class.last_eval.clone()
        } else {
            cone.row_value(row, ray1.as_ref().vector())
        };
        let val2 = if ray2.as_ref().class.last_eval_row == Some(row) {
            ray2.as_ref().class.last_eval.clone()
        } else {
            cone.row_value(row, ray2.as_ref().vector())
        };

        let a1 = val1.abs();
        let a2 = val2.abs();

        let mut new_vector = vec![N::zero(); ray1.as_ref().vector().len()];
        linalg::lin_comb2_into(
            &mut new_vector,
            ray1.as_ref().vector(),
            &a2,
            ray2.as_ref().vector(),
            &a1,
        );
        let a1_shadow = M::coerce_from(&a1).expect("ray weights must be convertible");
        let a2_shadow = M::coerce_from(&a2).expect("ray weights must be convertible");
        let mut new_shadow = vec![M::zero(); ray1.shadow().len()];
        linalg::lin_comb2_into(
            &mut new_shadow,
            ray1.shadow(),
            &a2_shadow,
            ray2.shadow(),
            &a1_shadow,
        );
        if !self
            .normalizer
            .normalize_pair(&self.eps, &mut new_vector, &mut new_shadow)
        {
            return None;
        }

        Some(self.build_ray_from_shadow(
            cone,
            new_vector,
            new_shadow,
            relaxed,
            Some(row),
            negative_out,
        ))
    }
}
