use crate::Error;
use crate::dd::Umpire;
use crate::dd::diag;
use crate::dd::mode::{HalfspaceMode, UmpireHalfspaceMode};
use crate::dd::ray::{
    AdjacencyEdge, EdgeTarget, Ray, RayId, RayListHeads, RayPartition, RayPartitionOwned,
};
use crate::dd::state::{ConeDd, ConeEngine, ConeOutput};
use calculo::num::{Epsilon, Normalizer, Num, Sign};
use hullabaloo::types::{ComputationStatus, Representation, Row, RowSet, trailing_mask};
#[inline]
fn rowset_cardinality_at_least(set: &RowSet, target: usize) -> bool {
    if target == 0 {
        return true;
    }
    let words = set.bit_slice();
    let mask = trailing_mask(set.len());
    let Some((&last, prefix)) = words.split_last() else {
        return false;
    };
    let mut count = 0usize;
    for &word in prefix {
        count += word.count_ones() as usize;
        if count >= target {
            return true;
        }
    }
    count += (last & mask).count_ones() as usize;
    count >= target
}

#[derive(Clone, Copy)]
enum DegeneracyCandidates<'a> {
    Slice(&'a [RayId]),
    BitSet(&'a RowSet),
}

impl<N: Num, R: Representation, U: Umpire<N, R>> ConeDd<N, R, U> {
    pub fn run_to_completion(mut self) -> Result<ConeOutput<N, R, U>, Error> {
        loop {
            if self.state.core.recompute_row_order {
                let (ctx, umpire, strict) = (
                    &mut self.state.core.ctx,
                    &mut self.state.umpire,
                    &self.state.core._strict_inequality_set,
                );
                umpire.recompute_row_order_vector(ctx, strict);
                let priority = self.state.core.weakly_added_halfspaces.clone();
                self.state
                    .umpire
                    .bump_priority_rows(&mut self.state.core.ctx, &priority);
                <UmpireHalfspaceMode<N, R, U> as HalfspaceMode>::on_row_order_recomputed(
                    &mut self.state,
                );
                #[cfg(debug_assertions)]
                {
                    self.state.debug_assert_iteration_prefix();
                }
                self.state.core.recompute_row_order = false;
                self.state.core.edges_dirty = true;
            }
            if self.state.core.comp_status == ComputationStatus::RegionEmpty
                || self.state.core.comp_status == ComputationStatus::AllFound
            {
                break;
            }
            let active = self.state.core.ray_graph.active_len();
            let Some(hh) = self.state.umpire.choose_next_halfspace(
                &self.state.core.ctx,
                &self.state.core.weakly_added_halfspaces,
                self.state.core.iter_state.iteration,
                active,
            ) else {
                self.state.core.comp_status = ComputationStatus::AllFound;
                break;
            };
            <UmpireHalfspaceMode<N, R, U> as HalfspaceMode>::add_halfspace(&mut self.state, hh)?;
        }
        self.state.reclassify_active_rays();
        Ok(ConeOutput { state: self.state })
    }
}

impl<N: Num, R: Representation, U: Umpire<N, R>> ConeEngine<N, R, U> {
    pub(crate) fn update_ray_orders(&mut self) {
        let relaxed = self.core.options.relaxed_enumeration();
        let mut ids = std::mem::take(&mut self.core.active_id_scratch);
        self.core.ray_graph.copy_active_ids(&mut ids);

        let mut changed = false;
        for id in ids.iter().copied() {
            let Some(ray_data) = self.core.ray_graph.ray_data_mut(id) else {
                continue;
            };
            let old = ray_data.as_ref().first_infeasible_row();
            self.umpire
                .update_first_infeasible_row(&self.core.ctx, ray_data, relaxed);
            changed |= old != ray_data.as_ref().first_infeasible_row();
        }
        self.core.active_id_scratch = ids;
        if changed {
            self.core.edges_dirty = true;
        }
    }

    pub fn ray_count(&self) -> usize {
        self.core.ray_graph.active_len()
    }

    fn position_of_row(&self, row: Row) -> Option<Row> {
        self.core
            .ctx
            .row_to_pos
            .get(row)
            .copied()
            .filter(|pos| *pos < self.row_count())
    }

    pub(crate) fn first_infeasible_position(&self, ray: &Ray<N>) -> Option<Row> {
        ray.first_infeasible_row()
            .and_then(|row| self.position_of_row(row))
    }

    fn first_infeasible_position_or_m(&self, ray: &Ray<N>) -> Row {
        self.first_infeasible_position(ray)
            .unwrap_or_else(|| self.row_count() + 1)
    }

    fn sync_iteration_with_added(&mut self) {
        let iter = self
            .core
            .weakly_added_halfspaces
            .cardinality()
            .min(self.row_count());
        self.core.iter_state.iteration = iter;
    }

    #[cfg(debug_assertions)]
    fn debug_assert_iteration_prefix(&self) {
        let iter = self.core.iter_state.iteration.min(self.row_count());
        debug_assert_eq!(
            iter,
            self.core.weakly_added_halfspaces.cardinality(),
            "iteration {} diverges from weakly-added count {}",
            iter,
            self.core.weakly_added_halfspaces.cardinality()
        );
        for pos in 0..iter {
            let row = self.core.ctx.order_vector[pos];
            debug_assert!(
                self.core.weakly_added_halfspaces.contains(row),
                "row {} at position {} not marked weakly added",
                row,
                pos
            );
        }
        for row in 0..self.row_count() {
            if self.core.weakly_added_halfspaces.contains(row) {
                let in_prefix = self
                    .position_of_row(row)
                    .map(|pos| pos < iter)
                    .unwrap_or(false);
                debug_assert!(
                    in_prefix,
                    "weakly-added row {} not placed in iteration prefix",
                    row
                );
            }
        }
    }

    pub(crate) fn add_new_halfspace_preordered(&mut self, row: Row) -> Result<(), Error> {
        let iter_pos = self
            .order_position(row)
            .unwrap_or_else(|| panic!("row {row} not present in order vector"));
        self.core.iter_state.iteration = iter_pos;
        self.tableau_entering_for_row(row);

        let partition = self.evaluate_row_partition(row);
        let partition_view = Self::partition_view(&partition);
        if partition_view.positive.is_empty() && partition_view.zero.is_empty() {
            self.core.ray_graph.deactivate_all();
            self.umpire.reset_infeasible_counts(self.row_count());
            self.clear_ray_indices();
            self.core.pending_new_rays.clear();
            self.core.comp_status = ComputationStatus::RegionEmpty;
            self.recycle_partition(partition);
            return Ok(());
        }
        let valid_first = Some(partition_view.positive);
        self.process_iteration_edges(iter_pos, self.core.ctx.order_vector[iter_pos], valid_first);
        self.delete_negative_rays(partition_view);
        self.prune_recent_rays();
        self.core.added_halfspaces.insert(row);
        self.core.weakly_added_halfspaces.insert(row);
        self.sync_iteration_with_added();
        self.sync_tableau_flag_for_row(row);

        if self.core.iter_state.iteration < self.row_count() && self.core.ray_graph.zero_len() > 1 {
            let zero_rays = std::mem::take(&mut self.core.active_id_scratch);
            if zero_rays.len() > 1 {
                self.update_edges(&zero_rays);
            }
            self.core.active_id_scratch = zero_rays;
        }
        <UmpireHalfspaceMode<N, R, U> as HalfspaceMode>::on_halfspace_added(self, row);
        if self.core.ray_graph.active_len() == self.core.ray_graph.weakly_feasible_len() {
            self.core.comp_status = ComputationStatus::AllFound;
        }
        self.recycle_partition(partition);
        Ok(())
    }

    pub(crate) fn add_new_halfspace_dynamic(&mut self, row: Row) -> Result<(), Error> {
        self.tableau_entering_for_row(row);
        let partition = self.evaluate_row_partition(row);
        let partition_view = Self::partition_view(&partition);
        if partition_view.negative.is_empty() {
            self.core.weakly_added_halfspaces.insert(row);
            self.sync_iteration_with_added();
            self.sync_tableau_flag_for_row(row);
            if self.core.ray_graph.active_len() == self.core.ray_graph.weakly_feasible_len() {
                self.core.comp_status = ComputationStatus::AllFound;
            }
            self.recycle_partition(partition);
            return Ok(());
        }
        if partition_view.positive.is_empty() && partition_view.zero.is_empty() {
            self.core.ray_graph.deactivate_all();
            self.umpire.reset_infeasible_counts(self.row_count());
            self.clear_ray_indices();
            self.core.pending_new_rays.clear();
            self.core.comp_status = ComputationStatus::RegionEmpty;
            self.recycle_partition(partition);
            return Ok(());
        }
        self.with_active_ray_ids(|state, adjacency_candidates| {
            for &pos in partition_view.positive {
                for &neg in partition_view.negative {
                    if !state.check_adjacency(neg, pos, adjacency_candidates) {
                        continue;
                    }
                    let _ = state.create_new_ray(neg, pos, row);
                }
            }
        });
        self.delete_negative_rays(partition_view);
        self.prune_recent_rays();
        self.core.added_halfspaces.insert(row);
        self.core.weakly_added_halfspaces.insert(row);
        self.sync_iteration_with_added();
        self.sync_tableau_flag_for_row(row);
        <UmpireHalfspaceMode<N, R, U> as HalfspaceMode>::on_halfspace_added(self, row);
        if self.core.ray_graph.active_len() == self.core.ray_graph.weakly_feasible_len() {
            self.core.comp_status = ComputationStatus::AllFound;
        }
        self.recycle_partition(partition);
        Ok(())
    }

    pub fn initialize_rays(&mut self) {
        self.core.ray_graph.reset(self.row_count());
        self.umpire.reset_infeasible_counts(self.row_count());
        self.core.tableau.tableau_nonbasic = Self::init_nonbasic(self.col_count());
        self.core.tableau.tableau_basic_col_for_row = vec![-1; self.row_count()];
        self.add_artificial_ray();
        self.clear_ray_indices();

        self.core.initial_halfspaces.clear();
        for &row in &self.core.iter_state.initial_ray_index {
            if let Some(r) = row {
                self.core.initial_halfspaces.insert(r);
            }
        }

        self.core.added_halfspaces = self.core.initial_halfspaces.clone();
        self.core.weakly_added_halfspaces = self.core.initial_halfspaces.clone();
        self.sync_tableau_flags();
        let initial = self.core.initial_halfspaces.clone();
        self.umpire.bump_priority_rows(&mut self.core.ctx, &initial);
        self.core.edges_dirty = true;
        let last_row = self.core.ctx.order_vector.first().copied();
        let m = self.row_count();
        let wants_purify = self.umpire.wants_initial_purification();
        let mut expected_zero = RowSet::new(0);
        if wants_purify {
            expected_zero.resize(m);
        }
        if diag::enabled()
            && std::any::type_name::<N>() == "f64"
            && std::env::var_os("HOWZAT_DD_EXACT_SIGN_VERBOSE").is_some()
        {
            eprintln!(
                "howzat dd init: rows={} cols={} initial_ray_index={:?}",
                self.row_count(),
                self.col_count(),
                self.core.iter_state.initial_ray_index
            );
        }
        for col in 0..self.col_count() {
            let mut vec = self.core.tableau.basis.column(col);
            let pivot_row = self
                .core
                .iter_state
                .initial_ray_index
                .get(col)
                .copied()
                .flatten();
            let pre_norm_max_abs = if diag::enabled() && std::any::type_name::<N>() == "f64" {
                let mut max = 0.0f64;
                for v in vec.iter() {
                    let abs = v.abs().to_f64();
                    if abs.is_finite() && abs > max {
                        max = abs;
                    }
                }
                Some(max)
            } else {
                None
            };
            if !{
                let (eps, normalizer) = self.umpire.eps_and_normalizer();
                normalizer.normalize(eps, &mut vec)
            } {
                continue;
            }
            if wants_purify {
                expected_zero.copy_from(&self.core.initial_halfspaces);
                expected_zero.union_inplace(&self.core.equality_set);
                if let Some(row) = pivot_row
                    && !self.core.equality_set.contains(row)
                {
                    expected_zero.remove(row);
                }

                let init_ray_diag = cfg!(any(test, debug_assertions))
                    && std::any::type_name::<N>() == "f64"
                    && std::env::var_os("HOWZAT_DD_INIT_RAY_DIAG").is_some();
                if init_ray_diag {
                    let eps = self.umpire.eps().eps().to_f64();
                    let rows = self.core.ctx.matrix().rows();
                    let mut worst_row = None;
                    let mut worst_value = 0.0f64;
                    for row_id in expected_zero.iter() {
                        let row = row_id.as_index();
                        let value = calculo::linalg::dot(&rows[row], &vec).to_f64();
                        let abs = value.abs();
                        if abs > worst_value {
                            worst_row = Some(row);
                            worst_value = abs;
                        }
                    }
                    if let Some(row) = worst_row {
                        let raw = calculo::linalg::dot(&rows[row], &vec).to_f64();
                        let sign = if raw > eps {
                            "pos"
                        } else if raw < -eps {
                            "neg"
                        } else {
                            "zero"
                        };
                        eprintln!(
                            "howzat dd init-ray residual: col={col} pivot_row={pivot_row:?} \
worst_row={row} dot={raw:.17e} |dot|={worst_value:.17e} eps={eps:.1e} sign={sign}",
                        );
                    }
                }

                if let Some(mut purified) =
                    self.umpire
                        .purify_vector_from_zero_set(&self.core.ctx, &expected_zero)
                    && {
                        let (eps, normalizer) = self.umpire.eps_and_normalizer();
                        normalizer.normalize(eps, &mut purified)
                    }
                {
                    let align = calculo::linalg::dot(&purified, &vec);
                    if self.umpire.eps().sign(&align) == Sign::Negative {
                        for v in &mut purified {
                            *v = v.ref_neg();
                        }
                    }
                    vec = purified;
                }
            }
            let has_initial = self
                .core
                .iter_state
                .initial_ray_index
                .get(col)
                .copied()
                .flatten()
                .is_some();
            let add_negative = !has_initial;
            let neg_vec = add_negative.then(|| vec.iter().cloned().map(|v| -v).collect::<Vec<N>>());
            let mut sets = self.core.ray_workspace.take_sets(m);
            let ray_data = {
                let _guard = diag::push_context(diag::DiagContext::InitializeRay {
                    col,
                    negated: false,
                    pivot_row,
                    pre_norm_max_abs,
                });
                // cddlib seeds use strict feasibility checks; do not apply relaxed handling here.
                self.umpire.classify_vector(
                    &self.core.ctx,
                    vec,
                    false,
                    last_row,
                    &mut sets.negative_set,
                )
            };
            if self
                .core
                .equality_set
                .subset_of(ray_data.as_ref().zero_set())
            {
                self.umpire.on_ray_inserted(&sets.negative_set);
                let id = self.core.ray_graph.insert_active(ray_data);
                self.register_ray_id(id);
                self.recycle_sets(sets);
                if let Some(neg_vec) = neg_vec {
                    let mut neg_sets = self.core.ray_workspace.take_sets(m);
                    let neg_ray_data = {
                        let _guard = diag::push_context(diag::DiagContext::InitializeRay {
                            col,
                            negated: true,
                            pivot_row,
                            pre_norm_max_abs,
                        });
                        self.umpire.classify_vector(
                            &self.core.ctx,
                            neg_vec,
                            false,
                            last_row,
                            &mut neg_sets.negative_set,
                        )
                    };
                    self.umpire.on_ray_inserted(&neg_sets.negative_set);
                    let id = self.core.ray_graph.insert_active(neg_ray_data);
                    self.register_ray_id(id);
                    self.recycle_sets(neg_sets);
                }
            } else {
                self.recycle_sets(sets);
            }
        }
        self.core.iter_state.iteration = self.col_count();
        self.with_active_ray_ids(|state, active_ids| {
            let mut floored = false;
            if state.core.iter_state.iteration < state.core.ctx.order_vector.len() {
                let floor_row = state.core.ctx.order_vector[state.core.iter_state.iteration];
                let floor_pos = state.core.iter_state.iteration;
                for &idx in active_ids {
                    if let Some(ray_pos) = state
                        .ray(idx)
                        .map(|ray| state.first_infeasible_position_or_m(ray))
                        && ray_pos < floor_pos
                        && let Some(ray_mut) = state.ray_mut(idx)
                    {
                        ray_mut.class.first_infeasible_row = Some(floor_row);
                        floored = true;
                    }
                }
            }
            if state.enforce_first_infeasible_floor(active_ids) {
                floored = true;
            }
            if floored {
                state.core.edges_dirty = true;
            }
        });
        <UmpireHalfspaceMode<N, R, U> as HalfspaceMode>::on_rays_initialized(self);
        self.core.iter_state.iteration = self.col_count().saturating_add(1);
        if self.core.iter_state.iteration > self.row_count() {
            self.core.iter_state.iteration = self.row_count();
        }
        if self.core.iter_state.iteration > self.row_count() {
            self.core.comp_status = ComputationStatus::AllFound;
        }

        // Start iteration counter aligned to rows that are actually marked added.
        // At initialization nothing has been added yet, so keep the iteration prefix empty.
        self.sync_iteration_with_added();
    }

    fn partition_view<'a>(partition: &'a RayPartitionOwned) -> RayPartition<'a> {
        RayPartition {
            negative: &partition.negative,
            positive: &partition.positive,
            zero: &partition.zero,
        }
    }

    pub(crate) fn recycle_partition(&mut self, mut partition: RayPartitionOwned) {
        partition.negative.clear();
        partition.positive.clear();
        partition.zero.clear();
        self.core.partitions = partition;
    }

    pub(crate) fn check_adjacency(&mut self, r1: RayId, r2: RayId, candidates: &[RayId]) -> bool {
        let use_added = !self.core.added_halfspaces.is_empty();
        let (ray1_zero, ray2_zero) = {
            let ray_graph = &self.core.ray_graph;
            let (Some(ray1), Some(ray2)) = (ray_graph.ray(r1), ray_graph.ray(r2)) else {
                return false;
            };
            (ray1.zero_set(), ray2.zero_set())
        };

        self.core.adj_face.copy_from(ray1_zero);
        self.core.adj_face.intersection_inplace(ray2_zero);
        if use_added {
            self.core
                .adj_face
                .intersection_inplace(&self.core.added_halfspaces);
        } else {
            self.core
                .adj_face
                .intersection_inplace(&self.core.ground_set);
        }

        let required = self.adjacency_dimension().saturating_sub(2);
        if !rowset_cardinality_at_least(&self.core.adj_face, required) {
            return false;
        }

        if self.core.options.assumes_nondegeneracy() {
            return true;
        }

        !self
            .core
            .ray_incidence
            .candidate_contains_face(&self.core.adj_face, candidates, r1, r2)
    }

    fn reclassify_active_rays(&mut self) {
        let mut ids = std::mem::take(&mut self.core.active_id_scratch);
        self.core.ray_graph.copy_active_ids(&mut ids);
        let relaxed = self.core.options.relaxed_enumeration();
        let m = self.row_count();
        for id in ids.iter().copied() {
            let mut sets = self.core.ray_workspace.take_sets(m);
            {
                let Some(ray_data) = self.core.ray_graph.ray_data_mut(id) else {
                    self.recycle_sets(sets);
                    continue;
                };
                self.umpire.reclassify_ray(
                    &self.core.ctx,
                    ray_data,
                    relaxed,
                    &mut sets.negative_set,
                );
            }
            self.recycle_sets(sets);
        }
        self.core.active_id_scratch = ids;
        self.rebuild_ray_index();
        self.core.ray_graph.recompute_counts();
    }

    fn prune_recent_rays(&mut self) {
        self.core.pending_new_rays.clear();
    }

    fn conditional_add_edge(&mut self, r1: RayId, r2: RayId, candidates: DegeneracyCandidates<'_>) {
        let f1 = match self.ray(r1) {
            Some(ray) => self.first_infeasible_position_or_m(ray),
            None => return,
        };
        let f2 = match self.ray(r2) {
            Some(ray) => self.first_infeasible_position_or_m(ray),
            None => return,
        };
        let (fmin, rmin, rmax) = if f1 <= f2 { (f1, r1, r2) } else { (f2, r2, r1) };
        if fmin >= self.core.ctx.order_vector.len() {
            return;
        }
        if self.ray(rmax).is_none() {
            return;
        }
        let mut queue_edge = false;
        let max_zero = {
            let ray_graph = &self.core.ray_graph;
            let Some(ray) = ray_graph.ray(rmax) else {
                return;
            };
            ray.zero_set()
        };
        self.core.adj_face.copy_from(max_zero);

        let fmin_row = self
            .core
            .ctx
            .order_vector
            .get(fmin)
            .copied()
            .unwrap_or(self.row_count());
        let strong_sep = !self.core.adj_face.contains(fmin_row);
        if !strong_sep {
            return;
        }

        let min_zero = {
            let ray_graph = &self.core.ray_graph;
            let Some(ray) = ray_graph.ray(rmin) else {
                return;
            };
            ray.zero_set()
        };
        self.core.adj_face.intersection_inplace(min_zero);

        self.core.count_intersections += 1;
        let mut last_chance = true;
        for iteration in (self.core.iter_state.iteration + 1)..fmin {
            let row_idx = self.core.ctx.order_vector[iteration];
            let contains_row = self.core.adj_face.contains(row_idx);
            if contains_row && !self.core._strict_inequality_set.contains(row_idx) {
                last_chance = false;
                self.core.count_intersections_bad += 1;
                break;
            }
        }
        if last_chance {
            self.core.count_intersections_good += 1;
            let use_added = !self.core.added_halfspaces.is_empty();
            if use_added {
                self.core
                    .adj_face
                    .intersection_inplace(&self.core.added_halfspaces);
            } else {
                self.core
                    .adj_face
                    .intersection_inplace(&self.core.ground_set);
            }
            let required = self.adjacency_dimension().saturating_sub(2);
            let mut adjacent = rowset_cardinality_at_least(&self.core.adj_face, required);
            if adjacent && !self.core.options.assumes_nondegeneracy() {
                let contains = match candidates {
                    DegeneracyCandidates::Slice(indices) => self
                        .core
                        .ray_incidence
                        .candidate_contains_face(&self.core.adj_face, indices, r1, r2),
                    DegeneracyCandidates::BitSet(set) => self
                        .core
                        .ray_incidence
                        .candidate_set_contains_face(&self.core.adj_face, set, r1, r2),
                };
                if contains {
                    adjacent = false;
                }
            }
            queue_edge = adjacent;
        }
        if queue_edge {
            let edge = AdjacencyEdge {
                retained: rmax,
                removed: rmin,
            };
            self.core.ray_graph.queue_edge(fmin, edge);
        }
    }

    pub(crate) fn create_initial_edges(&mut self) {
        self.core.iter_state.iteration = self.col_count();
        self.with_active_ray_ids(|state, rays| {
            if rays.len() < 2 {
                return;
            }
            for i in 0..rays.len() - 1 {
                let r1 = rays[i];
                let f1 = state
                    .ray(r1)
                    .map(|r| state.first_infeasible_position_or_m(r))
                    .unwrap_or(state.row_count());
                for &r2 in rays.iter().skip(i + 1) {
                    let f2 = state
                        .ray(r2)
                        .map(|r| state.first_infeasible_position_or_m(r))
                        .unwrap_or(state.row_count());
                    if f1 == f2 {
                        continue;
                    }
                    state.conditional_add_edge(r1, r2, DegeneracyCandidates::Slice(rays));
                }
            }
        });
    }

    pub fn update_edges(&mut self, zero_rays: &[RayId]) {
        if zero_rays.len() < 2 {
            return;
        }
        for i in 0..zero_rays.len() - 1 {
            let r1 = zero_rays[i];
            let fi = self
                .ray(r1)
                .map(|r| self.first_infeasible_position_or_m(r))
                .unwrap_or(self.row_count());
            for &r2 in zero_rays.iter().skip(i + 1) {
                let f2 = self
                    .ray(r2)
                    .map(|r| self.first_infeasible_position_or_m(r))
                    .unwrap_or(self.row_count());
                if f2 <= fi {
                    continue;
                }
                self.conditional_add_edge(r1, r2, DegeneracyCandidates::Slice(zero_rays));
            }
        }
    }

    fn process_iteration_edges(&mut self, iteration: Row, row: Row, valid_first: Option<&[RayId]>) {
        if iteration >= self.core.ray_graph.edge_buckets_len() {
            return;
        }
        if self.core.edges_dirty {
            self.refresh_edge_buckets();
            self.core.edges_dirty = false;
        }

        let valid_first = valid_first.unwrap_or(&[]);
        let edges = self.core.ray_graph.take_edges(iteration);

        if self.core.options.assumes_nondegeneracy() {
            for edge in edges {
                let f1 = match self.ray(edge.retained) {
                    Some(ray) => self.first_infeasible_position_or_m(ray),
                    None => continue,
                };

                let Some(new_idx) = self.create_new_ray(edge.removed, edge.retained, row) else {
                    continue;
                };

                let f2 = match self.ray(new_idx) {
                    Some(ray) => self.first_infeasible_position_or_m(ray),
                    None => continue,
                };

                if f1 != f2 {
                    self.conditional_add_edge(
                        edge.retained,
                        new_idx,
                        DegeneracyCandidates::Slice(valid_first),
                    );
                }
            }
            return;
        }

        let mut candidate_set = std::mem::replace(&mut self.core.candidate_ray_set, RowSet::new(0));
        candidate_set.resize(self.core.ray_incidence.ray_capacity());
        candidate_set.clear();
        for &rid in valid_first {
            candidate_set.insert(rid.as_index());
        }

        for edge in edges {
            let f1 = match self.ray(edge.retained) {
                Some(ray) => self.first_infeasible_position_or_m(ray),
                None => continue,
            };

            let Some(new_idx) = self.create_new_ray(edge.removed, edge.retained, row) else {
                continue;
            };

            let f2 = match self.ray(new_idx) {
                Some(ray) => self.first_infeasible_position_or_m(ray),
                None => continue,
            };

            if f1 != f2 {
                let need = self.core.ray_incidence.ray_capacity();
                if candidate_set.len() != need {
                    candidate_set.resize(need);
                }
                self.conditional_add_edge(
                    edge.retained,
                    new_idx,
                    DegeneracyCandidates::BitSet(&candidate_set),
                );
            }
        }
        self.core.candidate_ray_set = candidate_set;
    }

    pub(crate) fn delete_negative_rays(&mut self, partition: RayPartition<'_>) {
        let relaxed = self.core.options.relaxed_enumeration();
        for &idx in partition.negative.iter() {
            let ray_data = self.core.ray_graph.ray_data(idx);
            if let Some(ray_data) = ray_data {
                self.umpire
                    .on_ray_removed(&self.core.ctx, ray_data, relaxed);
            }
            self.unregister_ray_id(idx);
        }
        self.core
            .ray_graph
            .remove_many_keep_order(partition.negative);
        self.discard_pending_rays(partition.negative);

        let mut zeros = std::mem::take(&mut self.core.active_id_scratch);
        zeros.clear();
        zeros.reserve(partition.zero.len() + self.core.pending_new_rays.len());
        zeros.extend_from_slice(partition.zero);

        let mut order = self.core.ray_graph.take_active_order();
        order.clear();
        order.reserve(partition.positive.len() + zeros.len() + self.core.pending_new_rays.len());
        order.extend_from_slice(partition.positive);

        let mut max_id = 0usize;
        for &rid in partition.positive.iter().chain(zeros.iter()) {
            max_id = max_id.max(rid.as_index());
        }
        for &rid in &self.core.pending_new_rays {
            max_id = max_id.max(rid.as_index());
        }
        if max_id >= self.core.removed_marks.len() {
            self.core.removed_marks.resize(max_id + 1, 0);
        }
        self.core.removed_epoch = self.core.removed_epoch.wrapping_add(1);
        if self.core.removed_epoch == 0 {
            self.core.removed_epoch = 1;
            self.core.removed_marks.fill(0);
        }
        let epoch = self.core.removed_epoch;
        for &rid in partition.positive.iter().chain(zeros.iter()) {
            self.core.removed_marks[rid.as_index()] = epoch;
        }

        for &id in &self.core.pending_new_rays {
            if self.core.removed_marks[id.as_index()] == epoch {
                continue;
            }
            let Some(ray) = self.ray(id) else { continue };
            if ray.class.last_sign == Sign::Positive {
                order.push(id);
            } else {
                zeros.push(id);
            }
            self.core.removed_marks[id.as_index()] = epoch;
        }

        zeros.sort_unstable_by(|a, b| {
            let fa = self
                .ray(*a)
                .map(|r| self.first_infeasible_position_or_m(r))
                .unwrap_or(self.row_count());
            let fb = self
                .ray(*b)
                .map(|r| self.first_infeasible_position_or_m(r))
                .unwrap_or(self.row_count());
            fa.cmp(&fb).then_with(|| a.as_index().cmp(&b.as_index()))
        });

        let pos_head = order.first().copied();
        let pos_tail = order.last().copied();
        let zero_head = zeros.first().copied();
        let zero_tail = zeros.last().copied();
        let zero_count = zeros.len();
        order.extend_from_slice(&zeros);

        self.core
            .ray_graph
            .set_order_with_zero_count_unchecked(order, zero_count);

        self.core.lists = RayListHeads::default();
        self.core.lists.pos_head = pos_head;
        self.core.lists.pos_tail = pos_tail;
        self.core.lists.zero_head = zero_head;
        self.core.lists.zero_tail = zero_tail;
        self.core.active_id_scratch = zeros;
        if self.core.ray_graph.active_len() == 0 {
            self.core.comp_status = ComputationStatus::RegionEmpty;
            self.umpire.reset_infeasible_counts(self.row_count());
        }
    }

    pub(crate) fn refresh_edge_buckets(&mut self) {
        let row_cap = self.row_count();
        assert!(
            row_cap < usize::MAX,
            "row count overflow while refreshing edge buckets"
        );
        let target_len = self.core.ray_graph.edge_buckets_len().max(row_cap + 1);
        if target_len > 0 {
            self.core.ray_graph.ensure_edge_capacity(target_len - 1);
        }
        self.core.ray_graph.edge_count = 0;
        let buckets_to_process = std::mem::take(&mut self.core.ray_graph.non_empty_edge_buckets);
        for &bucket_idx in &buckets_to_process {
            debug_assert!(
                bucket_idx < self.core.ray_graph.edge_bucket_positions.len(),
                "edge bucket index out of range while clearing bucket positions"
            );
            self.core.ray_graph.edge_bucket_positions[bucket_idx] = None;
        }
        for bucket_idx in buckets_to_process {
            debug_assert!(
                bucket_idx < self.core.ray_graph.edges.len(),
                "edge bucket index out of range while draining buckets"
            );
            let mut bucket = Vec::new();
            std::mem::swap(&mut bucket, &mut self.core.ray_graph.edges[bucket_idx]);
            for edge in bucket.into_iter() {
                let target = self.edge_target_iteration(&edge);
                match target {
                    EdgeTarget::Scheduled(row) => self.core.ray_graph.schedule_edge(row, edge),
                    EdgeTarget::Stale(_) => {}
                    EdgeTarget::Discarded => {}
                }
            }
        }
    }

    pub(crate) fn edge_target_iteration(&self, edge: &AdjacencyEdge) -> EdgeTarget {
        let Some(ray1) = self.ray(edge.retained) else {
            return EdgeTarget::Discarded;
        };
        let Some(ray2) = self.ray(edge.removed) else {
            return EdgeTarget::Discarded;
        };
        let m = self.row_count();
        let f1 = self.first_infeasible_position_or_m(ray1);
        let f2 = self.first_infeasible_position_or_m(ray2);
        if f1 == f2 {
            return EdgeTarget::Discarded;
        }
        if f1 >= m && f2 >= m {
            return EdgeTarget::Discarded;
        }
        let fmin = f1.min(f2);
        if fmin < self.core.iter_state.iteration {
            return EdgeTarget::Stale(fmin);
        }
        EdgeTarget::Scheduled(fmin)
    }

    #[cfg(test)]
    pub(crate) fn add_ray(&mut self, vector: Vec<N>) -> RayId {
        let relaxed = self.core.options.relaxed_enumeration();
        let last_row = self.core.ctx.order_vector.first().copied();
        let m = self.row_count();
        let mut sets = self.core.ray_workspace.take_sets(m);
        let ray_data = {
            self.umpire.classify_vector(
                &self.core.ctx,
                vector,
                relaxed,
                last_row,
                &mut sets.negative_set,
            )
        };
        debug_assert!(!ray_data.as_ref().is_feasible() || ray_data.as_ref().is_weakly_feasible());
        self.umpire.on_ray_inserted(&sets.negative_set);
        let id = self.core.ray_graph.insert_active(ray_data);
        self.register_ray_id(id);
        self.record_new_ray(id);
        self.recycle_sets(sets);
        id
    }

    pub(crate) fn add_artificial_ray(&mut self) -> RayId {
        if let Some(idx) = self.core.ray_graph.artificial_ray() {
            return idx;
        }
        let dimension = self.col_count().max(1);
        let vector = vec![N::zero(); dimension];
        let last_row = self.core.ctx.order_vector.first().copied();
        let m = self.row_count();
        let mut sets = self.core.ray_workspace.take_sets(m);
        let ray_data = {
            let _guard = diag::push_context(diag::DiagContext::ArtificialRay);
            self.umpire.classify_vector(
                &self.core.ctx,
                vector,
                false,
                last_row,
                &mut sets.negative_set,
            )
        };
        self.recycle_sets(sets);
        let idx = self.core.ray_graph.insert_inactive(ray_data);
        self.core.ray_graph.set_artificial(idx);
        idx
    }

    pub(crate) fn evaluate_row_partition(&mut self, row: Row) -> RayPartitionOwned {
        self.core.lists = RayListHeads::default();
        let mut partition = std::mem::take(&mut self.core.partitions);
        partition.negative.clear();
        partition.positive.clear();
        partition.zero.clear();
        let mut active_order = self.core.ray_graph.take_active_order();
        {
            let ctx = &self.core.ctx;
            let (umpire, ray_graph) = (&mut self.umpire, &mut self.core.ray_graph);
            for &idx in active_order.iter() {
                let Some(ray_data) = ray_graph.ray_data_mut(idx) else {
                    continue;
                };
                let _guard =
                    diag::push_context(diag::DiagContext::ClassifyRay { row, ray: idx });
                let sign = umpire.classify_ray(ctx, ray_data, row);
                match sign {
                    Sign::Negative => partition.negative.push(idx),
                    Sign::Positive => partition.positive.push(idx),
                    Sign::Zero => partition.zero.push(idx),
                }
            }
        }

        self.core.lists.neg_head = partition.negative.first().copied();
        self.core.lists.neg_tail = partition.negative.last().copied();
        self.core.lists.pos_head = partition.positive.first().copied();
        self.core.lists.pos_tail = partition.positive.last().copied();
        self.core.lists.zero_head = partition.zero.first().copied();
        self.core.lists.zero_tail = partition.zero.last().copied();

        let floored_pos = self.enforce_first_infeasible_floor(&partition.positive);
        let floored_zero = self.enforce_first_infeasible_floor(&partition.zero);
        if floored_pos || floored_zero {
            self.core.edges_dirty = true;
        }

        let mut cursor = 0usize;
        for &id in partition
            .negative
            .iter()
            .chain(partition.positive.iter())
            .chain(partition.zero.iter())
        {
            if cursor < active_order.len() {
                active_order[cursor] = id;
            } else {
                active_order.push(id);
            }
            cursor += 1;
        }
        active_order.truncate(cursor);

        self.core
            .ray_graph
            .set_order_with_zero_count_unchecked(active_order, partition.zero.len());
        partition
    }

    pub(crate) fn create_new_ray(&mut self, r1: RayId, r2: RayId, row: Row) -> Option<RayId> {
        if r1 == r2 {
            return None;
        }

        let relaxed = self.core.options.relaxed_enumeration();
        let parent_a = self.core.ray_graph.ray_key(r1);
        let parent_b = self.core.ray_graph.ray_key(r2);
        let m = self.row_count();
        let mut sets = self.core.ray_workspace.take_sets(m);
        let ray_data = {
            let ray1 = self.core.ray_graph.ray_data(r1)?;
            let ray2 = self.core.ray_graph.ray_data(r2)?;
            let _guard = diag::push_context(diag::DiagContext::GenerateNewRay {
                row,
                parents: (r1, r2),
            });
            self.umpire.generate_new_ray(
                &self.core.ctx,
                (r1, ray1, r2, ray2),
                row,
                relaxed,
                &mut sets.negative_set,
            )?
        };
        if self.ray_exists(&ray_data) {
            self.core.dedup_drops = self.core.dedup_drops.wrapping_add(1);
            self.recycle_sets(sets);
            return None;
        }

        self.umpire.on_ray_inserted(&sets.negative_set);
        let id = self.core.ray_graph.insert_active(ray_data);
        self.core
            .ray_graph
            .set_ray_origin(id, Some(parent_a), Some(parent_b), Some(row));
        self.register_ray_id(id);
        self.record_new_ray(id);
        self.recycle_sets(sets);
        Some(id)
    }

    pub fn expand_ray_vector(&self, compact: &[N]) -> Vec<N> {
        assert_eq!(
            compact.len(),
            self.col_count(),
            "expand_ray_vector expects a vector of length col_count"
        );
        assert_eq!(
            self.core.iter_state.newcol.len(),
            self.core.iter_state.d_orig,
            "column remapping must match original dimension"
        );
        if !self.core.iter_state.col_reduced || self.core.iter_state.d_orig == self.col_count() {
            return compact.to_vec();
        }
        let mut full = vec![N::zero(); self.core.iter_state.d_orig];
        for (orig_idx, &map) in self.core.iter_state.newcol.iter().enumerate() {
            if let Some(m) = map {
                assert!(m < compact.len(), "column remapping out of range");
                // SAFETY: `orig_idx < d_orig == full.len()` by construction, and `m < compact.len()` asserted above.
                unsafe {
                    *full.get_unchecked_mut(orig_idx) = compact.get_unchecked(m).clone();
                }
            }
        }
        full
    }

    pub(crate) fn record_new_ray(&mut self, id: RayId) {
        self.core.pending_new_rays.push(id);
    }

    fn discard_pending_rays(&mut self, removed: &[RayId]) {
        if self.core.pending_new_rays.is_empty() || removed.is_empty() {
            return;
        }
        self.core.removed_epoch = self.core.removed_epoch.wrapping_add(1);
        if self.core.removed_epoch == 0 {
            self.core.removed_epoch = 1;
            self.core.removed_marks.fill(0);
        }

        let mut max_id = 0usize;
        for &rid in removed {
            max_id = max_id.max(rid.as_index());
        }
        for &rid in &self.core.pending_new_rays {
            max_id = max_id.max(rid.as_index());
        }
        if max_id >= self.core.removed_marks.len() {
            self.core.removed_marks.resize(max_id + 1, 0);
        }

        let epoch = self.core.removed_epoch;
        for &rid in removed {
            self.core.removed_marks[rid.as_index()] = epoch;
        }

        self.core
            .pending_new_rays
            .retain(|rid| self.core.removed_marks[rid.as_index()] != epoch);
    }

    pub(crate) fn ray(&self, index: RayId) -> Option<&Ray<N>> {
        self.core.ray_graph.ray(index)
    }

    pub(crate) fn ray_mut(&mut self, index: RayId) -> Option<&mut Ray<N>> {
        self.core.ray_graph.ray_mut(index)
    }

    pub(crate) fn with_active_ray_ids<T>(&mut self, f: impl FnOnce(&mut Self, &[RayId]) -> T) -> T {
        let mut ids = std::mem::take(&mut self.core.active_id_scratch);
        self.core.ray_graph.copy_active_ids(&mut ids);
        let result = f(self, &ids);
        self.core.active_id_scratch = ids;
        result
    }

    pub(crate) fn sync_tableau_flags(&mut self) {
        let m = self.row_count();
        if self.core.tableau.row_status.len() != m {
            self.core.tableau.row_status = vec![-1; m];
        } else {
            self.core.tableau.row_status.fill(-1);
        }
        for row in self.core.weakly_added_halfspaces.iter() {
            self.core.tableau.row_status[row.as_index()] = 0;
        }
        for row in self.core.added_halfspaces.iter() {
            self.core.tableau.row_status[row.as_index()] = 1;
        }
    }

    #[inline]
    pub(crate) fn sync_tableau_flag_for_row(&mut self, row: Row) {
        if row >= self.row_count() {
            return;
        }
        if self.core.tableau.row_status.len() != self.row_count() {
            self.sync_tableau_flags();
            return;
        }
        let flag = if self.core.added_halfspaces.contains(row) {
            1
        } else if self.core.weakly_added_halfspaces.contains(row) {
            0
        } else {
            -1
        };
        self.core.tableau.row_status[row] = flag;
    }

    pub(crate) fn enforce_first_infeasible_floor(&mut self, indices: &[RayId]) -> bool {
        let min_order = self.core.iter_state.iteration;
        if min_order >= self.core.ctx.order_vector.len() {
            return false;
        }
        let floor_row = self.core.ctx.order_vector[min_order];
        let mut changed = false;
        for &idx in indices {
            let should_floor = match self.ray(idx) {
                Some(ray) => {
                    if ray.class.last_sign == Sign::Negative {
                        false
                    } else {
                        self.first_infeasible_position(ray)
                            .map(|pos| pos < min_order)
                            .unwrap_or(false)
                    }
                }
                None => false,
            };
            if should_floor && let Some(ray) = self.ray_mut(idx) {
                ray.class.first_infeasible_row = Some(floor_row);
                changed = true;
            }
        }
        changed
    }

    fn adjacency_dimension(&self) -> usize {
        self.col_count()
    }
}

impl<N: Num, R: Representation, U: Umpire<N, R>> ConeEngine<N, R, U> {
    pub fn feasibility_indices(&mut self, row: Row) -> (usize, usize) {
        let active = self.core.ray_graph.active_len();
        if row >= self.row_count() {
            return (active, 0);
        }

        let mut infeasible = 0usize;
        let mut ids = std::mem::take(&mut self.core.active_id_scratch);
        self.core.ray_graph.copy_active_ids(&mut ids);
        for id in ids.iter().copied() {
            let Some(ray_data) = self.core.ray_graph.ray_data(id) else {
                continue;
            };
            if self
                .umpire
                .sign_for_row_on_ray(&self.core.ctx, ray_data, row)
                == Sign::Negative
            {
                infeasible += 1;
            }
        }
        self.core.active_id_scratch = ids;

        assert!(active >= infeasible, "infeasible count exceeds active rays");
        (active - infeasible, infeasible)
    }
}
