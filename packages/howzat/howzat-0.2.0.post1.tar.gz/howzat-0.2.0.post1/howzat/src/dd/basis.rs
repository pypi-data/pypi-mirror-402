use crate::Error;
use crate::dd::state::{ConeBasisPrep, ConeDd, ConeEngine, ConeOutput};
use crate::dd::{PivotCtx, Umpire, UmpireMatrix};
use crate::lp::LpSolver;
use calculo::num::Num;
use hullabaloo::matrix::BasisMatrix;
use hullabaloo::types::{ColSet, ComputationStatus, Representation, RepresentationKind, RowSet};

type FindInitialBasisResult<N, R, U> = Result<Result<ConeDd<N, R, U>, ConeOutput<N, R, U>>, Error>;

impl<N: Num, R: Representation, U: Umpire<N, R>> ConeBasisPrep<N, R, U> {
    pub(crate) fn new(state: ConeEngine<N, R, U>) -> Self {
        Self { state }
    }

    pub fn into_state(self) -> ConeEngine<N, R, U> {
        self.state
    }

    pub fn run_dd(self) -> Result<ConeOutput<N, R, U>, Error> {
        match self.find_initial_basis()? {
            Ok(phase2) => phase2.run_to_completion(),
            Err(output) => Ok(output),
        }
    }

    pub fn find_initial_basis(mut self) -> FindInitialBasisResult<N, R, U> {
        if self.state.core.comp_status != ComputationStatus::InProgress {
            return Ok(Err(ConeOutput { state: self.state }));
        }
        if self.state.col_count() == 0 {
            self.state.core.comp_status = ComputationStatus::AllFound;
            return Ok(Err(ConeOutput { state: self.state }));
        }
        if self.state.check_emptiness()? {
            self.state.core.comp_status = ComputationStatus::RegionEmpty;
            return Ok(Err(ConeOutput { state: self.state }));
        }
        if !self.state.core.iter_state.col_reduced {
            self.state.core.tableau.basis_saved = self.state.core.tableau.basis.clone();
        }
        let found = self.state.find_initial_rays();
        if !found {
            self.state.core.comp_status = ComputationStatus::RegionEmpty;
            return Ok(Err(ConeOutput { state: self.state }));
        }
        self.state.initialize_rays();
        if self.state.core.comp_status != ComputationStatus::InProgress {
            return Ok(Err(ConeOutput { state: self.state }));
        }
        Ok(Ok(ConeDd { state: self.state }))
    }
}

impl<N: Num, R: Representation, U: Umpire<N, R>> ConeEngine<N, R, U> {
    pub(crate) fn check_emptiness(&mut self) -> Result<bool, Error> {
        match R::KIND {
            RepresentationKind::Inequality => {
                let (core, umpire) = self.split_core_umpire();
                let exists = umpire.restricted_face_exists(
                    core.ctx.matrix(),
                    &core.equality_set,
                    &core._strict_inequality_set,
                    LpSolver::DualSimplex,
                )?;
                Ok(!exists)
            }
            RepresentationKind::Generator => Ok(false),
        }
    }

    pub(crate) fn find_initial_rays(&mut self) -> bool {
        let mut rank = 0usize;
        self.find_basis(&mut rank);
        let rank_info = {
            let matrix = self.core.ctx.matrix();
            let ignored_rows = RowSet::new(matrix.row_count());
            let ignored_cols = ColSet::new(matrix.col_count());
            self.umpire.rank(matrix, &ignored_rows, &ignored_cols)
        };
        let detected_rank = rank_info.rank.max(rank);
        assert!(
            self.core.iter_state.d_orig >= detected_rank,
            "detected rank exceeds original dimension"
        );
        self.core.iter_state.linearity_dim = self.core.iter_state.d_orig - detected_rank;
        if self.core.iter_state.linearity_dim > 0 {
            // Column reduction updates both core state and the umpire-owned matrix representation.
            self.column_reduce();
            self.find_basis(&mut rank);
            self.core.recompute_row_order = true;
        }
        true
    }

    pub(crate) fn find_basis(&mut self, rank: &mut usize) {
        *rank = 0;
        let col_count = self.col_count();
        let row_count = self.row_count();
        self.core
            .iter_state
            .initial_ray_index
            .resize(col_count, None);
        self.core
            .iter_state
            .initial_ray_index
            .iter_mut()
            .for_each(|v| *v = None);
        self.core.initial_halfspaces.clear();
        let mut col_selected = ColSet::new(col_count);
        let mut nopivot_row = self.core._strict_inequality_set.clone();
        self.core.tableau.basis = BasisMatrix::identity(col_count);
        self.core.tableau.tableau_nonbasic = Self::init_nonbasic(col_count);
        self.core.tableau.tableau_basic_col_for_row = vec![-1; row_count];
        self.rebuild_tableau();
        let rowmax = row_count;

        loop {
            let pivot = {
                let (core, umpire) = self.split_core_umpire();
                let mut ctx = PivotCtx::new(
                    &core.ctx,
                    &mut core.tableau,
                    rowmax,
                    &nopivot_row,
                    &col_selected,
                    &core.equality_set,
                );
                umpire.choose_and_apply_pivot(&mut ctx)
            };
            let Some((r, s)) = pivot else {
                break;
            };
            nopivot_row.insert(r);
            col_selected.insert(s);
            self.core.initial_halfspaces.insert(r);
            if s >= self.core.iter_state.initial_ray_index.len() {
                self.core
                    .iter_state
                    .initial_ray_index
                    .resize(s + 1, Some(0));
            }
            self.core.iter_state.initial_ray_index[s] = Some(r);
            *rank += 1;
            if *rank == col_count {
                break;
            }
        }
    }

    fn column_reduce(&mut self) {
        let mut kept = Vec::new();
        let mut mapping = vec![None; self.core.iter_state.d_orig];
        let mut new_idx = 0;
        let keep_col0 = R::KIND == RepresentationKind::Inequality;
        for (j, &row_idx) in self.core.iter_state.initial_ray_index.iter().enumerate() {
            if row_idx.is_some() || (keep_col0 && j == 0) {
                kept.push(j);
                mapping[j] = Some(new_idx);
                new_idx += 1;
            } else {
                mapping[j] = None;
            }
        }
        if kept.len() == self.col_count() {
            self.core.iter_state.newcol = mapping;
            return;
        }
        let new_d = kept.len();
        let old_basis = self.core.tableau.basis.clone();
        let old_initial = self.core.iter_state.initial_ray_index.clone();
        self.core.ctx.matrix = self
            .core
            .ctx
            .matrix
            .select_columns(&kept)
            .expect("column reduction maintains matrix shape");

        let reduced_basis_rows: Vec<Vec<N>> = kept
            .iter()
            .map(|&r| {
                let mut row_vec = Vec::with_capacity(new_d);
                for &c in &kept {
                    row_vec.push(old_basis.get(r, c).clone());
                }
                row_vec
            })
            .collect();
        let reduced_basis = BasisMatrix::from_rows(reduced_basis_rows);

        self.core.tableau.basis_saved = old_basis;
        self.core.tableau.basis = reduced_basis;

        let mut reduced_initial = vec![None; new_d];
        for (old_idx, mapped) in mapping.iter().enumerate() {
            if let Some(new_pos) = mapped {
                reduced_initial[*new_pos] = old_initial.get(old_idx).cloned().flatten();
            }
        }
        self.core.iter_state.initial_ray_index = reduced_initial;
        self.core.iter_state.newcol = mapping;
        self.rebuild_tableau();
        self.core.tableau.tableau_nonbasic = Self::init_nonbasic(new_d);
        self.update_rays_after_column_reduction();
        self.core.tableau.tableau_basic_col_for_row = vec![-1; self.row_count()];
        self.sync_tableau_flags();
        self.core.iter_state.col_reduced = true;
    }

    fn update_rays_after_column_reduction(&mut self) {
        let new_d = self.col_count();
        let mapping = self.core.iter_state.newcol.clone();

        self.with_active_ray_ids(|state, rays| {
            for id in rays.iter().copied() {
                if let Some(ray) = state.ray_mut(id) {
                    let mut new_vec = vec![N::zero(); new_d];
                    for (old_idx, &new_idx) in mapping.iter().enumerate() {
                        if let Some(idx) = new_idx {
                            debug_assert!(
                                idx < new_vec.len(),
                                "column reduction mapping out of range"
                            );
                            debug_assert!(
                                old_idx < ray.vector.len(),
                                "ray vector shorter than expected"
                            );
                            new_vec[idx] = ray.vector[old_idx].clone();
                        }
                    }
                    ray.vector = new_vec;
                }
            }
        });
        self.reclassify_rays();
    }

    fn reclassify_rays(&mut self) {
        let relaxed = self.core.options.relaxed_enumeration();
        self.with_active_ray_ids(|state, rays| {
            let m = state.row_count();
            for id in rays.iter().copied() {
                let mut sets = state.core.ray_workspace.take_sets(m);
                {
                    let Some(ray_data) = state.core.ray_graph.ray_data_mut(id) else {
                        state.recycle_sets(sets);
                        continue;
                    };
                    state.umpire.reclassify_ray(
                        &state.core.ctx,
                        ray_data,
                        relaxed,
                        &mut sets.negative_set,
                    );
                }
                state.recycle_sets(sets);
            }
        });
        self.rebuild_ray_index();
        self.core.ray_graph.recompute_counts();
    }
}
