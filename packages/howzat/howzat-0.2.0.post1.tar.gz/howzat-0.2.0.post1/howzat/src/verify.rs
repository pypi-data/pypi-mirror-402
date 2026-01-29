use crate::lp::LpResult;
use crate::polyhedron::{PolyhedronOptions, PolyhedronOutput};
use calculo::num::{CoerceFrom, Epsilon, Num, Rat};
use hullabaloo::set_family::SetFamily;
use hullabaloo::types::{DualRepresentation, Generator, Row};

pub use crate::lp::{LpBasisStatusIssue, LpBasisStatusResult};
pub use crate::polyhedron::repair::{
    FacetGraphRepairDiagnostics, FacetGraphRepairError, FacetGraphRepairOptions,
    FacetGraphRepairReport, FacetGraphRepairResult, FrontierRepairMode, FrontierRepairReport,
    GeneralFrontierRepairDiagnostics, GeneralFrontierRepairReport, RepairedFacet, SimplicialFacet,
    SimplicialFrontierRepairDiagnostics, SimplicialFrontierRepairError,
    SimplicialFrontierRepairOptions, SimplicialFrontierRepairReport,
    SimplicialFrontierRepairResult,
};
pub use crate::polyhedron::{
    PartialResolveIssue, PartialResolveResult, PreparedPartialRepairResolveResult,
    PreparedPartialResolveResult, ResolveError, ResolveOptions,
};

#[derive(Clone, Debug)]
pub struct SimplicialFrontierRidge {
    ridge: Vec<Row>,
    incident_facet: usize,
    dropped_vertex: Row,
}

impl SimplicialFrontierRidge {
    pub fn ridge(&self) -> &[Row] {
        &self.ridge
    }

    pub fn incident_facet(&self) -> usize {
        self.incident_facet
    }

    pub fn dropped_vertex(&self) -> Row {
        self.dropped_vertex
    }
}

pub fn simplicial_frontier_ridge_count(facets: &[Vec<Row>], facet_dimension: usize) -> usize {
    crate::polyhedron::repair::simplicial_frontier_ridge_count(facets, facet_dimension)
}

pub fn simplicial_frontier_ridges(
    facets: &[Vec<Row>],
    facet_dimension: usize,
) -> Vec<SimplicialFrontierRidge> {
    crate::polyhedron::repair::simplicial_frontier_ridges_by_facet_index(facets, facet_dimension)
        .into_iter()
        .map(
            |(ridge, (facet_idx, dropped_vertex))| SimplicialFrontierRidge {
                ridge,
                incident_facet: facet_idx,
                dropped_vertex,
            },
        )
        .collect()
}

#[derive(Clone, Copy, Debug)]
pub struct Certificate<'a, N: Num, R: DualRepresentation> {
    poly: &'a PolyhedronOutput<N, R>,
    incidence: &'a SetFamily,
}

#[derive(Clone, Copy, Debug)]
pub enum CertificateError {
    MissingOutputIncidence,
}

pub fn lp_basis_status<N: Num>(
    solution: &LpResult<N>,
    eps: &impl Epsilon<N>,
) -> LpBasisStatusResult<N> {
    solution.verify_basis_status_internal::<N>(eps)
}

pub fn lp_basis_status_as<N: Num, M>(
    solution: &LpResult<N>,
    eps: &impl Epsilon<M>,
) -> LpBasisStatusResult<M>
where
    M: Num + CoerceFrom<N>,
{
    solution.verify_basis_status_internal::<M>(eps)
}

pub fn certificate<N: Num, R: DualRepresentation>(
    poly: &PolyhedronOutput<N, R>,
) -> Result<Certificate<'_, N, R>, CertificateError> {
    let Some(incidence) = poly.incidence() else {
        return Err(CertificateError::MissingOutputIncidence);
    };
    Ok(Certificate { poly, incidence })
}

impl<'a, N: Num, R: DualRepresentation> Certificate<'a, N, R> {
    pub fn polyhedron(&self) -> &'a PolyhedronOutput<N, R> {
        self.poly
    }

    pub fn resolve_as<M>(
        &self,
        poly_options: PolyhedronOptions,
        options: ResolveOptions,
        eps: &impl Epsilon<M>,
    ) -> Result<PolyhedronOutput<M, R>, ResolveError<M>>
    where
        M: Rat + CoerceFrom<N>,
        <M as Rat>::Int: std::ops::SubAssign<<M as Rat>::Int>,
        for<'b> <M as Rat>::Int: std::ops::AddAssign<&'b <M as Rat>::Int>,
    {
        self.poly
            .resolve_from_incidence_certificate_as(&poly_options, self.incidence, options, eps)
    }

    pub fn resolve_partial_as<M>(
        &self,
        poly_options: PolyhedronOptions,
        options: ResolveOptions,
        eps: &impl Epsilon<M>,
    ) -> Result<PartialResolveResult<M, R>, ResolveError<M>>
    where
        M: Rat + CoerceFrom<N>,
        <M as Rat>::Int: std::ops::SubAssign<<M as Rat>::Int>,
        for<'b> <M as Rat>::Int: std::ops::AddAssign<&'b <M as Rat>::Int>,
    {
        self.poly.resolve_partial_from_incidence_certificate_as(
            &poly_options,
            self.incidence,
            options,
            eps,
        )
    }

    pub fn resolve_partial_prepared_as<M>(
        &self,
        poly_options: PolyhedronOptions,
        options: ResolveOptions,
        eps: &impl Epsilon<M>,
    ) -> Result<PreparedPartialResolveResult<M, R>, ResolveError<M>>
    where
        M: Rat + CoerceFrom<N>,
        <M as Rat>::Int: std::ops::SubAssign<<M as Rat>::Int>,
        for<'b> <M as Rat>::Int: std::ops::AddAssign<&'b <M as Rat>::Int>,
    {
        self.poly
            .resolve_partial_from_incidence_certificate_as_prepared(
                &poly_options,
                self.incidence,
                options,
                eps,
            )
    }

    pub fn resolve_partial_prepared_minimal_as<M>(
        &self,
        poly_options: PolyhedronOptions,
        options: ResolveOptions,
        eps: &impl Epsilon<M>,
    ) -> Result<PreparedPartialRepairResolveResult<M, R>, ResolveError<M>>
    where
        M: Rat + CoerceFrom<N>,
        <M as Rat>::Int: std::ops::SubAssign<<M as Rat>::Int>,
        for<'b> <M as Rat>::Int: std::ops::AddAssign<&'b <M as Rat>::Int>,
    {
        self.poly
            .resolve_partial_from_incidence_certificate_as_prepared_minimal(
                &poly_options,
                self.incidence,
                options,
                eps,
            )
    }
}

pub fn repair_simplicial_frontier<N: Num>(
    partial: &PartialResolveResult<N, Generator>,
    options: SimplicialFrontierRepairOptions,
    eps: &impl Epsilon<N>,
) -> Result<SimplicialFrontierRepairResult<N>, SimplicialFrontierRepairError> {
    partial.repair_simplicial_frontier(options, eps)
}

pub fn repair_facet_graph<M: Rat, N: Num>(
    partial: &PartialResolveResult<M, Generator>,
    inexact: &PolyhedronOutput<N, Generator>,
    options: FacetGraphRepairOptions,
    eps: &impl Epsilon<M>,
) -> Result<FacetGraphRepairResult<M>, FacetGraphRepairError>
where
    <M as Rat>::Int: std::ops::SubAssign<<M as Rat>::Int>,
    for<'b> <M as Rat>::Int: std::ops::AddAssign<&'b <M as Rat>::Int>,
{
    partial.repair_facet_graph(inexact, options, eps)
}

pub trait PreparedFacetGraphRepair<M: Rat> {
    fn repair_facet_graph_from_inexact_prepared<N: Num>(
        &self,
        inexact: &PolyhedronOutput<N, Generator>,
        options: FacetGraphRepairOptions,
        eps: &impl Epsilon<M>,
    ) -> Result<FacetGraphRepairResult<M>, FacetGraphRepairError>;
}

impl<M: Rat> PreparedFacetGraphRepair<M> for PreparedPartialResolveResult<M, Generator>
where
    <M as Rat>::Int: std::ops::SubAssign<<M as Rat>::Int>,
    for<'a> <M as Rat>::Int: std::ops::AddAssign<&'a <M as Rat>::Int>,
{
    fn repair_facet_graph_from_inexact_prepared<N: Num>(
        &self,
        inexact: &PolyhedronOutput<N, Generator>,
        options: FacetGraphRepairOptions,
        eps: &impl Epsilon<M>,
    ) -> Result<FacetGraphRepairResult<M>, FacetGraphRepairError> {
        PreparedPartialResolveResult::repair_facet_graph_from_inexact_prepared(
            self, inexact, options, eps,
        )
    }
}

impl<M: Rat> PreparedFacetGraphRepair<M> for PreparedPartialRepairResolveResult<M, Generator>
where
    <M as Rat>::Int: std::ops::SubAssign<<M as Rat>::Int>,
    for<'a> <M as Rat>::Int: std::ops::AddAssign<&'a <M as Rat>::Int>,
{
    fn repair_facet_graph_from_inexact_prepared<N: Num>(
        &self,
        inexact: &PolyhedronOutput<N, Generator>,
        options: FacetGraphRepairOptions,
        eps: &impl Epsilon<M>,
    ) -> Result<FacetGraphRepairResult<M>, FacetGraphRepairError> {
        PreparedPartialRepairResolveResult::repair_facet_graph_from_inexact_prepared(
            self, inexact, options, eps,
        )
    }
}

pub fn repair_facet_graph_from_inexact_prepared<M: Rat, N: Num>(
    prepared: &impl PreparedFacetGraphRepair<M>,
    inexact: &PolyhedronOutput<N, Generator>,
    options: FacetGraphRepairOptions,
    eps: &impl Epsilon<M>,
) -> Result<FacetGraphRepairResult<M>, FacetGraphRepairError>
where
    <M as Rat>::Int: std::ops::SubAssign<<M as Rat>::Int>,
    for<'b> <M as Rat>::Int: std::ops::AddAssign<&'b <M as Rat>::Int>,
{
    prepared.repair_facet_graph_from_inexact_prepared(inexact, options, eps)
}
