//! DD (Double Description) core engine.
//!
//! This module contains the DD enumeration engine and its numeric policy layer ("umpire").

use calculo::num::{GcdNormalizer, MaxNormalizer, Normalizer, Num};

pub trait DefaultNormalizer: Num {
    type Norm: Normalizer<Self> + Default;
}

impl DefaultNormalizer for f64 {
    type Norm = MaxNormalizer;
}

#[cfg(feature = "rug")]
impl DefaultNormalizer for calculo::num::RugRat {
    type Norm = GcdNormalizer<calculo::num::RugRat>;
}

#[cfg(feature = "rug")]
impl<const P: u32> DefaultNormalizer for calculo::num::RugFloat<P> {
    type Norm = MaxNormalizer;
}

#[cfg(feature = "dashu")]
impl DefaultNormalizer for calculo::num::DashuRat {
    type Norm = GcdNormalizer<calculo::num::DashuRat>;
}

#[cfg(feature = "dashu")]
impl<const P: usize> DefaultNormalizer for calculo::num::DashuFloat<P> {
    type Norm = MaxNormalizer;
}

mod basis;
mod builder;
mod diag;
mod engine;
mod index;
mod ray;
mod state;
pub mod umpire;

pub mod mode {
    use crate::Error;
    use calculo::num::Num;
    use hullabaloo::types::{Representation, Row};

    use super::state::ConeEngine;
    use super::umpire::Umpire;

    /// The halfspace-add mode selected by an umpire's `HalfspacePolicy`.
    pub type UmpireHalfspaceMode<N, R, U> = <<U as Umpire<N, R>>::HalfspacePolicy as
        crate::dd::umpire::policies::HalfspacePolicy<N>>::Mode;

    /// How the DD core applies a chosen halfspace.
    ///
    /// This replaces ad-hoc core booleans like `preordered_run` with a monomorphized strategy.
    pub trait HalfspaceMode: Clone + std::fmt::Debug + Default {
        /// Whether the DD loop should perform an initial row-order recomputation.
        ///
        /// This is a compile-time property of the mode (no runtime branching in the core).
        #[inline(always)]
        fn initial_recompute_row_order() -> bool {
            false
        }

        /// Called after the cone's row order vector changes.
        #[inline(always)]
        fn on_row_order_recomputed<N: Num, R: Representation, U: Umpire<N, R>>(
            _state: &mut ConeEngine<N, R, U>,
        ) {
        }

        /// Called after ray initialization finishes.
        #[inline(always)]
        fn on_rays_initialized<N: Num, R: Representation, U: Umpire<N, R>>(
            _state: &mut ConeEngine<N, R, U>,
        ) {
        }

        /// Called after a halfspace is successfully added.
        #[inline(always)]
        fn on_halfspace_added<N: Num, R: Representation, U: Umpire<N, R>>(
            _state: &mut ConeEngine<N, R, U>,
            _row: Row,
        ) {
        }

        /// Apply `row` as the next halfspace.
        fn add_halfspace<N: Num, R: Representation, U: Umpire<N, R>>(
            state: &mut ConeEngine<N, R, U>,
            row: Row,
        ) -> Result<(), Error>;
    }

    #[derive(Clone, Copy, Debug, Default)]
    pub struct Preordered;

    impl HalfspaceMode for Preordered {
        #[inline(always)]
        fn on_row_order_recomputed<N: Num, R: Representation, U: Umpire<N, R>>(
            state: &mut ConeEngine<N, R, U>,
        ) {
            state.update_ray_orders();
        }

        #[inline(always)]
        fn on_rays_initialized<N: Num, R: Representation, U: Umpire<N, R>>(
            state: &mut ConeEngine<N, R, U>,
        ) {
            state.create_initial_edges();
        }

        #[inline(always)]
        fn add_halfspace<N: Num, R: Representation, U: Umpire<N, R>>(
            state: &mut ConeEngine<N, R, U>,
            row: Row,
        ) -> Result<(), Error> {
            state.add_new_halfspace_preordered(row)
        }
    }

    #[derive(Clone, Copy, Debug, Default)]
    pub struct Dynamic;

    impl HalfspaceMode for Dynamic {
        #[inline(always)]
        fn initial_recompute_row_order() -> bool {
            true
        }

        #[inline(always)]
        fn on_halfspace_added<N: Num, R: Representation, U: Umpire<N, R>>(
            state: &mut ConeEngine<N, R, U>,
            _row: Row,
        ) {
            state.core.recompute_row_order = true;
        }

        #[inline(always)]
        fn add_halfspace<N: Num, R: Representation, U: Umpire<N, R>>(
            state: &mut ConeEngine<N, R, U>,
            row: Row,
        ) -> Result<(), Error> {
            state.swap_row_into_iteration_slot(row);
            state.add_new_halfspace_dynamic(row)
        }
    }
}

pub(crate) mod tableau {
    #[cfg(test)]
    use std::cmp::Ordering;

    use calculo::num::Num;
    use hullabaloo::matrix::BasisMatrix;
    use hullabaloo::types::{Col, Representation, Row};

    #[cfg(test)]
    use calculo::num::Epsilon;

    use super::state::ConeEngine;
    use super::umpire::Umpire;

    #[derive(Clone, Debug)]
    pub(crate) struct TableauState<N: Num> {
        pub(crate) basis: BasisMatrix<N>,
        pub(crate) basis_saved: BasisMatrix<N>,
        pub(crate) tableau: Vec<N>,
        pub(crate) tableau_rows: Row,
        pub(crate) tableau_cols: Col,
        pub(crate) tableau_nonbasic: Vec<isize>,
        pub(crate) tableau_basic_col_for_row: Vec<isize>,
        pub(crate) row_status: Vec<i8>,
        pub(crate) pivot_row: Vec<N>,
        pub(crate) factors: Vec<N>,
    }

    impl<N: Num> TableauState<N> {
        pub(crate) fn reset_storage(&mut self, rows: Row, cols: Col) {
            self.tableau_rows = rows;
            self.tableau_cols = cols;
            assert!(
                cols == 0 || rows <= usize::MAX / cols,
                "tableau size overflow (rows={}, cols={})",
                rows,
                cols
            );
            self.tableau.resize(rows * cols, N::zero());
        }

        #[inline(always)]
        pub(crate) fn index(&self, row: Row, col: Col) -> usize {
            row * self.tableau_cols + col
        }

        #[inline(always)]
        pub(crate) fn row(&self, row: Row) -> &[N] {
            let start = row * self.tableau_cols;
            let end = start + self.tableau_cols;
            &self.tableau[start..end]
        }

        #[inline(always)]
        pub(crate) fn is_empty(&self) -> bool {
            self.tableau.is_empty()
        }
    }

    impl<N: Num, R: Representation, U: Umpire<N, R>> ConeEngine<N, R, U> {
        #[inline]
        pub(crate) fn init_nonbasic(cols: usize) -> Vec<isize> {
            (0..cols).map(|c| -((c as isize) + 1)).collect()
        }

        pub(crate) fn tableau_entering_for_row(&mut self, row: Row) {
            if row >= self.row_count() {
                return;
            }
            if self.core.tableau.tableau_basic_col_for_row.len() != self.row_count() {
                self.core.tableau.tableau_basic_col_for_row = vec![-1; self.row_count()];
            }
            if self.core.tableau.tableau_nonbasic.is_empty() {
                self.core.tableau.tableau_nonbasic = Self::init_nonbasic(self.col_count());
            }
            if self.core.tableau.tableau_basic_col_for_row[row] == -1
                && let Some((col_idx, nb)) = self
                    .core
                    .tableau
                    .tableau_nonbasic
                    .iter_mut()
                    .enumerate()
                    .find(|(_, v)| **v < 0)
            {
                *nb = row as isize;
                self.core.tableau.tableau_basic_col_for_row[row] = col_idx as isize;
            }
        }

        pub(crate) fn rebuild_tableau(&mut self) {
            let rows = self.row_count();
            let cols = self.col_count();
            let matrix_rows = self.core.ctx.matrix().rows();
            debug_assert_eq!(self.core.tableau.basis.dim(), cols);
            self.core.tableau.reset_storage(rows, cols);
            if self.core.tableau.basis.is_identity() {
                let tableau = &mut self.core.tableau.tableau;
                for (row_idx, src) in matrix_rows.iter().enumerate() {
                    let start = row_idx * cols;
                    let end = start + cols;
                    tableau[start..end].clone_from_slice(src);
                }
                return;
            }
            let basis = &self.core.tableau.basis;
            let tableau = &mut self.core.tableau.tableau;
            for (row_idx, src) in matrix_rows.iter().enumerate() {
                let row_start = row_idx * cols;
                for col_idx in 0..cols {
                    let mut acc = N::zero();
                    for (j, src_j) in src.iter().enumerate() {
                        let factor = basis.get(j, col_idx);
                        calculo::linalg::add_mul_assign(&mut acc, src_j, factor);
                    }
                    tableau[row_start + col_idx] = acc;
                }
            }
        }

        #[cfg(test)]
        pub(crate) fn lex_compare_columns(
            &self,
            left: usize,
            right: usize,
            eps: &impl Epsilon<N>,
        ) -> Ordering {
            debug_assert_eq!(self.core.ctx.order_vector.len(), self.row_count());
            let zero = N::zero();
            let tableau = &self.core.tableau.tableau;
            let cols = self.core.tableau.tableau_cols;
            debug_assert!(left < cols && right < cols);
            for &row in &self.core.ctx.order_vector {
                debug_assert!(row < self.core.tableau.tableau_rows);
                let row_start = row * cols;
                let idx_l = row_start + left;
                let idx_r = row_start + right;
                let diff = tableau[idx_l].ref_sub(&tableau[idx_r]);
                if eps.is_zero(&diff) {
                    if let Some(ord) = diff.partial_cmp(&zero)
                        && ord != Ordering::Equal
                    {
                        return ord;
                    }
                    continue;
                }
                if eps.is_positive(&diff) {
                    return Ordering::Greater;
                }
                if eps.is_negative(&diff) {
                    return Ordering::Less;
                }
            }
            Ordering::Equal
        }
    }
}

pub use builder::{
    BasisInitialization, Cone, ConeBuilder, ConeOptions, ConeOptionsBuilder, EnumerationMode,
};
pub(crate) use ray::RayClass;
pub use ray::{AdjacencyEdge, Ray, RayId, RayPartition, RayPartitionOwned};
pub(crate) use ray::{RayKey, RayOrigin};
pub use state::{ColumnReduction, ConeBasisPrep, ConeDd, ConeEngine, ConeOutput};
pub use umpire::{
    AdaptivePrecisionUmpire, ConeCtx, MultiPrecisionUmpire, NoPurifier, PivotCtx, Purifier,
    SinglePrecisionUmpire, SnapPurifier, Umpire, UmpireMatrix, UpcastingSnapPurifier,
};

#[cfg(test)]
mod tests;
