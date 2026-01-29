use crate::Error;
use crate::dd::umpire::policies::HalfspacePolicy as _;
use crate::dd::{Ray, RayId};
use crate::lp::LpSolver;
use crate::matrix::{LpMatrix, MatrixRank};
use calculo::linalg;
use calculo::num::{Epsilon, Normalizer, Num, Sign};
use hullabaloo::types::{Col, ColSet, InequalityKind, Representation, Row, RowSet};
use std::cmp::Ordering;

mod adaptive_precision;
mod multi_precision;
mod kernels {
    use crate::dd::tableau::TableauState;
    use calculo::linalg;
    use calculo::num::{Epsilon, Num};
    use hullabaloo::types::{Col, Row};

    /// Baseline single-precision pivot step (migrated from `ConeEngine::gaussian_column_pivot`).
    #[inline(always)]
    pub(crate) fn gaussian_column_pivot_step<N: Num, E: Epsilon<N>>(
        tableau: &mut TableauState<N>,
        r: Row,
        s: Col,
        eps: &E,
    ) {
        if tableau.is_empty() {
            return;
        }
        let col_count = tableau.tableau_cols;
        let row_count = tableau.tableau_rows;
        debug_assert!(r < row_count, "pivot row out of range");
        debug_assert!(s < col_count, "pivot col out of range");

        let mut pivot_row = std::mem::take(&mut tableau.pivot_row);
        pivot_row.resize(col_count, N::zero());
        pivot_row.clone_from_slice(tableau.row(r));
        let pivot = pivot_row[s].clone();
        tableau.pivot_row = pivot_row;
        if eps.is_zero(&pivot) {
            return;
        }

        tableau.basis.mark_non_identity();
        let pivot_inv = N::one().ref_div(&pivot);
        tableau.factors.resize(col_count, N::zero());
        for (j, factor) in tableau.factors.iter_mut().enumerate() {
            if j == s || eps.is_zero(&tableau.pivot_row[j]) {
                *factor = N::zero();
                continue;
            }
            let scaled = tableau.pivot_row[j].ref_mul(&pivot_inv);
            if eps.is_zero(&scaled) {
                *factor = N::zero();
            } else {
                *factor = scaled;
            }
        }
        let factors = tableau.factors.as_slice();

        // Update basis row-wise to avoid strided access and repeated clones.
        for basis_row in tableau.basis.rows_mut() {
            let pivot_entry = basis_row[s].clone();
            if !eps.is_zero(&pivot_entry) {
                linalg::axpy_sub(basis_row, &pivot_entry, factors);
            }
            basis_row[s] = pivot_entry.ref_mul(&pivot_inv);
        }

        let cols = col_count;
        for row_idx in 0..row_count {
            let start = row_idx * cols;
            let row_slice = &mut tableau.tableau[start..start + cols];
            let pivot_entry = row_slice[s].clone();
            if !eps.is_zero(&pivot_entry) {
                linalg::axpy_sub(row_slice, &pivot_entry, factors);
            }
            row_slice[s] = pivot_entry.ref_mul(&pivot_inv);
        }
    }

    /// Pivot step + tableau book-keeping.
    #[inline(always)]
    pub(crate) fn gaussian_column_pivot<N: Num, E: Epsilon<N>>(
        tableau: &mut TableauState<N>,
        r: Row,
        s: Col,
        eps: &E,
    ) {
        gaussian_column_pivot_step(tableau, r, s, eps);
        let entering = tableau.tableau_nonbasic[s];
        tableau.tableau_basic_col_for_row[r] = s as isize;
        tableau.tableau_nonbasic[s] = r as isize;
        if entering >= 0 {
            let idx = entering as usize;
            debug_assert!(
                idx < tableau.tableau_basic_col_for_row.len(),
                "tableau basis row out of range"
            );
            tableau.tableau_basic_col_for_row[idx] = -1;
        }
    }
}
pub mod policies;
mod single_precision;

pub use adaptive_precision::AdaptivePrecisionUmpire;
pub use multi_precision::MultiPrecisionUmpire;
pub use single_precision::SinglePrecisionUmpire;
pub use single_precision::{NoPurifier, Purifier, SnapPurifier, UpcastingSnapPurifier};

/// Opaque (umpire-owned) representation for the cone's working matrix.
///
/// The DD core may hold onto this type, but must only use it through:
/// - `AsRef<LpMatrix<..>>` for read-only access to the base numeric matrix, and
/// - `select_columns` for column-reduction.
///
/// More refined tiers (e.g. exact shadows) should live *inside* this representation, not as a
/// separately-managed "shadow matrix" inside the umpire.
pub trait UmpireMatrix<N: Num, R: Representation>: Clone + std::fmt::Debug {
    fn base(&self) -> &LpMatrix<N, R>;

    fn select_columns(&self, columns: &[usize]) -> Result<Self, Error>;
}

impl<N: Num, R: Representation> UmpireMatrix<N, R> for LpMatrix<N, R> {
    #[inline(always)]
    fn base(&self) -> &LpMatrix<N, R> {
        self
    }

    #[inline(always)]
    fn select_columns(&self, columns: &[usize]) -> Result<Self, Error> {
        LpMatrix::select_columns(self, columns)
    }
}

pub struct PivotCtx<'a, N: Num, R: Representation, C: UmpireMatrix<N, R> = LpMatrix<N, R>> {
    cone: &'a ConeCtx<N, R, C>,
    tableau: &'a mut crate::dd::tableau::TableauState<N>,
    rowmax: Row,
    nopivot_row: &'a RowSet,
    nopivot_col: &'a ColSet,
    equality_set: &'a RowSet,
}

impl<'a, N: Num, R: Representation, C: UmpireMatrix<N, R>> PivotCtx<'a, N, R, C> {
    pub(crate) fn new(
        cone: &'a ConeCtx<N, R, C>,
        tableau: &'a mut crate::dd::tableau::TableauState<N>,
        rowmax: Row,
        nopivot_row: &'a RowSet,
        nopivot_col: &'a ColSet,
        equality_set: &'a RowSet,
    ) -> Self {
        Self {
            cone,
            tableau,
            rowmax,
            nopivot_row,
            nopivot_col,
            equality_set,
        }
    }

    #[inline(always)]
    pub fn row_count(&self) -> Row {
        self.tableau.tableau_rows
    }

    #[inline(always)]
    pub fn col_count(&self) -> Col {
        self.tableau.tableau_cols
    }

    #[inline(always)]
    pub fn order_vector(&self) -> &[Row] {
        &self.cone.order_vector
    }

    #[inline(always)]
    pub fn tableau_entry(&self, r: Row, c: Col) -> &N {
        debug_assert!(r < self.row_count());
        debug_assert!(c < self.col_count());
        let idx = self.tableau.index(r, c);
        &self.tableau.tableau[idx]
    }

    #[inline(always)]
    pub fn apply_gaussian_column_pivot<E: Epsilon<N>>(&mut self, r: Row, s: Col, eps: &E) {
        kernels::gaussian_column_pivot(self.tableau, r, s, eps);
    }
}

/// Cone fields the umpire is allowed to consult to make numeric decisions.
///
/// Stored on `ConeEngine` so we can pass `&ConeCtx` directly (no per-call view construction).
#[derive(Clone, Debug)]
pub struct ConeCtx<N: Num, R: Representation, M: UmpireMatrix<N, R> = LpMatrix<N, R>> {
    pub(crate) matrix: M,
    pub(crate) equality_kinds: Vec<InequalityKind>,
    pub(crate) order_vector: Vec<Row>,
    pub(crate) row_to_pos: Vec<Row>,
    pub(crate) _phantom: std::marker::PhantomData<(N, R)>,
}

impl<N: Num, R: Representation, M: UmpireMatrix<N, R>> ConeCtx<N, R, M> {
    #[inline(always)]
    pub fn matrix(&self) -> &LpMatrix<N, R> {
        self.matrix.base()
    }

    #[inline(always)]
    pub fn row_value(&self, row: Row, ray: &[N]) -> N {
        linalg::dot(&self.matrix().rows()[row], ray)
    }

    #[inline(always)]
    pub(crate) fn refresh_row_to_pos(&mut self) {
        let m = self.matrix().row_count();
        if self.row_to_pos.len() != m {
            self.row_to_pos = vec![m; m];
        }
        for slot in self.row_to_pos.iter_mut() {
            *slot = m;
        }
        for (pos, &row) in self.order_vector.iter().enumerate() {
            self.row_to_pos[row] = pos;
        }
    }
}

/// Umpire strategy controlling how rays are created and classified.
///
/// - `RayData` is the payload stored in the ray graph.
/// - `RayData` must provide a view of a `Ray<N>` for the DD core's combinatorial logic.
pub trait Umpire<N: Num, R: Representation>: Sized {
    type Eps: Epsilon<N>;
    type Normalizer: Normalizer<N>;
    type MatrixData: UmpireMatrix<N, R>;
    type RayData: AsRef<Ray<N>> + AsMut<Ray<N>> + Clone + std::fmt::Debug;
    type HalfspacePolicy: policies::HalfspacePolicy<N>;

    /// Convert a base matrix into the umpire-owned working representation.
    fn ingest(&mut self, matrix: LpMatrix<N, R>) -> Self::MatrixData;

    fn eps(&self) -> &Self::Eps;
    fn normalizer(&mut self) -> &mut Self::Normalizer;
    fn eps_and_normalizer(&mut self) -> (&Self::Eps, &mut Self::Normalizer);
    fn halfspace_policy(&mut self) -> &mut Self::HalfspacePolicy;

    /// Whether initial rays should be purified from their expected active rows.
    ///
    /// This is intended for snap-style modes that can cheaply reconstruct initial rays from the
    /// initial basis halfspaces (rather than relying on accumulated pivot arithmetic).
    #[inline(always)]
    fn wants_initial_purification(&self) -> bool {
        false
    }

    /// Optionally reconstruct a ray vector from a set of rows expected to evaluate to zero.
    ///
    /// Returning `None` indicates the umpire does not support this purification mode, or that the
    /// selected rows do not yield a 1D nullspace under the current numeric policy.
    #[inline(always)]
    fn purify_vector_from_zero_set(
        &mut self,
        _cone: &ConeCtx<N, R, Self::MatrixData>,
        _expected_zero: &RowSet,
    ) -> Option<Vec<N>> {
        None
    }

    /// Decide whether two rays should be treated as duplicates.
    ///
    /// The DD core guarantees the two rays share the same zero set before calling this method.
    /// The default implementation matches the existing `eps.cmp` component-wise equality check.
    #[inline(always)]
    fn rays_equivalent(&mut self, a: &Self::RayData, b: &Self::RayData) -> bool {
        let eps = self.eps();
        let va = a.as_ref().vector();
        let vb = b.as_ref().vector();
        va.len() == vb.len()
            && va
                .iter()
                .zip(vb.iter())
                .all(|(lhs, rhs)| eps.cmp(lhs, rhs) == Ordering::Equal)
    }

    /// Optional near-zero/ambiguous rows for `ray_data`.
    ///
    /// Umpires that consult a higher-precision shadow only for ambiguous evaluations can return
    /// the rows that required shadow evaluation here.
    #[inline(always)]
    fn near_zero_rows_on_ray<'a>(&self, _ray_data: &'a Self::RayData) -> Option<&'a [Row]> {
        None
    }

    /// Whether `near_zero_rows_on_ray` was truncated due to internal caps.
    #[inline(always)]
    fn near_zero_rows_truncated_on_ray(&self, _ray_data: &Self::RayData) -> bool {
        false
    }

    /// Matrix homogeneity check under the umpire's numeric policy.
    #[inline(always)]
    fn is_homogeneous(&self, matrix: &LpMatrix<N, R>) -> bool {
        matrix.is_homogeneous(self.eps())
    }

    /// Compute/refresh `cone.order_vector` under this umpire's policy.
    fn recompute_row_order_vector(
        &mut self,
        cone: &mut ConeCtx<N, R, Self::MatrixData>,
        strict_rows: &RowSet,
    );

    /// Bump the given rows to the front of `order_vector`, preserving relative order.
    ///
    /// Direct migration of the existing `ConeEngine::update_row_order_vector` behavior.
    #[inline(always)]
    fn bump_priority_rows(
        &mut self,
        cone: &mut ConeCtx<N, R, Self::MatrixData>,
        priority_rows: &RowSet,
    ) {
        let m = cone.matrix().row_count();
        let count = priority_rows.cardinality();
        for target_pos in 0..count {
            if let Some(current_pos) =
                (target_pos..m).find(|pos| priority_rows.contains(cone.order_vector[*pos]))
                && current_pos > target_pos
            {
                let selected = cone.order_vector[current_pos];
                for k in (target_pos + 1..=current_pos).rev() {
                    cone.order_vector[k] = cone.order_vector[k - 1];
                }
                cone.order_vector[target_pos] = selected;
            }
        }
        cone.refresh_row_to_pos();
    }

    /// Choose the next halfspace row to add under this umpire's policy.
    fn choose_next_halfspace(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        excluded: &RowSet,
        iteration: Row,
        active_rays: usize,
    ) -> Option<Row>;

    /// Reset any infeasible-count bookkeeping used by the halfspace policy.
    #[inline(always)]
    fn reset_infeasible_counts(&mut self, row_count: Row) {
        self.halfspace_policy().reset_infeasible_counts(row_count);
    }

    /// Notify the umpire that a ray with the given negative set has been inserted.
    #[inline(always)]
    fn on_ray_inserted(&mut self, negative_set: &RowSet) {
        self.halfspace_policy().on_ray_inserted(negative_set);
    }

    /// Notify the umpire that a ray is about to be removed, so any infeasible-count cache can be updated.
    fn on_ray_removed(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &Self::RayData,
        relaxed: bool,
    );

    /// Choose a pivot (Option A) and apply the pivot step to the tableau.
    ///
    /// This is a direct migration of the existing `ConeEngine::{select_pivot,select_pivot_column}`
    /// + tableau pivot application logic behind the umpire boundary.
    #[inline(always)]
    fn choose_and_apply_pivot(
        &mut self,
        pivot: &mut PivotCtx<'_, N, R, Self::MatrixData>,
    ) -> Option<(Row, Col)> {
        let eps = self.eps();
        let row_count = pivot.tableau.tableau_rows;
        let col_count = pivot.tableau.tableau_cols;
        let mut row_excluded = pivot.nopivot_row.clone();
        for i in (pivot.rowmax + 1)..row_count {
            row_excluded.insert(i);
        }

        loop {
            let mut candidate = None;
            for i in 0..row_count {
                if pivot.equality_set.contains(i) && !row_excluded.contains(i) {
                    candidate = Some(i);
                    break;
                }
            }
            if candidate.is_none() {
                for pos in 0..row_count {
                    let row = pivot.cone.order_vector[pos];
                    if !row_excluded.contains(row) {
                        candidate = Some(row);
                        break;
                    }
                }
            }
            let r = candidate?;

            let mut s_opt = None;
            {
                let start = r * col_count;
                let row_slice = &pivot.tableau.tableau[start..start + col_count];
                for col_id in pivot.nopivot_col.iter().complement() {
                    let s = col_id.as_index();
                    let val = &row_slice[s];
                    if !eps.is_zero(val) {
                        s_opt = Some(s);
                        break;
                    }
                }
            }
            if let Some(s) = s_opt {
                pivot.apply_gaussian_column_pivot(r, s, eps);
                return Some((r, s));
            }
            row_excluded.insert(r);
        }
    }

    /// Compute matrix rank under the umpire's numeric policy.
    #[inline(always)]
    fn rank(
        &mut self,
        matrix: &LpMatrix<N, R>,
        ignored_rows: &RowSet,
        ignored_cols: &ColSet,
    ) -> MatrixRank {
        matrix.rows().rank(ignored_rows, ignored_cols, self.eps())
    }

    /// Feasibility of a restricted face under the umpire's numeric policy.
    #[inline(always)]
    fn restricted_face_exists(
        &mut self,
        matrix: &LpMatrix<N, R>,
        equalities: &RowSet,
        strict_inequalities: &RowSet,
        solver: LpSolver,
    ) -> Result<bool, Error> {
        matrix.restricted_face_exists(equalities, strict_inequalities, solver, self.eps())
    }

    /// Compute the sign of a row evaluation on a ray **without** mutating any ray-local caches.
    ///
    /// This exists specifically for hot-loop scans (e.g. cutoff feasibility counts) where
    /// clobbering `RayClass.last_*` would hurt cache efficiency elsewhere.
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
        let value = cone.row_value(row, ray_ref.vector());
        self.eps().sign(&value)
    }

    /// Classify an existing ray against `row`, updating any cached evaluation in `ray_data`.
    fn classify_ray(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &mut Self::RayData,
        row: Row,
    ) -> Sign;

    /// Fully classify a vector as a new ray, writing any needed sign sets into `sets_out`.
    ///
    /// `last_row` indicates a row whose evaluation should be cached on the ray (if provided).
    fn classify_vector(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        vector: Vec<N>,
        relaxed: bool,
        last_row: Option<Row>,
        negative_out: &mut RowSet,
    ) -> Self::RayData;

    /// Compute sign sets for an existing ray under the umpire's numeric policy, writing into
    /// `sets_out` (typically used for infeasible-count bookkeeping).
    fn sign_sets_for_ray(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &Self::RayData,
        relaxed: bool,
        force_infeasible: bool,
        negative_out: &mut RowSet,
    );

    /// Recompute `first_infeasible_row` under the current row order.
    ///
    /// This must not rely on `RayClass.last_*` cache fields (which are used by Phase2's hot loop).
    fn update_first_infeasible_row(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &mut Self::RayData,
        relaxed: bool,
    );

    /// Recompute ray feasibility + incidence (`zero_set`) under the current row order.
    ///
    /// Implementations should generally preserve the `RayClass.last_*` cache fields.
    fn reclassify_ray(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        ray_data: &mut Self::RayData,
        relaxed: bool,
        negative_out: &mut RowSet,
    );

    /// Construct a new ray from two parent rays at the intersection row.
    ///
    /// Returning `None` indicates the new ray should be discarded.
    fn generate_new_ray(
        &mut self,
        cone: &ConeCtx<N, R, Self::MatrixData>,
        parents: (RayId, &Self::RayData, RayId, &Self::RayData),
        row: Row,
        relaxed: bool,
        negative_out: &mut RowSet,
    ) -> Option<Self::RayData>;
}
