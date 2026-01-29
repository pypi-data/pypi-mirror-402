pub mod context;
pub mod dd;
pub mod error;
pub mod lp;
pub mod lrs;
pub mod matrix;
pub mod polyhedron;
pub mod verify;

pub use error::HowzatError;

/// Type alias for backward compatibility during migration.
pub type Error = HowzatError;
