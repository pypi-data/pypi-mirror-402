//! Lexicographic reverse search (LRS) traversal.

mod tableau;
mod util;

mod enumerator;
mod input;
mod ops;
mod output;

pub use calculo::num::{Int, IntError};
pub use enumerator::Traversal;
pub use input::traversal_from_matrix;
pub use output::{enumerate_rows, enumerate_rows_with_incidence};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Cursor {
    Scan { next_cobasis_pos: usize },
    Backtrack,
}

/// Restart configuration for a traversal.
#[derive(Clone, Debug)]
pub enum Start {
    Root,
    Cobasis { cobasis: Vec<u32> },
    Checkpoint(Checkpoint),
}

/// A compact restart checkpoint expressed in terms of variable indices and traversal cursor state.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Checkpoint {
    pub cobasis: Vec<u32>,
    pub depth: usize,
    pub cursor: Cursor,
}

#[derive(Clone, Debug)]
pub struct Options {
    pub cache_limit: usize,
    pub emit_all_bases: bool,
    pub max_depth: Option<usize>,
    pub start: Start,
}

impl Default for Options {
    fn default() -> Self {
        Self {
            cache_limit: 0,
            emit_all_bases: false,
            max_depth: None,
            start: Start::Root,
        }
    }
}

#[derive(Clone, Debug)]
pub enum Error {
    DimensionTooLarge,
    Infeasible,
    InvalidWarmStart,
    Arithmetic(IntError),
    InvariantViolation,
}

pub type Result<T> = std::result::Result<T, Error>;

impl From<IntError> for Error {
    fn from(value: IntError) -> Self {
        Self::Arithmetic(value)
    }
}
