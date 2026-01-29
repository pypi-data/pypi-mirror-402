#[cfg(any(test, debug_assertions))]
mod imp {
    use std::cell::RefCell;
    use std::sync::OnceLock;

    use calculo::num::{Epsilon, Num, Sign};
    use hullabaloo::types::Row;

    use crate::dd::ray::RayId;

    #[cfg(feature = "rug")]
    use calculo::num::RugRat;

    #[derive(Clone, Debug)]
    pub(crate) enum DiagContext {
        ClassifyRay { row: Row, ray: RayId },
        GenerateNewRay { row: Row, parents: (RayId, RayId) },
        InitializeRay {
            col: usize,
            negated: bool,
            pivot_row: Option<Row>,
            pre_norm_max_abs: Option<f64>,
        },
        ArtificialRay,
    }

    impl std::fmt::Display for DiagContext {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            match self {
                Self::ClassifyRay { row, ray } => write!(f, "ClassifyRay(row={row}, ray={ray:?})"),
                Self::GenerateNewRay { row, parents } => {
                    write!(f, "GenerateNewRay(row={row}, parents={parents:?})")
                }
                Self::InitializeRay {
                    col,
                    negated,
                    pivot_row,
                    pre_norm_max_abs,
                } => write!(
                    f,
                    "InitializeRay(col={col}, negated={negated}, pivot_row={pivot_row:?}, pre_norm_max_abs={pre_norm_max_abs:?})"
                ),
                Self::ArtificialRay => write!(f, "ArtificialRay"),
            }
        }
    }

    thread_local! {
        static DIAG_CONTEXT: RefCell<Vec<DiagContext>> = RefCell::new(Vec::new());
    }

    #[derive(Debug)]
    pub(crate) struct DiagGuard {
        enabled: bool,
        depth: usize,
    }

    impl Drop for DiagGuard {
        fn drop(&mut self) {
            if !self.enabled {
                return;
            }
            DIAG_CONTEXT.with(|ctx| {
                let mut stack = ctx.borrow_mut();
                stack.truncate(self.depth);
            });
        }
    }

    #[inline(always)]
    pub(crate) fn enabled() -> bool {
        static ENABLED: OnceLock<bool> = OnceLock::new();
        *ENABLED.get_or_init(|| std::env::var_os("HOWZAT_DD_EXACT_SIGN").is_some())
    }

    #[inline(always)]
    pub(crate) fn push_context(context: DiagContext) -> DiagGuard {
        if !enabled() {
            return DiagGuard {
                enabled: false,
                depth: 0,
            };
        }

        DIAG_CONTEXT.with(|ctx| {
            let mut stack = ctx.borrow_mut();
            let depth = stack.len();
            stack.push(context);
            DiagGuard {
                enabled: true,
                depth,
            }
        })
    }

    fn format_context_stack() -> String {
        DIAG_CONTEXT.with(|ctx| {
            let stack = ctx.borrow();
            if stack.is_empty() {
                return "-".to_string();
            }
            stack
                .iter()
                .map(ToString::to_string)
                .collect::<Vec<_>>()
                .join(" -> ")
        })
    }

    #[cfg(feature = "rug")]
    fn exact_dot_rugrat(row: &[f64], ray: &[f64]) -> RugRat {
        debug_assert_eq!(row.len(), ray.len(), "dot length mismatch");
        let mut acc = RugRat::zero();
        for (&a, &b) in row.iter().zip(ray.iter()) {
            let ar = RugRat::try_from_f64(a).expect("exact dot requires finite f64");
            let br = RugRat::try_from_f64(b).expect("exact dot requires finite f64");
            acc = acc + ar * br;
        }
        acc
    }

    #[cfg(feature = "rug")]
    fn strict_sign_for_rugrat(value: &RugRat) -> Sign {
        if value == &RugRat::zero() {
            return Sign::Zero;
        }
        if value > &RugRat::zero() {
            return Sign::Positive;
        }
        Sign::Negative
    }

    pub(crate) fn check_row_eval_sign<N: Num, E: Epsilon<N>>(
        eps: &E,
        eval_row: Row,
        row: &[N],
        ray: &[N],
        computed: &N,
        note: &'static str,
    ) {
        if !enabled() {
            return;
        }

        if std::any::type_name::<N>() != "f64" {
            return;
        }

        #[cfg(feature = "rug")]
        {
            let row_f64: &[f64] =
                unsafe { std::slice::from_raw_parts(row.as_ptr() as *const f64, row.len()) };
            let ray_f64: &[f64] =
                unsafe { std::slice::from_raw_parts(ray.as_ptr() as *const f64, ray.len()) };
            let computed_f64 = unsafe { *(computed as *const N as *const f64) };
            let eps_f64 = unsafe { *(eps.eps() as *const N as *const f64) };

            let exact = exact_dot_rugrat(row_f64, ray_f64);
            let exact_sign = strict_sign_for_rugrat(&exact);
            let computed_sign = eps.sign(computed);

            if computed_sign == exact_sign {
                return;
            }

            let computed_rat = RugRat::try_from_f64(computed_f64).expect("finite f64 required");
            let diff = exact.ref_sub(&computed_rat);
            let eps_rat = RugRat::try_from_f64(eps_f64).expect("finite f64 required");
            let abs_exact = exact.abs();
            let exact_f64 = exact.to_f64();
            let abs_exact_f64 = abs_exact.to_f64();
            let diff_f64 = diff.to_f64();

            let ctx = format_context_stack();
            panic!(
                concat!(
                    "howzat dd strict-sign mismatch ({note}): eval_row={eval_row} ctx={ctx}\n",
                    "  computed={computed_f64:.17e} sign={computed_sign:?}\n",
                    "  exact={exact} (~{exact_f64:.17e}) strict_sign={exact_sign:?}\n",
                    "  |exact|={abs_exact} (~{abs_exact_f64:.17e})\n",
                    "  eps={eps_f64:.17e} (= {eps_rat})\n",
                    "  exact-computed={diff} (~{diff_f64:.17e})",
                ),
                note = note,
                eval_row = eval_row,
                ctx = ctx,
                computed_f64 = computed_f64,
                computed_sign = computed_sign,
                exact = exact,
                exact_f64 = exact_f64,
                exact_sign = exact_sign,
                abs_exact = abs_exact,
                abs_exact_f64 = abs_exact_f64,
                eps_f64 = eps_f64,
                eps_rat = eps_rat,
                diff = diff,
                diff_f64 = diff_f64,
            );
        }
    }
}

#[cfg(not(any(test, debug_assertions)))]
mod imp {
    use calculo::num::{Epsilon, Num};
    use hullabaloo::types::Row;

    use crate::dd::ray::RayId;

    #[allow(dead_code)]
    #[derive(Clone, Debug)]
    pub(crate) enum DiagContext {
        ClassifyRay { row: Row, ray: RayId },
        GenerateNewRay { row: Row, parents: (RayId, RayId) },
        InitializeRay {
            col: usize,
            negated: bool,
            pivot_row: Option<Row>,
            pre_norm_max_abs: Option<f64>,
        },
        ArtificialRay,
    }

    #[derive(Debug)]
    pub(crate) struct DiagGuard;

    #[inline(always)]
    pub(crate) fn enabled() -> bool {
        false
    }

    #[inline(always)]
    pub(crate) fn push_context(_context: DiagContext) -> DiagGuard {
        DiagGuard
    }

    #[inline(always)]
    pub(crate) fn check_row_eval_sign<N: Num, E: Epsilon<N>>(
        _eps: &E,
        _eval_row: Row,
        _row: &[N],
        _ray: &[N],
        _computed: &N,
        _note: &'static str,
    ) {
    }
}

pub(crate) use imp::*;
