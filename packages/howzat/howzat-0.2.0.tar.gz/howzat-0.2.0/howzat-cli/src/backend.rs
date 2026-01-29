use std::{
    collections::HashMap,
    fmt,
    time::{Duration, Instant},
};

use anyhow::{anyhow, ensure};
use calculo::num::{
    CoerceFrom, DashuFloat, DashuRat, DynamicEpsilon, Epsilon, F64Em12Epsilon, F64Em7Epsilon,
    F64Em9Epsilon, GcdNormalizer, MaxNormalizer, MinNormalizer, NoNormalizer, Normalizer, Num,
    Rat, RugFloat, RugRat,
};
use howzat::dd::{
    ConeOptions, DefaultNormalizer, SinglePrecisionUmpire as SpUmpire, SnapPurifier as Snap,
    UpcastingSnapPurifier,
};
use hullabaloo::types::{AdjacencyOutput, IncidenceOutput, RowId, RowSet};
use serde::{Deserialize, Serialize};
use tracing::warn;

use lrslib_rs as lrslib;

use crate::polytope::howzat::build_generator_matrix_vertices;
use crate::polytope::{rowset_from_list, rowsets_from_adjacency_lists};
use crate::vertices::{VerticesF64, VerticesRowMajor, VerticesVecVec};

#[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
enum HowzatDdNum {
    F64,
    RugFloat128,
    RugFloat256,
    RugFloat512,
    DashuFloat128,
    DashuFloat256,
    DashuFloat512,
    RugRat,
    DashuRat,
}

impl HowzatDdNum {
    fn canonical_token(self) -> &'static str {
        match self {
            Self::F64 => "f64",
            Self::RugFloat128 => "rugfloat[128]",
            Self::RugFloat256 => "rugfloat[256]",
            Self::RugFloat512 => "rugfloat[512]",
            Self::DashuFloat128 => "dashufloat[128]",
            Self::DashuFloat256 => "dashufloat[256]",
            Self::DashuFloat512 => "dashufloat[512]",
            Self::RugRat => "rugrat",
            Self::DashuRat => "dashurat",
        }
    }
}

#[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
enum HowzatDdNormalizer {
    No,
    Min,
    Max,
    Gcd,
}

impl HowzatDdNormalizer {
    fn canonical_token(self) -> &'static str {
        match self {
            Self::No => "no",
            Self::Min => "min",
            Self::Max => "max",
            Self::Gcd => "gcd",
        }
    }
}

#[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
enum HowzatDdPurifierSpec {
    Snap,
    UpSnap(HowzatDdNum),
}

impl HowzatDdPurifierSpec {
    fn canonical_token(self) -> String {
        match self {
            Self::Snap => "snap".to_string(),
            Self::UpSnap(target) => format!("upsnap[{}]", target.canonical_token()),
        }
    }
}

#[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
enum HowzatDdF64Eps {
    BuiltinEm7,
    BuiltinEm9,
    BuiltinEm12,
    Dynamic(u64),
}

impl HowzatDdF64Eps {
    fn canonical_value_token(self) -> String {
        match self {
            Self::BuiltinEm7 => "1e-7".to_string(),
            Self::BuiltinEm9 => "1e-9".to_string(),
            Self::BuiltinEm12 => "1e-12".to_string(),
            Self::Dynamic(bits) => format!("{:.17e}", f64::from_bits(bits)),
        }
    }
}

#[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
struct HowzatDdCompute {
    num: HowzatDdNum,
    f64_eps: Option<HowzatDdF64Eps>,
    normalizer: Option<HowzatDdNormalizer>,
}

impl HowzatDdCompute {
    fn canonical_token(self) -> String {
        let num = self.num.canonical_token();
        if self.num == HowzatDdNum::F64 && (self.f64_eps.is_some() || self.normalizer.is_some()) {
            let mut parts = Vec::new();
            if let Some(eps) = self.f64_eps {
                parts.push(format!("eps[{}]", eps.canonical_value_token()));
            }
            if let Some(normalizer) = self.normalizer {
                parts.push(normalizer.canonical_token().to_string());
            }
            return format!("{num}[{}]", parts.join(","));
        }

        let Some(normalizer) = self.normalizer else {
            return num.to_string();
        };
        format!("{num}[{}]", normalizer.canonical_token())
    }
}

#[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
enum HowzatDdCheckKind {
    Resolve,
    Repair,
}

impl HowzatDdCheckKind {
    fn canonical_token(self) -> &'static str {
        match self {
            Self::Resolve => "resolve",
            Self::Repair => "repair",
        }
    }
}

#[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
struct HowzatDdCheck {
    kind: HowzatDdCheckKind,
    target: HowzatDdNum,
}

impl HowzatDdCheck {
    fn canonical_token(self) -> String {
        format!(
            "{}[{}]",
            self.kind.canonical_token(),
            self.target.canonical_token()
        )
    }
}

#[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
enum HowzatDdStep {
    Compute(HowzatDdCompute),
    Check(HowzatDdCheck),
}

impl HowzatDdStep {
    fn canonical_token(self) -> String {
        match self {
            Self::Compute(compute) => compute.canonical_token(),
            Self::Check(check) => check.canonical_token(),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
struct HowzatDdPipelineSpec {
    steps: Vec<HowzatDdStep>,
}

impl HowzatDdPipelineSpec {
    fn canonical(&self) -> String {
        self.steps
            .iter()
            .copied()
            .map(HowzatDdStep::canonical_token)
            .collect::<Vec<_>>()
            .join("-")
    }
}

const DEFAULT_HOWZAT_DD_PIPELINE: &str = "f64-repair[rugrat]";

fn split_howzat_dd_brackets(raw: &str) -> Option<(&str, Vec<&str>)> {
    let token = raw.trim();
    if token.is_empty() {
        return None;
    }

    if !token.contains('[') && token.contains(']') {
        return None;
    }

    let base_end = token.find('[').unwrap_or(token.len());
    let base = token.get(..base_end)?.trim();
    if base.is_empty() {
        return None;
    }

    let mut brackets: Vec<&str> = Vec::new();
    let mut pos = base_end;
    while pos < token.len() {
        let tail = token.get(pos..)?;
        let after_open = tail.strip_prefix('[')?;
        let mut depth = 1usize;
        let mut idx = 0usize;
        for (offset, ch) in after_open.char_indices() {
            match ch {
                '[' => depth += 1,
                ']' => {
                    depth = depth.saturating_sub(1);
                    if depth == 0 {
                        idx = offset;
                        break;
                    }
                }
                _ => {}
            }
        }
        if depth != 0 {
            return None;
        }

        let inner = after_open.get(..idx)?.trim();
        brackets.push(inner);
        pos = token
            .len()
            .saturating_sub(after_open.len())
            .saturating_add(idx + 1);
    }

    Some((base, brackets))
}

fn parse_howzat_dd_purifier(raw: &str) -> Result<HowzatDdPurifierSpec, String> {
    let token = raw.trim();
    if token.is_empty() {
        return Err("howzat-dd purifier cannot be empty".to_string());
    }
    let Some((base, brackets)) = split_howzat_dd_brackets(token) else {
        return Err(format!(
            "invalid howzat-dd purifier '{token}' (expected snap or upsnap[rugrat|dashurat])"
        ));
    };

    match base {
        "snap" => {
            if !brackets.is_empty() {
                return Err("snap does not take parameters (expected snap)".to_string());
            }
            Ok(HowzatDdPurifierSpec::Snap)
        }
        "upsnap" => {
            let [target_raw] = brackets.as_slice() else {
                return Err("upsnap expects exactly one parameter: upsnap[rugrat|dashurat]".to_string());
            };
            let Some(target) = parse_howzat_dd_num(target_raw) else {
                return Err(format!(
                    "unknown upsnap target '{target_raw}' (expected rugrat or dashurat)"
                ));
            };
            if !matches!(target, HowzatDdNum::RugRat | HowzatDdNum::DashuRat) {
                return Err(format!(
                    "upsnap only supports targets '{}' and '{}' (got '{}')",
                    HowzatDdNum::RugRat.canonical_token(),
                    HowzatDdNum::DashuRat.canonical_token(),
                    target.canonical_token()
                ));
            }
            Ok(HowzatDdPurifierSpec::UpSnap(target))
        }
        _ => Err(format!(
            "unknown howzat-dd purifier '{token}' (expected snap or upsnap[rugrat|dashurat])"
        )),
    }
}

fn parse_howzat_dd_num(raw: &str) -> Option<HowzatDdNum> {
    let (base, brackets) = split_howzat_dd_brackets(raw)?;

    match (base, brackets.as_slice()) {
        ("f64", []) => return Some(HowzatDdNum::F64),
        ("rugrat", []) => return Some(HowzatDdNum::RugRat),
        ("dashurat", []) => return Some(HowzatDdNum::DashuRat),
        _ => {}
    }

    let bits = match (base, brackets.as_slice()) {
        ("rugfloat" | "dashufloat", [bits]) => bits.parse::<u32>().ok(),
        _ => None,
    }?;

    match (base, bits) {
        ("rugfloat", 128) => Some(HowzatDdNum::RugFloat128),
        ("rugfloat", 256) => Some(HowzatDdNum::RugFloat256),
        ("rugfloat", 512) => Some(HowzatDdNum::RugFloat512),
        ("dashufloat", 128) => Some(HowzatDdNum::DashuFloat128),
        ("dashufloat", 256) => Some(HowzatDdNum::DashuFloat256),
        ("dashufloat", 512) => Some(HowzatDdNum::DashuFloat512),
        _ => None,
    }
}

fn parse_howzat_dd_normalizer(raw: &str) -> Option<HowzatDdNormalizer> {
    match raw.trim() {
        "no" => Some(HowzatDdNormalizer::No),
        "min" => Some(HowzatDdNormalizer::Min),
        "max" => Some(HowzatDdNormalizer::Max),
        "gcd" => Some(HowzatDdNormalizer::Gcd),
        _ => None,
    }
}

fn parse_howzat_dd_compute(raw: &str) -> Result<Option<HowzatDdCompute>, String> {
    let token = raw.trim();
    if token.is_empty() {
        return Ok(None);
    }

    let Some((base, brackets)) = split_howzat_dd_brackets(token) else {
        return Ok(None);
    };

    fn split_bracket_options(raw: &str) -> Result<Vec<&str>, String> {
        let raw = raw.trim();
        if raw.is_empty() {
            return Err("option list cannot be empty".to_string());
        }

        let mut parts = Vec::new();
        let mut depth = 0usize;
        let mut start = 0usize;
        for (idx, ch) in raw.char_indices() {
            match ch {
                '[' => depth += 1,
                ']' => {
                    depth = depth
                        .checked_sub(1)
                        .ok_or_else(|| "option list contains unmatched ']'".to_string())?;
                }
                ',' if depth == 0 => {
                    parts.push(raw[start..idx].trim());
                    start = idx + ch.len_utf8();
                }
                _ => {}
            }
        }
        if depth != 0 {
            return Err("option list contains unmatched '['".to_string());
        }
        parts.push(raw[start..].trim());

        if parts.iter().any(|p| p.is_empty()) {
            return Err("option list contains empty elements".to_string());
        }
        Ok(parts)
    }

    let (num, f64_eps, normalizer_raw): (HowzatDdNum, Option<HowzatDdF64Eps>, Option<&str>) =
        match base {
            "f64" => {
                let mut eps = None;
                let mut norm = None;

                if brackets.len() > 1 {
                    return Err(
                        "f64 accepts a single option list: f64[eps[...],no|min|max]".to_string(),
                    );
                }

                for &bracket_group in &brackets {
                    for option in split_bracket_options(bracket_group)? {
                        if let Some(inner) = option
                            .strip_prefix("eps[")
                            .and_then(|s| s.strip_suffix(']'))
                        {
                            if eps.is_some() {
                                return Err(
                                    "f64 accepts at most one eps spec: f64[eps[...],...]"
                                        .to_string(),
                                );
                            }
                            let raw = inner.trim();
                            let value = raw.parse::<f64>().map_err(|_| {
                                format!(
                                    "invalid f64 eps '{raw}' (expected a finite floating literal)"
                                )
                            })?;
                            if !value.is_finite() || value < 0.0 {
                                return Err(format!(
                                    "invalid f64 eps '{raw}' (expected a finite non-negative float)"
                                ));
                            }

                            let bits = value.to_bits();
                            eps = Some(if bits == (1.0e-7f64).to_bits() {
                                HowzatDdF64Eps::BuiltinEm7
                            } else if bits == (1.0e-9f64).to_bits() {
                                HowzatDdF64Eps::BuiltinEm9
                            } else if bits == (1.0e-12f64).to_bits() {
                                HowzatDdF64Eps::BuiltinEm12
                            } else {
                                warn!(
                                    "howzat-dd:f64 uses non-builtin eps={raw} (parsed={parsed:.17e}); \
cannot inline at compile time; performance may be degraded",
                                    raw = raw,
                                    parsed = value,
                                );
                                HowzatDdF64Eps::Dynamic(bits)
                            });
                            continue;
                        }

                        if norm.is_some() {
                            return Err(
                                "f64 accepts at most one normalizer option: f64[...,no|min|max]"
                                    .to_string(),
                            );
                        }
                        norm = Some(option);
                    }
                }
                (HowzatDdNum::F64, eps, norm)
            }
            "rugrat" => match brackets.as_slice() {
                [] => (HowzatDdNum::RugRat, None, None),
                [norm] => (HowzatDdNum::RugRat, None, Some(*norm)),
                _ => {
                    return Err(
                        "rugrat accepts at most one normalizer suffix: rugrat[no|min|max|gcd]"
                            .to_string(),
                    );
                }
            },
            "dashurat" => match brackets.as_slice() {
                [] => (HowzatDdNum::DashuRat, None, None),
                [norm] => (HowzatDdNum::DashuRat, None, Some(*norm)),
                _ => {
                    return Err(
                        "dashurat accepts at most one normalizer suffix: dashurat[no|min|max|gcd]"
                            .to_string(),
                    );
                }
            },
            "rugfloat" | "dashufloat" => {
                let bits = brackets
                    .first()
                    .copied()
                    .ok_or_else(|| format!("{base} requires a precision: {base}[128|256|512]"))?;
                let bits = bits.parse::<u32>().map_err(|_| {
                    format!("unsupported {base} precision '{bits}' (supported: 128, 256, 512)")
                })?;
                let num = match (base, bits) {
                    ("rugfloat", 128) => HowzatDdNum::RugFloat128,
                    ("rugfloat", 256) => HowzatDdNum::RugFloat256,
                    ("rugfloat", 512) => HowzatDdNum::RugFloat512,
                    ("dashufloat", 128) => HowzatDdNum::DashuFloat128,
                    ("dashufloat", 256) => HowzatDdNum::DashuFloat256,
                    ("dashufloat", 512) => HowzatDdNum::DashuFloat512,
                    _ => {
                        return Err(format!(
                            "unsupported {base} precision '{bits}' (supported: 128, 256, 512)"
                        ));
                    }
                };
                let normalizer_raw = match brackets.as_slice() {
                    [_bits] => None,
                    [_bits, norm] => Some(*norm),
                    _ => {
                        return Err(format!(
                            "{base} accepts at most one normalizer suffix: {base}[bits][no|min|max]"
                        ));
                    }
                };
                (num, None, normalizer_raw)
            }
            _ => return Ok(None),
        };

    let allow_gcd = matches!(num, HowzatDdNum::RugRat | HowzatDdNum::DashuRat);
    let normalizer = match normalizer_raw {
        None => None,
        Some(raw) => Some(parse_howzat_dd_normalizer(raw).ok_or_else(|| {
            if allow_gcd {
                format!("unknown howzat-dd normalizer '{raw}' (expected no|min|max|gcd)")
            } else {
                format!("unknown howzat-dd normalizer '{raw}' (expected no|min|max)")
            }
        })?),
    };

    if normalizer == Some(HowzatDdNormalizer::Gcd) && !allow_gcd {
        return Err(format!(
            "normalizer [{}] is only supported for rugrat/dashurat (got {})",
            HowzatDdNormalizer::Gcd.canonical_token(),
            num.canonical_token()
        ));
    }

    Ok(Some(HowzatDdCompute {
        num,
        f64_eps,
        normalizer,
    }))
}

fn parse_howzat_dd_check(raw: &str) -> Result<Option<HowzatDdCheck>, String> {
    let token = raw.trim();
    if token.is_empty() {
        return Ok(None);
    }

    let (kind, inner) = if let Some(inner) = token
        .strip_prefix("resolve[")
        .and_then(|s| s.strip_suffix(']'))
    {
        (HowzatDdCheckKind::Resolve, inner)
    } else if let Some(inner) = token
        .strip_prefix("repair[")
        .and_then(|s| s.strip_suffix(']'))
    {
        (HowzatDdCheckKind::Repair, inner)
    } else {
        return Ok(None);
    };

    let Some(target) = parse_howzat_dd_num(inner) else {
        return Err(format!(
            "unknown {} target '{inner}'",
            kind.canonical_token()
        ));
    };

    if !matches!(target, HowzatDdNum::RugRat | HowzatDdNum::DashuRat) {
        return Err(format!(
            "{} currently only supports targets '{}' and '{}' (got '{}')",
            kind.canonical_token(),
            HowzatDdNum::RugRat.canonical_token(),
            HowzatDdNum::DashuRat.canonical_token(),
            target.canonical_token()
        ));
    }

    Ok(Some(HowzatDdCheck { kind, target }))
}

fn parse_howzat_dd_pipeline(raw: &str) -> Result<HowzatDdPipelineSpec, String> {
    let raw = raw.trim();
    if raw.is_empty() {
        return Err("howzat-dd pipeline cannot be empty".to_string());
    }

    let parts: Vec<&str> = {
        let mut parts = Vec::new();
        let mut depth = 0usize;
        let mut start = 0usize;
        for (idx, ch) in raw.char_indices() {
            match ch {
                '[' => depth += 1,
                ']' => {
                    depth = depth
                        .checked_sub(1)
                        .ok_or_else(|| "howzat-dd pipeline contains unmatched ']'".to_string())?;
                }
                '-' if depth == 0 => {
                    parts.push(raw[start..idx].trim());
                    start = idx + ch.len_utf8();
                }
                _ => {}
            }
        }
        if depth != 0 {
            return Err("howzat-dd pipeline contains unmatched '['".to_string());
        }
        parts.push(raw[start..].trim());
        parts
    };

    let mut steps: Vec<HowzatDdStep> = Vec::new();
    for token in parts {
        if token.is_empty() {
            return Err("howzat-dd pipeline cannot contain empty tokens".to_string());
        }
        if let Some(check) = parse_howzat_dd_check(token)? {
            steps.push(HowzatDdStep::Check(check));
            continue;
        }
        if let Some(compute) = parse_howzat_dd_compute(token)? {
            steps.push(HowzatDdStep::Compute(compute));
            continue;
        }
        return Err(format!("unknown howzat-dd pipeline token '{token}'"));
    }

    let Some(first) = steps.first().copied() else {
        return Err("howzat-dd pipeline cannot be empty".to_string());
    };
    if !matches!(first, HowzatDdStep::Compute(_)) {
        return Err("howzat-dd pipeline must start with a numeric stage (e.g. f64)".to_string());
    }
    for pair in steps.windows(2) {
        let [a, b] = pair else { continue };
        if matches!(a, HowzatDdStep::Compute(_)) && matches!(b, HowzatDdStep::Compute(_)) {
            return Err(format!(
                "howzat-dd pipeline cannot have consecutive numeric stages ('{}-{}'); \
insert resolve[...] or repair[...] between them",
                a.canonical_token(),
                b.canonical_token()
            ));
        }
    }

    let mut last_compute: Option<HowzatDdNum> = None;
    for step in steps.iter().copied() {
        match step {
            HowzatDdStep::Compute(compute) => last_compute = Some(compute.num),
            HowzatDdStep::Check(check) => {
                let Some(prev) = last_compute else {
                    return Err("howzat-dd pipeline check must follow a numeric stage".to_string());
                };
                if !howzat_dd_can_coerce(prev, check.target) {
                    return Err(format!(
                        "{} after {} is not supported (no {} -> {} coercion available)",
                        check.canonical_token(),
                        prev.canonical_token(),
                        prev.canonical_token(),
                        check.target.canonical_token()
                    ));
                }
            }
        }
    }

    Ok(HowzatDdPipelineSpec { steps })
}

fn howzat_dd_can_coerce(from: HowzatDdNum, to: HowzatDdNum) -> bool {
    use HowzatDdNum::*;
    matches!(
        (from, to),
        (F64, _)
            | (RugFloat128, F64 | RugFloat128 | RugRat)
            | (RugFloat256, F64 | RugFloat256 | RugRat)
            | (RugFloat512, F64 | RugFloat512 | RugRat)
            | (DashuFloat128, F64 | DashuFloat128 | DashuRat)
            | (DashuFloat256, F64 | DashuFloat256 | DashuRat)
            | (DashuFloat512, F64 | DashuFloat512 | DashuRat)
            | (RugRat, F64 | RugRat)
            | (DashuRat, F64 | DashuRat)
    )
}

#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
enum BackendSpec {
    CddlibF64,
    CddlibGmpFloat,
    CddlibGmpRational,
    CddlibHlblF64,
    CddlibHlblGmpFloat,
    CddlibHlblGmpRational,
    HowzatDd {
        purifier: Option<HowzatDdPurifierSpec>,
        pipeline: HowzatDdPipelineSpec,
    },
    HowzatLrsRug,
    HowzatLrsDashu,
    LrslibHlblGmpInt,
}

impl BackendSpec {
    fn is_cddlib(&self) -> bool {
        matches!(
            self,
            Self::CddlibF64
                | Self::CddlibGmpFloat
                | Self::CddlibGmpRational
                | Self::CddlibHlblF64
                | Self::CddlibHlblGmpFloat
                | Self::CddlibHlblGmpRational
        )
    }

    fn is_howzat_dd(&self) -> bool {
        matches!(self, Self::HowzatDd { .. })
    }

    fn is_howzat_lrs(&self) -> bool {
        matches!(self, Self::HowzatLrsRug | Self::HowzatLrsDashu)
    }
}

impl fmt::Display for BackendSpec {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::CddlibF64 => f.write_str("cddlib:f64"),
            Self::CddlibGmpFloat => f.write_str("cddlib:gmpfloat"),
            Self::CddlibGmpRational => f.write_str("cddlib:gmprational"),
            Self::CddlibHlblF64 => f.write_str("cddlib+hlbl:f64"),
            Self::CddlibHlblGmpFloat => f.write_str("cddlib+hlbl:gmpfloat"),
            Self::CddlibHlblGmpRational => f.write_str("cddlib+hlbl:gmprational"),
            Self::HowzatDd { purifier, pipeline } => {
                let Some(purifier) = purifier else {
                    return write!(f, "howzat-dd:{}", pipeline.canonical());
                };
                write!(
                    f,
                    "{}@howzat-dd:{}",
                    purifier.canonical_token(),
                    pipeline.canonical()
                )
            }
            Self::HowzatLrsRug => f.write_str("howzat-lrs:rug"),
            Self::HowzatLrsDashu => f.write_str("howzat-lrs:dashu"),
            Self::LrslibHlblGmpInt => f.write_str("lrslib+hlbl:gmpint"),
        }
    }
}

impl std::str::FromStr for BackendSpec {
    type Err = String;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let raw = value.trim();
        if raw.is_empty() {
            return Err("backend spec cannot be empty".to_string());
        }

        let raw = raw.to_ascii_lowercase();
        let (purifier, raw) = raw
            .split_once('@')
            .map(|(p, rest)| (Some(p.trim()), rest.trim()))
            .unwrap_or((None, raw.trim()));
        if raw.is_empty() {
            return Err("backend spec cannot be empty".to_string());
        }
        if raw.contains('@') {
            return Err(format!(
                "backend spec '{value}' contains multiple '@' separators"
            ));
        }
        let purifier = purifier.map(parse_howzat_dd_purifier).transpose()?;

        let (kind, num) = raw
            .split_once(':')
            .map(|(k, n)| (k.trim(), Some(n.trim())))
            .unwrap_or((raw.trim(), None));
        if purifier.is_some() && kind != "howzat-dd" {
            return Err(format!(
                "purifier prefix is only supported for howzat-dd backends (got '{value}')"
            ));
        }

        let spec = match (kind, num) {
            ("cddlib", None | Some("") | Some("gmprational")) => Self::CddlibGmpRational,
            ("cddlib", Some("f64")) => Self::CddlibF64,
            ("cddlib", Some("gmpfloat")) => Self::CddlibGmpFloat,
            ("cddlib+hlbl", None | Some("") | Some("gmprational")) => Self::CddlibHlblGmpRational,
            ("cddlib+hlbl", Some("f64")) => Self::CddlibHlblF64,
            ("cddlib+hlbl", Some("gmpfloat")) => Self::CddlibHlblGmpFloat,
            ("howzat-dd", None | Some("")) => Self::HowzatDd {
                purifier,
                pipeline: parse_howzat_dd_pipeline(DEFAULT_HOWZAT_DD_PIPELINE)?,
            },
            ("howzat-dd", Some(spec)) => Self::HowzatDd {
                purifier,
                pipeline: parse_howzat_dd_pipeline(spec)?,
            },
            ("howzat-lrs", None | Some("") | Some("rug")) => Self::HowzatLrsRug,
            ("howzat-lrs", Some("dashu")) => Self::HowzatLrsDashu,
            ("lrslib+hlbl", None | Some("") | Some("gmpint")) => Self::LrslibHlblGmpInt,
            _ => {
                return Err(format!(
                    "unknown backend spec '{value}' (see --help for supported values)"
                ));
            }
        };

        Ok(spec)
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
pub struct Backend(BackendSpec);

impl Backend {
    pub fn parse(spec: &str) -> Result<Self, String> {
        spec.parse()
    }

    pub fn is_cddlib(&self) -> bool {
        self.0.is_cddlib()
    }

    pub fn is_howzat_dd(&self) -> bool {
        self.0.is_howzat_dd()
    }

    pub fn is_howzat_lrs(&self) -> bool {
        self.0.is_howzat_lrs()
    }

    pub fn solve(
        &self,
        vertices: &[Vec<f64>],
        config: &BackendRunConfig,
    ) -> Result<BackendRun, anyhow::Error> {
        let vertices = VerticesVecVec::new(vertices);
        self.solve_impl(&vertices, config)
    }

    pub fn solve_row_major(
        &self,
        coords: &[f64],
        vertex_count: usize,
        dim: usize,
        config: &BackendRunConfig,
    ) -> Result<BackendRun, anyhow::Error> {
        let vertices = VerticesRowMajor::new(coords, vertex_count, dim)?;
        self.solve_impl(&vertices, config)
    }

    fn solve_impl<V: VerticesF64>(
        &self,
        vertices: &V,
        config: &BackendRunConfig,
    ) -> Result<BackendRun, anyhow::Error> {
        let start_run = Instant::now();
        let timing = config.timing_detail;

        let run = match &self.0 {
            BackendSpec::CddlibF64 => run_cddlib_backend::<f64, V, _>(
                self.clone(),
                vertices,
                |v| crate::polytope::cddlib::build_polyhedron_f64_vertices(v),
                false,
                timing,
            ),
            BackendSpec::CddlibGmpFloat => run_cddlib_backend::<cddlib_rs::CddFloat, V, _>(
                self.clone(),
                vertices,
                |v| crate::polytope::cddlib::build_polyhedron_gmp_vertices(v),
                false,
                timing,
            ),
            BackendSpec::CddlibGmpRational => run_cddlib_backend::<cddlib_rs::CddRational, V, _>(
                self.clone(),
                vertices,
                |v| crate::polytope::cddlib::build_polyhedron_rational_vertices(v),
                false,
                timing,
            ),
            BackendSpec::CddlibHlblF64 => run_cddlib_backend::<f64, V, _>(
                self.clone(),
                vertices,
                |v| crate::polytope::cddlib::build_polyhedron_f64_vertices(v),
                true,
                timing,
            ),
            BackendSpec::CddlibHlblGmpFloat => run_cddlib_backend::<cddlib_rs::CddFloat, V, _>(
                self.clone(),
                vertices,
                |v| crate::polytope::cddlib::build_polyhedron_gmp_vertices(v),
                true,
                timing,
            ),
            BackendSpec::CddlibHlblGmpRational => run_cddlib_backend::<cddlib_rs::CddRational, V, _>(
                self.clone(),
                vertices,
                |v| crate::polytope::cddlib::build_polyhedron_rational_vertices(v),
                true,
                timing,
            ),
            BackendSpec::HowzatDd { purifier, pipeline } => run_howzat_dd_backend(
                self.clone(),
                *purifier,
                pipeline,
                config.howzat_output_adjacency,
                vertices,
                &config.howzat_options,
                timing,
            ),
            BackendSpec::HowzatLrsRug | BackendSpec::HowzatLrsDashu => {
                run_howzat_lrs_backend(self.clone(), vertices, timing)
            }
            BackendSpec::LrslibHlblGmpInt => {
                if let Some(vertices) = vertices.as_vecvec() {
                    run_lrslib_hlbl_backend(self.clone(), vertices, timing)
                } else {
                    let vertices = vertices.rows().map(|row| row.to_vec()).collect::<Vec<_>>();
                    run_lrslib_hlbl_backend(self.clone(), &vertices, timing)
                }
            }
        };

        match run {
            Ok(run) => Ok(run),
            Err(err) => {
                if self.is_cddlib()
                    && is_cddlib_error_code(&err, cddlib_rs::CddErrorCode::NumericallyInconsistent)
                {
                    Ok(backend_error_run(
                        self.clone(),
                        vertices.dim(),
                        vertices.vertex_count(),
                        start_run.elapsed(),
                        err.to_string(),
                    ))
                } else {
                    Err(err)
                }
            }
        }
    }
}

impl fmt::Display for Backend {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(f)
    }
}

impl std::str::FromStr for Backend {
    type Err = String;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let spec: BackendSpec = value.parse()?;
        Ok(Self(spec))
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BackendArg {
    pub spec: Backend,
    pub authoritative: bool,
    pub perf_baseline: bool,
}

impl std::str::FromStr for BackendArg {
    type Err = String;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let raw = value.trim();
        if raw.is_empty() {
            return Err("backend spec cannot be empty".to_string());
        }

        let mut authoritative = false;
        let mut perf_baseline = false;
        let mut rest = raw;

        loop {
            let Some(prefix) = rest.chars().next() else {
                break;
            };
            match prefix {
                '^' => {
                    if authoritative {
                        return Err(format!(
                            "backend spec '{value}' contains multiple '^' prefixes"
                        ));
                    }
                    authoritative = true;
                    rest = &rest['^'.len_utf8()..];
                }
                '%' => {
                    if perf_baseline {
                        return Err(format!(
                            "backend spec '{value}' contains multiple '%' prefixes"
                        ));
                    }
                    perf_baseline = true;
                    rest = &rest['%'.len_utf8()..];
                }
                _ => break,
            }
        }

        let spec: Backend = rest.trim().parse()?;
        Ok(Self {
            spec,
            authoritative,
            perf_baseline,
        })
    }
}

#[derive(Clone, Debug)]
pub struct BackendRunConfig {
    pub howzat_options: ConeOptions,
    pub howzat_output_adjacency: AdjacencyOutput,
    pub timing_detail: bool,
}

impl Default for BackendRunConfig {
    fn default() -> Self {
        Self {
            howzat_options: ConeOptions::default(),
            howzat_output_adjacency: AdjacencyOutput::List,
            timing_detail: false,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Stats {
    pub dimension: usize,
    pub vertices: usize,
    pub facets: usize,
    pub ridges: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackendTiming {
    pub total: Duration,
    pub fast: Option<Duration>,
    pub resolve: Option<Duration>,
    pub exact: Option<Duration>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct CddlibTimingDetail {
    pub build: Duration,
    pub incidence: Duration,
    pub vertex_adjacency: Duration,
    pub facet_adjacency: Duration,
    pub vertex_positions: Duration,
    pub post_inc: Duration,
    pub post_v_adj: Duration,
    pub post_f_adj: Duration,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct HowzatDdTimingDetail {
    pub fast_matrix: Duration,
    pub fast_dd: Duration,
    pub cert: Duration,
    pub repair_partial: Duration,
    pub repair_graph: Duration,
    pub exact_matrix: Duration,
    pub exact_dd: Duration,
    pub incidence: Duration,
    pub vertex_adjacency: Duration,
    pub facet_adjacency: Duration,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct HowzatLrsTimingDetail {
    pub matrix: Duration,
    pub lrs: Duration,
    pub cert: Duration,
    pub incidence: Duration,
    pub vertex_adjacency: Duration,
    pub facet_adjacency: Duration,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct LrslibTimingDetail {
    pub build: Duration,
    pub incidence: Duration,
    pub vertex_adjacency: Duration,
    pub facet_adjacency: Duration,
    pub post_inc: Duration,
    pub post_v_adj: Duration,
    pub post_f_adj: Duration,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TimingDetail {
    Cddlib(CddlibTimingDetail),
    HowzatDd(HowzatDdTimingDetail),
    HowzatLrs(HowzatLrsTimingDetail),
    Lrslib(LrslibTimingDetail),
}

#[derive(Debug, Clone)]
pub struct BackendRun {
    pub spec: Backend,
    pub stats: Stats,
    pub timing: BackendTiming,
    pub geometry: BackendGeometry,
    pub fails: usize,
    pub fallbacks: usize,
    pub error: Option<String>,
    pub detail: Option<TimingDetail>,
}

#[derive(Debug, Clone)]
pub enum BackendGeometry {
    Baseline(BaselineGeometry),
    Input(InputGeometry),
}

#[derive(Debug, Clone)]
pub struct BaselineGeometry {
    pub vertex_positions: Vec<Vec<f64>>,
    pub vertex_adjacency: Vec<RowSet>,
    pub facets_to_vertices: Vec<RowSet>,
    pub facet_adjacency: Vec<RowSet>,
}

#[derive(Debug, Clone)]
pub struct InputGeometry {
    pub vertex_adjacency: Vec<RowSet>,
    pub facets_to_vertices: Vec<RowSet>,
    pub facet_adjacency: Vec<RowSet>,
}

fn run_cddlib_backend<N, V, B>(
    spec: Backend,
    vertices: &V,
    build: B,
    use_hull_facet_graph: bool,
    timing: bool,
) -> Result<BackendRun, anyhow::Error>
where
    N: cddlib_rs::CddNumber,
    V: VerticesF64,
    B: FnOnce(&V) -> Result<cddlib_rs::Polyhedron<N>, anyhow::Error>,
{
    // Measure the full pipeline: build polytope + incidence + vertex graph + facet (ridge) graph.
    let start_total = Instant::now();

    let start = Instant::now();
    let poly = build(vertices)?;
    let facets = poly.facets()?;
    let generators = poly.generators()?;

    let dim = facets.cols().saturating_sub(1);
    let num_facets = facets.rows();
    let time_build = start.elapsed();

    let start = Instant::now();
    let incidence = poly.incidence()?.to_adjacency_lists();
    let time_incidence = start.elapsed();

    let start = Instant::now();
    let vertex_graph = poly.input_adjacency()?.to_adjacency_lists();
    let time_vertex_graph = start.elapsed();

    let start = Instant::now();
    let facet_graph = if use_hull_facet_graph {
        hullabaloo::adjacency::adjacency_from_incidence(
            &incidence,
            vertices.vertex_count(),
            facets.cols(),
            hullabaloo::adjacency::IncidenceAdjacencyOptions::default(),
        )
        .adjacency
    } else {
        poly.adjacency()?.to_adjacency_lists()
    };
    let time_facet_graph = start.elapsed();

    let start = Instant::now();
    let vertex_positions = crate::polytope::cddlib::vertex_positions_from_generators(&generators)?;
    let time_vertex_positions = start.elapsed();

    let ridges = facet_graph.iter().map(|n| n.len()).sum::<usize>() / 2;
    let stats = Stats {
        dimension: dim,
        vertices: vertex_positions.len(),
        facets: num_facets,
        ridges,
    };

    let start = timing.then(Instant::now);
    let facets_to_vertices = incidence
        .iter()
        .map(|verts| rowset_from_list(vertex_positions.len(), verts))
        .collect::<Vec<_>>();
    let time_post_inc = start.map_or(Duration::ZERO, |start| start.elapsed());

    let start = timing.then(Instant::now);
    let vertex_adjacency = rowsets_from_adjacency_lists(&vertex_graph, vertex_positions.len());
    let time_post_v_adj = start.map_or(Duration::ZERO, |start| start.elapsed());

    let start = timing.then(Instant::now);
    let facet_adjacency = rowsets_from_adjacency_lists(&facet_graph, facets_to_vertices.len());
    let time_post_f_adj = start.map_or(Duration::ZERO, |start| start.elapsed());

    let duration = start_total.elapsed();
    let detail = timing.then(|| {
        TimingDetail::Cddlib(CddlibTimingDetail {
            build: time_build,
            incidence: time_incidence,
            vertex_adjacency: time_vertex_graph,
            facet_adjacency: time_facet_graph,
            vertex_positions: time_vertex_positions,
            post_inc: time_post_inc,
            post_v_adj: time_post_v_adj,
            post_f_adj: time_post_f_adj,
        })
    });

    Ok(BackendRun {
        spec,
        stats,
        timing: BackendTiming {
            total: duration,
            fast: None,
            resolve: None,
            exact: None,
        },
        geometry: BackendGeometry::Baseline(BaselineGeometry {
            vertex_positions,
            vertex_adjacency,
            facets_to_vertices,
            facet_adjacency,
        }),
        fails: 0,
        fallbacks: 0,
        error: None,
        detail,
    })
}

fn run_howzat_dd_backend<V: VerticesF64>(
    spec: Backend,
    purifier: Option<HowzatDdPurifierSpec>,
    pipeline: &HowzatDdPipelineSpec,
    output_adjacency: AdjacencyOutput,
    vertices: &V,
    howzat_options: &ConeOptions,
    timing: bool,
) -> Result<BackendRun, anyhow::Error> {
    type HowzatRepr = hullabaloo::types::Generator;
    type Poly<N> = howzat::polyhedron::PolyhedronOutput<N, HowzatRepr>;
    type HowzatMatrix<N> = howzat::matrix::LpMatrix<N, HowzatRepr>;

    fn default_norm<N: DefaultNormalizer>() -> <N as DefaultNormalizer>::Norm {
        <N as DefaultNormalizer>::Norm::default()
    }

    fn dd_poly<N: Num, U: howzat::dd::Umpire<N, HowzatRepr>>(
        matrix: HowzatMatrix<N>,
        cone_options: &ConeOptions,
        poly_options: howzat::polyhedron::PolyhedronOptions,
        umpire: U,
    ) -> Result<Poly<N>, howzat::Error> {
        Poly::<N>::from_matrix_dd_with_options(matrix, cone_options.clone(), poly_options, umpire)
    }

    #[derive(Clone, Debug)]
    enum PolyAny {
        F64(Poly<f64>),
        RugFloat128(Poly<RugFloat<128>>),
        RugFloat256(Poly<RugFloat<256>>),
        RugFloat512(Poly<RugFloat<512>>),
        DashuFloat128(Poly<DashuFloat<128>>),
        DashuFloat256(Poly<DashuFloat<256>>),
        DashuFloat512(Poly<DashuFloat<512>>),
        RugRat(Poly<RugRat>),
        DashuRat(Poly<DashuRat>),
    }

    struct ComputeStageArgs<'a, Vtx: VerticesF64> {
        vertices: &'a Vtx,
        howzat_options: &'a ConeOptions,
        poly_options: howzat::polyhedron::PolyhedronOptions,
        spec_label: &'a str,
    }

    fn compute_dd<N: Num, E: Epsilon<N>, NM: Normalizer<N>, Vtx: VerticesF64>(
        args: ComputeStageArgs<'_, Vtx>,
        stage: HowzatDdCompute,
        wrap: fn(Poly<N>) -> PolyAny,
        eps: E,
        normalizer: NM,
        purifier: Option<HowzatDdPurifierSpec>,
    ) -> Result<(PolyAny, Duration, Duration), anyhow::Error> {
        let ComputeStageArgs {
            vertices,
            howzat_options,
            poly_options,
            spec_label,
        } = args;

        let start_matrix = Instant::now();
        let matrix = build_generator_matrix_vertices::<N, _>(vertices)?;
        let time_matrix = start_matrix.elapsed();

        let start_dd = Instant::now();
        let poly = match purifier {
            Some(HowzatDdPurifierSpec::Snap) => {
                let umpire = SpUmpire::with_purifier(eps, normalizer, Snap::default());
                dd_poly(matrix, howzat_options, poly_options, umpire)
            }
            None | Some(HowzatDdPurifierSpec::UpSnap(_)) => {
                let umpire = SpUmpire::with_normalizer(eps, normalizer);
                dd_poly(matrix, howzat_options, poly_options, umpire)
            }
        }
        .map_err(|e| anyhow!("{spec_label} dd({}) failed: {e:?}", stage.canonical_token()))?;
        let time_dd = start_dd.elapsed();

        Ok((wrap(poly), time_matrix, time_dd))
    }

    fn compute_poly_any<Vtx: VerticesF64>(
        stage: HowzatDdCompute,
        purifier: Option<HowzatDdPurifierSpec>,
        vertices: &Vtx,
        howzat_options: &ConeOptions,
        poly_options: howzat::polyhedron::PolyhedronOptions,
        spec_label: &str,
    ) -> Result<(PolyAny, Duration, Duration), anyhow::Error> {
        use HowzatDdNormalizer::{Gcd, Max, Min, No};
        use HowzatDdNum::{
            DashuFloat128, DashuFloat256, DashuFloat512, F64, RugFloat128, RugFloat256, RugFloat512,
        };

        let args = ComputeStageArgs {
            vertices,
            howzat_options,
            poly_options,
            spec_label,
        };

        fn compute_as_num<N: Num + DefaultNormalizer, Vtx: VerticesF64>(
            args: ComputeStageArgs<'_, Vtx>,
            stage: HowzatDdCompute,
            wrap: fn(Poly<N>) -> PolyAny,
            purifier: Option<HowzatDdPurifierSpec>,
        ) -> Result<(PolyAny, Duration, Duration), anyhow::Error> {
            match stage.normalizer {
                None => compute_dd(args, stage, wrap, N::default_eps(), default_norm::<N>(), purifier),
                Some(No) => compute_dd(args, stage, wrap, N::default_eps(), NoNormalizer, purifier),
                Some(Min) => compute_dd(args, stage, wrap, N::default_eps(), MinNormalizer, purifier),
                Some(Max) => compute_dd(args, stage, wrap, N::default_eps(), MaxNormalizer, purifier),
                Some(Gcd) => Err(anyhow!(
                    "internal: gcd normalizer requested for non-rational type {}",
                    stage.num.canonical_token()
                )),
            }
        }

        fn compute_as_rat<N: Rat + DefaultNormalizer, Vtx: VerticesF64>(
            args: ComputeStageArgs<'_, Vtx>,
            stage: HowzatDdCompute,
            wrap: fn(Poly<N>) -> PolyAny,
            purifier: Option<HowzatDdPurifierSpec>,
        ) -> Result<(PolyAny, Duration, Duration), anyhow::Error> {
            match stage.normalizer {
                None => compute_dd(args, stage, wrap, N::default_eps(), default_norm::<N>(), purifier),
                Some(No) => compute_dd(args, stage, wrap, N::default_eps(), NoNormalizer, purifier),
                Some(Min) => compute_dd(args, stage, wrap, N::default_eps(), MinNormalizer, purifier),
                Some(Max) => compute_dd(args, stage, wrap, N::default_eps(), MaxNormalizer, purifier),
                Some(Gcd) => compute_dd(
                    args,
                    stage,
                    wrap,
                    N::default_eps(),
                    GcdNormalizer::default(),
                    purifier,
                ),
            }
        }

        match stage.num {
            F64 => {
                fn compute_f64_upsnap<M: Num, E: Epsilon<f64>, Vtx: VerticesF64>(
                    args: ComputeStageArgs<'_, Vtx>,
                    stage: HowzatDdCompute,
                    eps: E,
                    normalizer: impl Normalizer<f64>,
                ) -> Result<(PolyAny, Duration, Duration), anyhow::Error>
                where
                    M: CoerceFrom<f64>,
                    f64: CoerceFrom<M>,
                {
                    let ComputeStageArgs {
                        vertices,
                        howzat_options,
                        poly_options,
                        spec_label,
                    } = args;

                    let start_matrix = Instant::now();
                    let matrix = build_generator_matrix_vertices::<f64, _>(vertices)?;
                    let time_matrix = start_matrix.elapsed();

                    let purifier = UpcastingSnapPurifier::<M, _>::new(M::default_eps());
                    let umpire = SpUmpire::with_purifier(eps, normalizer, purifier);

                    let start_dd = Instant::now();
                    let poly = dd_poly(matrix, howzat_options, poly_options, umpire).map_err(|e| {
                        anyhow!(
                            "{spec_label} dd({}) failed: {e:?}",
                            stage.canonical_token()
                        )
                    })?;
                    let time_dd = start_dd.elapsed();

                    Ok((PolyAny::F64(poly), time_matrix, time_dd))
                }

                fn compute_f64_upsnap_any<E: Epsilon<f64>, Vtx: VerticesF64>(
                    args: ComputeStageArgs<'_, Vtx>,
                    stage: HowzatDdCompute,
                    target: HowzatDdNum,
                    eps: E,
                    normalizer: impl Normalizer<f64>,
                ) -> Result<(PolyAny, Duration, Duration), anyhow::Error> {
                    match target {
                        HowzatDdNum::RugRat => {
                            compute_f64_upsnap::<RugRat, _, _>(args, stage, eps, normalizer)
                        }
                        HowzatDdNum::DashuRat => {
                            compute_f64_upsnap::<DashuRat, _, _>(args, stage, eps, normalizer)
                        }
                        _ => Err(anyhow!(
                            "internal: upsnap target must be rugrat or dashurat (got {})",
                            target.canonical_token()
                        )),
                    }
                }

                fn compute_f64_eps<E: Epsilon<f64>, Vtx: VerticesF64>(
                    args: ComputeStageArgs<'_, Vtx>,
                    stage: HowzatDdCompute,
                    purifier: Option<HowzatDdPurifierSpec>,
                    eps: E,
                ) -> Result<(PolyAny, Duration, Duration), anyhow::Error> {
                    use HowzatDdNormalizer::{Gcd, Max, Min, No};

                    let Some(HowzatDdPurifierSpec::UpSnap(target)) = purifier else {
                        return match stage.normalizer {
                            None => compute_dd(args, stage, PolyAny::F64, eps, default_norm::<f64>(), purifier),
                            Some(No) => compute_dd(args, stage, PolyAny::F64, eps, NoNormalizer, purifier),
                            Some(Min) => compute_dd(args, stage, PolyAny::F64, eps, MinNormalizer, purifier),
                            Some(Max) => compute_dd(args, stage, PolyAny::F64, eps, MaxNormalizer, purifier),
                            Some(Gcd) => Err(anyhow!(
                                "internal: gcd normalizer requested for non-rational type {}",
                                stage.num.canonical_token()
                            )),
                        };
                    };

                    match stage.normalizer {
                        None => compute_f64_upsnap_any(args, stage, target, eps, default_norm::<f64>()),
                        Some(No) => compute_f64_upsnap_any(args, stage, target, eps, NoNormalizer),
                        Some(Min) => compute_f64_upsnap_any(args, stage, target, eps, MinNormalizer),
                        Some(Max) => compute_f64_upsnap_any(args, stage, target, eps, MaxNormalizer),
                        Some(Gcd) => Err(anyhow!(
                            "internal: gcd normalizer requested for non-rational type {}",
                            stage.num.canonical_token()
                        )),
                    }
                }

                match stage.f64_eps {
                    None => compute_f64_eps(args, stage, purifier, f64::default_eps()),
                    Some(HowzatDdF64Eps::BuiltinEm7) => compute_f64_eps(args, stage, purifier, F64Em7Epsilon),
                    Some(HowzatDdF64Eps::BuiltinEm9) => compute_f64_eps(args, stage, purifier, F64Em9Epsilon),
                    Some(HowzatDdF64Eps::BuiltinEm12) => compute_f64_eps(args, stage, purifier, F64Em12Epsilon),
                    Some(HowzatDdF64Eps::Dynamic(bits)) => compute_f64_eps(
                        args,
                        stage,
                        purifier,
                        DynamicEpsilon::new(f64::from_bits(bits)),
                    ),
                }
            }
            RugFloat128 => compute_as_num::<RugFloat<128>, _>(args, stage, PolyAny::RugFloat128, purifier),
            RugFloat256 => compute_as_num::<RugFloat<256>, _>(args, stage, PolyAny::RugFloat256, purifier),
            RugFloat512 => compute_as_num::<RugFloat<512>, _>(args, stage, PolyAny::RugFloat512, purifier),
            DashuFloat128 => {
                compute_as_num::<DashuFloat<128>, _>(args, stage, PolyAny::DashuFloat128, purifier)
            }
            DashuFloat256 => {
                compute_as_num::<DashuFloat<256>, _>(args, stage, PolyAny::DashuFloat256, purifier)
            }
            DashuFloat512 => {
                compute_as_num::<DashuFloat<512>, _>(args, stage, PolyAny::DashuFloat512, purifier)
            }
            HowzatDdNum::RugRat => compute_as_rat::<RugRat, _>(args, stage, PolyAny::RugRat, purifier),
            HowzatDdNum::DashuRat => {
                compute_as_rat::<DashuRat, _>(args, stage, PolyAny::DashuRat, purifier)
            }
        }
    }

    fn try_resolve_to_rat<Src, Dst>(
        poly: &Poly<Src>,
        poly_options: &howzat::polyhedron::PolyhedronOptions,
        wrap: fn(Poly<Dst>) -> PolyAny,
    ) -> Option<PolyAny>
    where
        Src: Num,
        Dst: Rat + CoerceFrom<Src>,
        <Dst as Rat>::Int: std::ops::SubAssign<<Dst as Rat>::Int>,
        for<'a> <Dst as Rat>::Int: std::ops::AddAssign<&'a <Dst as Rat>::Int>,
    {
        let eps = Dst::default_eps();
        resolve_howzat_certificate_as::<Src, Dst>(poly, poly_options, &eps).map(wrap)
    }

    fn resolve_any(
        inexact: &PolyAny,
        target: HowzatDdNum,
        poly_options: &howzat::polyhedron::PolyhedronOptions,
    ) -> Option<PolyAny> {
        use PolyAny::*;

        match target {
            HowzatDdNum::RugRat => {
                let wrap = PolyAny::RugRat;
                match inexact {
                    F64(poly) => try_resolve_to_rat(poly, poly_options, wrap),
                    RugFloat128(poly) => try_resolve_to_rat(poly, poly_options, wrap),
                    RugFloat256(poly) => try_resolve_to_rat(poly, poly_options, wrap),
                    RugFloat512(poly) => try_resolve_to_rat(poly, poly_options, wrap),
                    RugRat(poly) => Some(RugRat(poly.clone())),
                    _ => None,
                }
            }
            HowzatDdNum::DashuRat => {
                let wrap = PolyAny::DashuRat;
                match inexact {
                    F64(poly) => try_resolve_to_rat(poly, poly_options, wrap),
                    DashuFloat128(poly) => try_resolve_to_rat(poly, poly_options, wrap),
                    DashuFloat256(poly) => try_resolve_to_rat(poly, poly_options, wrap),
                    DashuFloat512(poly) => try_resolve_to_rat(poly, poly_options, wrap),
                    DashuRat(poly) => Some(DashuRat(poly.clone())),
                    _ => None,
                }
            }
            _ => None,
        }
    }

    fn try_repair_to_rat<Src, Dst>(
        poly: &Poly<Src>,
        poly_options: &howzat::polyhedron::PolyhedronOptions,
        wrap: fn(Poly<Dst>) -> PolyAny,
    ) -> Option<(PolyAny, bool, Duration, Duration, Duration)>
    where
        Src: Num,
        Dst: Rat + CoerceFrom<Src>,
        <Dst as Rat>::Int: std::ops::SubAssign<<Dst as Rat>::Int>,
        for<'a> <Dst as Rat>::Int: std::ops::AddAssign<&'a <Dst as Rat>::Int>,
    {
        let eps = Dst::default_eps();
        repair_howzat_facet_graph_as::<Dst, Src>(poly, poly_options, &eps)
            .ok()
            .map(|(poly, report, cert, partial, repair)| {
                let frontier_ok = report
                    .frontier
                    .as_ref()
                    .map(|r| r.remaining_frontier_ridges() == 0 && !r.step_limit_reached())
                    .unwrap_or(true);

                (
                    wrap(poly),
                    report.unresolved_nodes == 0 && frontier_ok,
                    cert,
                    partial,
                    repair,
                )
            })
    }

    fn repair_any(
        inexact: &PolyAny,
        target: HowzatDdNum,
        poly_options: &howzat::polyhedron::PolyhedronOptions,
    ) -> Option<(PolyAny, bool, Duration, Duration, Duration)> {
        use PolyAny::*;

        match target {
            HowzatDdNum::RugRat => match inexact {
                F64(poly) => try_repair_to_rat(poly, poly_options, PolyAny::RugRat),
                RugFloat128(poly) => try_repair_to_rat(poly, poly_options, PolyAny::RugRat),
                RugFloat256(poly) => try_repair_to_rat(poly, poly_options, PolyAny::RugRat),
                RugFloat512(poly) => try_repair_to_rat(poly, poly_options, PolyAny::RugRat),
                RugRat(poly) => Some((
                    RugRat(poly.clone()),
                    true,
                    Duration::ZERO,
                    Duration::ZERO,
                    Duration::ZERO,
                )),
                _ => None,
            },
            HowzatDdNum::DashuRat => match inexact {
                F64(poly) => try_repair_to_rat(poly, poly_options, PolyAny::DashuRat),
                DashuFloat128(poly) => try_repair_to_rat(poly, poly_options, PolyAny::DashuRat),
                DashuFloat256(poly) => try_repair_to_rat(poly, poly_options, PolyAny::DashuRat),
                DashuFloat512(poly) => try_repair_to_rat(poly, poly_options, PolyAny::DashuRat),
                DashuRat(poly) => Some((
                    DashuRat(poly.clone()),
                    true,
                    Duration::ZERO,
                    Duration::ZERO,
                    Duration::ZERO,
                )),
                _ => None,
            },
            _ => None,
        }
    }

    let poly_options_final = howzat::polyhedron::PolyhedronOptions {
        output_incidence: IncidenceOutput::Set,
        output_adjacency,
        input_incidence: IncidenceOutput::Off,
        input_adjacency: AdjacencyOutput::Off,
        save_basis_and_tableau: false,
        save_repair_hints: false,
        profile_adjacency: false,
    };

    let poly_options_inexact_repair = howzat::polyhedron::PolyhedronOptions {
        output_incidence: IncidenceOutput::Set,
        output_adjacency,
        input_incidence: IncidenceOutput::Off,
        input_adjacency: AdjacencyOutput::Off,
        save_basis_and_tableau: false,
        save_repair_hints: true,
        profile_adjacency: false,
    };

    let poly_options_cert = howzat::polyhedron::PolyhedronOptions {
        output_incidence: IncidenceOutput::Set,
        output_adjacency: AdjacencyOutput::Off,
        input_incidence: IncidenceOutput::Off,
        input_adjacency: AdjacencyOutput::Off,
        save_basis_and_tableau: false,
        save_repair_hints: false,
        profile_adjacency: false,
    };

    let spec_label = spec.to_string();

    let start_total = Instant::now();

    let mut time_fast_matrix = Duration::ZERO;
    let mut time_fast_dd = Duration::ZERO;
    let mut time_cert = Duration::ZERO;
    let mut time_repair_partial = Duration::ZERO;
    let mut time_repair_graph = Duration::ZERO;
    let mut time_exact_matrix = Duration::ZERO;
    let mut time_exact_dd = Duration::ZERO;

    let mut executed_computes = 0usize;
    let mut fails = 0usize;

    let mut current: Option<PolyAny> = None;
    for (idx, step) in pipeline.steps.iter().copied().enumerate() {
        match step {
            HowzatDdStep::Compute(num) => {
                let mut needs_repair_hints = false;
                let mut has_next_compute = false;
                for next in pipeline.steps.iter().copied().skip(idx + 1) {
                    match next {
                        HowzatDdStep::Compute(_) => {
                            has_next_compute = true;
                            break;
                        }
                        HowzatDdStep::Check(check) => {
                            if check.kind == HowzatDdCheckKind::Repair {
                                needs_repair_hints = true;
                            }
                        }
                    }
                }

                let options = if has_next_compute {
                    if needs_repair_hints {
                        poly_options_inexact_repair.clone()
                    } else {
                        poly_options_cert.clone()
                    }
                } else if needs_repair_hints {
                    poly_options_inexact_repair.clone()
                } else {
                    poly_options_final.clone()
                };

                let (poly_any, time_matrix, time_dd) = compute_poly_any(
                    num,
                    purifier,
                    vertices,
                    howzat_options,
                    options,
                    &spec_label,
                )?;

                executed_computes += 1;
                if executed_computes == 1 {
                    time_fast_matrix += time_matrix;
                    time_fast_dd += time_dd;
                } else {
                    time_exact_matrix += time_matrix;
                    time_exact_dd += time_dd;
                }
                current = Some(poly_any);
            }
            HowzatDdStep::Check(check) => {
                let Some(inexact) = current.as_ref() else {
                    return Err(anyhow!("internal: howzat-dd check without preceding compute"));
                };

                let target = check.target;
                let opts = &poly_options_final;

                match check.kind {
                    HowzatDdCheckKind::Resolve => {
                        let start_cert = Instant::now();
                        if let Some(poly_any) = resolve_any(inexact, target, opts) {
                            current = Some(poly_any);
                            time_cert += start_cert.elapsed();
                            break;
                        }
                        time_cert += start_cert.elapsed();
                    }
                    HowzatDdCheckKind::Repair => {
                        let repaired = repair_any(inexact, target, opts);

                        if let Some((poly_any, ok, cert, partial, repair)) = repaired {
                            time_cert += cert;
                            time_repair_partial += partial;
                            time_repair_graph += repair;
                            if ok {
                                current = Some(poly_any);
                                break;
                            } else if idx + 1 == pipeline.steps.len() {
                                current = Some(poly_any);
                                fails = 1;
                            }
                        }
                    }
                }

                if idx + 1 == pipeline.steps.len() {
                    fails = 1;
                }
            }
        }
    }

    let Some(final_poly) = current else {
        return Err(anyhow!("internal: howzat-dd pipeline produced no poly"));
    };

    let (geometry, extract_detail) = match &final_poly {
        PolyAny::F64(poly) => summarize_howzat_geometry(poly, timing)?,
        PolyAny::RugFloat128(poly) => summarize_howzat_geometry(poly, timing)?,
        PolyAny::RugFloat256(poly) => summarize_howzat_geometry(poly, timing)?,
        PolyAny::RugFloat512(poly) => summarize_howzat_geometry(poly, timing)?,
        PolyAny::DashuFloat128(poly) => summarize_howzat_geometry(poly, timing)?,
        PolyAny::DashuFloat256(poly) => summarize_howzat_geometry(poly, timing)?,
        PolyAny::DashuFloat512(poly) => summarize_howzat_geometry(poly, timing)?,
        PolyAny::RugRat(poly) => summarize_howzat_geometry(poly, timing)?,
        PolyAny::DashuRat(poly) => summarize_howzat_geometry(poly, timing)?,
    };

    let total = start_total.elapsed();
    let fallbacks = executed_computes.saturating_sub(1);

    let detail = timing.then(|| {
        TimingDetail::HowzatDd(HowzatDdTimingDetail {
            fast_matrix: time_fast_matrix,
            fast_dd: time_fast_dd,
            cert: time_cert,
            repair_partial: time_repair_partial,
            repair_graph: time_repair_graph,
            exact_matrix: time_exact_matrix,
            exact_dd: time_exact_dd,
            incidence: extract_detail.incidence,
            vertex_adjacency: extract_detail.vertex_adjacency,
            facet_adjacency: extract_detail.facet_adjacency,
        })
    });

    let time_checks = time_cert + time_repair_partial + time_repair_graph;
    Ok(BackendRun {
        spec,
        stats: geometry.stats,
        timing: BackendTiming {
            total,
            fast: Some(time_fast_matrix + time_fast_dd),
            resolve: Some(time_checks),
            exact: if fallbacks > 0 {
                Some(time_exact_matrix + time_exact_dd)
            } else {
                None
            },
        },
        geometry: BackendGeometry::Input(InputGeometry {
            vertex_adjacency: geometry.vertex_adjacency,
            facets_to_vertices: geometry.facets_to_vertices,
            facet_adjacency: geometry.facet_adjacency,
        }),
        fails,
        fallbacks,
        error: None,
        detail,
    })
}

fn resolve_howzat_certificate_as<N: Num, M>(
    poly: &howzat::polyhedron::PolyhedronOutput<N, hullabaloo::types::Generator>,
    poly_options: &howzat::polyhedron::PolyhedronOptions,
    eps: &impl Epsilon<M>,
) -> Option<howzat::polyhedron::PolyhedronOutput<M, hullabaloo::types::Generator>>
where
    M: Rat + CoerceFrom<N>,
    <M as Rat>::Int: std::ops::SubAssign<<M as Rat>::Int>,
    for<'a> <M as Rat>::Int: std::ops::AddAssign<&'a <M as Rat>::Int>,
{
    let cert = howzat::verify::certificate(poly).ok()?;
    cert.resolve_as::<M>(
        poly_options.clone(),
        howzat::polyhedron::ResolveOptions::default(),
        eps,
    )
    .ok()
}

fn repair_howzat_facet_graph_as<M, N>(
    poly: &howzat::polyhedron::PolyhedronOutput<N, hullabaloo::types::Generator>,
    poly_options: &howzat::polyhedron::PolyhedronOptions,
    eps: &impl Epsilon<M>,
) -> Result<
    (
        howzat::polyhedron::PolyhedronOutput<M, hullabaloo::types::Generator>,
        howzat::verify::FacetGraphRepairReport,
        Duration,
        Duration,
        Duration,
    ),
    anyhow::Error,
>
where
    M: Rat + CoerceFrom<N>,
    N: Num,
    <M as Rat>::Int: std::ops::SubAssign<<M as Rat>::Int>,
    for<'a> <M as Rat>::Int: std::ops::AddAssign<&'a <M as Rat>::Int>,
{
    let start_cert = Instant::now();
    let cert = howzat::verify::certificate(poly)
        .map_err(|e| anyhow!("howzat-dd repair: missing certificate: {e:?}"))?;
    let time_cert = start_cert.elapsed();

    let resolve_options = howzat::polyhedron::ResolveOptions {
        partial_use_certificate_only: true,
        ..howzat::polyhedron::ResolveOptions::default()
    };
    let mut partial_options = poly_options.clone();
    partial_options.output_adjacency = AdjacencyOutput::Off;
    let start_partial = Instant::now();
    let prepared = cert
        .resolve_partial_prepared_minimal_as::<M>(partial_options, resolve_options, eps)
        .map_err(|e| anyhow!("howzat-dd repair: partial resolve failed: {e:?}"))?;
    let time_partial = start_partial.elapsed();

    let repair_options = howzat::verify::FacetGraphRepairOptions {
        rebuild_polyhedron_output: true,
        frontier: howzat::verify::FrontierRepairMode::General,
        ..howzat::verify::FacetGraphRepairOptions::default()
    };
    let start_repair = Instant::now();
    let repaired = howzat::verify::repair_facet_graph_from_inexact_prepared(
        &prepared,
        poly,
        repair_options,
        eps,
    )
    .map_err(|e| anyhow!("howzat-dd repair: facet-graph repair failed: {e:?}"))?;

    let report = repaired.report().clone();
    let Some(rebuilt) = repaired.rebuilt_polyhedron().cloned() else {
        return Err(anyhow!(
            "howzat-dd repair: facet-graph repair did not rebuild polyhedron"
        ));
    };
    let time_repair = start_repair.elapsed();
    Ok((rebuilt, report, time_cert, time_partial, time_repair))
}

fn run_howzat_lrs_backend<V: VerticesF64>(
    spec: Backend,
    vertices: &V,
    timing: bool,
) -> Result<BackendRun, anyhow::Error> {
    let start_total = Instant::now();

    // First, run the LRS conversion just to obtain the output-incidence certificate.
    // Keep this step minimal so we don't "pay twice" for graph construction.
    let cert_options = howzat::polyhedron::PolyhedronOptions {
        output_incidence: IncidenceOutput::Set,
        output_adjacency: AdjacencyOutput::Off,
        input_incidence: IncidenceOutput::Off,
        input_adjacency: AdjacencyOutput::Off,
        save_basis_and_tableau: false,
        save_repair_hints: false,
        profile_adjacency: false,
    };

    // Then, complete into exact arithmetic using the certificate, requesting the full
    // incidence + adjacency information we benchmark/compare.
    let exact_options = howzat::polyhedron::PolyhedronOptions {
        output_incidence: IncidenceOutput::Set,
        output_adjacency: AdjacencyOutput::List,
        input_incidence: IncidenceOutput::Off,
        input_adjacency: AdjacencyOutput::Off,
        save_basis_and_tableau: false,
        save_repair_hints: false,
        profile_adjacency: false,
    };

    let eps = f64::default_eps();
    let start_fast = Instant::now();
    let start_matrix = Instant::now();
    let matrix = build_generator_matrix_vertices::<f64, _>(vertices)?;
    let time_matrix = start_matrix.elapsed();

    type HowzatPolyF64 = howzat::polyhedron::PolyhedronOutput<f64, hullabaloo::types::Generator>;
    let start_lrs = Instant::now();
    let poly = match &spec.0 {
        BackendSpec::HowzatLrsRug => HowzatPolyF64::from_matrix_lrs_as_exact::<RugRat, f64>(
            matrix,
            cert_options,
            howzat::lrs::Options::default(),
            &eps,
        )
        .map_err(|e| anyhow!("howzat-lrs conversion failed: {e:?}"))?,
        BackendSpec::HowzatLrsDashu => {
            HowzatPolyF64::from_matrix_lrs_as_exact::<DashuRat, f64>(
                matrix,
                cert_options,
                howzat::lrs::Options::default(),
                &eps,
            )
            .map_err(|e| anyhow!("howzat-lrs conversion failed: {e:?}"))?
        }
        _ => return Err(anyhow!("internal: howzat-lrs called with non-howzat-lrs backend")),
    };
    let time_lrs = start_lrs.elapsed();
    let time_fast = start_fast.elapsed();

    // Resolve the output into exact arithmetic using the stored witness sets.
    let start_exact = Instant::now();
    let cert =
        howzat::verify::certificate(&poly).map_err(|e| anyhow!("howzat-lrs missing certificate: {e:?}"))?;

    let (geometry, extract_detail, time_exact) = match &spec.0 {
        BackendSpec::HowzatLrsRug => {
            let exact_eps = RugRat::default_eps();
            let exact_poly = cert
                .resolve_as::<RugRat>(
                    exact_options,
                    howzat::polyhedron::ResolveOptions::default(),
                    &exact_eps,
                )
                .map_err(|e| anyhow!("howzat-lrs exact resolution failed: {e:?}"))?;
            let time_exact = start_exact.elapsed();

            let (geometry, extract_detail) = summarize_howzat_geometry(&exact_poly, timing)?;
            (geometry, extract_detail, time_exact)
        }
        BackendSpec::HowzatLrsDashu => {
            let exact_eps = DashuRat::default_eps();
            let exact_poly = cert
                .resolve_as::<DashuRat>(
                    exact_options,
                    howzat::polyhedron::ResolveOptions::default(),
                    &exact_eps,
                )
                .map_err(|e| anyhow!("howzat-lrs exact resolution failed: {e:?}"))?;
            let time_exact = start_exact.elapsed();

            let (geometry, extract_detail) = summarize_howzat_geometry(&exact_poly, timing)?;
            (geometry, extract_detail, time_exact)
        }
        _ => return Err(anyhow!("internal: howzat-lrs called with non-howzat-lrs backend")),
    };

    let total = start_total.elapsed();
    let exact_total = total.saturating_sub(time_fast);

    let detail = timing.then(|| {
        TimingDetail::HowzatLrs(HowzatLrsTimingDetail {
            matrix: time_matrix,
            lrs: time_lrs,
            cert: time_exact,
            incidence: extract_detail.incidence,
            vertex_adjacency: extract_detail.vertex_adjacency,
            facet_adjacency: extract_detail.facet_adjacency,
        })
    });

    Ok(BackendRun {
        spec,
        stats: geometry.stats,
        timing: BackendTiming {
            total,
            fast: Some(time_fast),
            resolve: None,
            exact: Some(exact_total),
        },
        geometry: BackendGeometry::Input(InputGeometry {
            vertex_adjacency: geometry.vertex_adjacency,
            facets_to_vertices: geometry.facets_to_vertices,
            facet_adjacency: geometry.facet_adjacency,
        }),
        fails: 0,
        fallbacks: 0,
        error: None,
        detail,
    })
}

fn run_lrslib_hlbl_backend(
    spec: Backend,
    vertices: &[Vec<f64>],
    timing: bool,
) -> Result<BackendRun, anyhow::Error> {
    let start_total = Instant::now();

    let start = Instant::now();
    let poly = lrslib::Polyhedron::from_vertices(vertices)
        .map_err(|e| anyhow!("lrslib+hlbl: build polyhedron failed: {e}"))?;
    let time_build = start.elapsed();

    let start = Instant::now();
    let solved = poly
        .solve()
        .map_err(|e| anyhow!("lrslib+hlbl: solve failed: {e}"))?;
    let time_incidence = start.elapsed();

    let start = Instant::now();
    let vertex_graph = hullabaloo::adjacency::adjacency_from_incidence(
        solved.input_incidence().sets(),
        solved.output().rows(),
        solved.input().cols(),
        hullabaloo::adjacency::IncidenceAdjacencyOptions::default(),
    );
    let time_input_adj = start.elapsed();

    let start = Instant::now();
    let facet_graph = hullabaloo::adjacency::adjacency_from_incidence(
        solved.incidence().sets(),
        solved.input().rows(),
        solved.input().cols(),
        hullabaloo::adjacency::IncidenceAdjacencyOptions::default(),
    );
    let time_facet_adj = start.elapsed();

    let dim = vertices.first().map_or(0, |v| v.len());

    let ridges = facet_graph.adjacency.iter().map(|n| n.len()).sum::<usize>() / 2;

    let stats = Stats {
        dimension: dim,
        vertices: vertices.len(),
        facets: solved.incidence().len(),
        ridges,
    };

    let start = timing.then(Instant::now);
    let facets_to_vertices = (0..solved.incidence().len())
        .map(|i| rowset_from_list(vertices.len(), solved.incidence().set(i).unwrap_or(&[])))
        .collect::<Vec<_>>();
    let time_post_inc = start.map_or(Duration::ZERO, |start| start.elapsed());

    let start = timing.then(Instant::now);
    let vertex_adjacency = rowsets_from_adjacency_lists(&vertex_graph.adjacency, vertices.len());
    let time_post_v_adj = start.map_or(Duration::ZERO, |start| start.elapsed());

    let start = timing.then(Instant::now);
    let facet_adjacency = rowsets_from_adjacency_lists(&facet_graph.adjacency, facets_to_vertices.len());
    let time_post_f_adj = start.map_or(Duration::ZERO, |start| start.elapsed());

    let duration = start_total.elapsed();
    let detail = timing.then(|| {
        TimingDetail::Lrslib(LrslibTimingDetail {
            build: time_build,
            incidence: time_incidence,
            vertex_adjacency: time_input_adj,
            facet_adjacency: time_facet_adj,
            post_inc: time_post_inc,
            post_v_adj: time_post_v_adj,
            post_f_adj: time_post_f_adj,
        })
    });
    Ok(BackendRun {
        spec,
        stats,
        timing: BackendTiming {
            total: duration,
            fast: None,
            resolve: None,
            exact: None,
        },
        geometry: BackendGeometry::Input(InputGeometry {
            vertex_adjacency,
            facets_to_vertices,
            facet_adjacency,
        }),
        fails: 0,
        fallbacks: 0,
        error: None,
        detail,
    })
}

#[derive(Debug, Clone)]
struct HowzatGeometrySummary {
    stats: Stats,
    vertex_adjacency: Vec<RowSet>,
    facets_to_vertices: Vec<RowSet>,
    facet_adjacency: Vec<RowSet>,
}

#[derive(Debug, Clone, Default)]
struct HowzatExtractTimingDetail {
    incidence: Duration,
    vertex_adjacency: Duration,
    facet_adjacency: Duration,
}

fn edge_count(adjacency: &[RowSet]) -> usize {
    adjacency
        .iter()
        .enumerate()
        .map(|(u, neighbors)| neighbors.iter().filter(|v| v.as_index() > u).count())
        .sum()
}

fn rowset_to_vec(set: &RowSet) -> Vec<usize> {
    set.iter().map(|v| v.as_index()).collect()
}

fn summarize_howzat_geometry<N: Num>(
    howzat_poly: &howzat::polyhedron::PolyhedronOutput<N, hullabaloo::types::Generator>,
    timing: bool,
) -> Result<(HowzatGeometrySummary, HowzatExtractTimingDetail), anyhow::Error> {
    let mut detail = HowzatExtractTimingDetail::default();
    let start_incidence = timing.then(Instant::now);

    let howzat_rows = howzat_poly.input();
    let input_rows = howzat_rows.row_count();
    let redundant_input = howzat_poly
        .redundant_rows()
        .cloned()
        .unwrap_or_else(|| RowSet::new(input_rows));
    let dominant_input = howzat_poly
        .dominant_rows()
        .cloned()
        .unwrap_or_else(|| RowSet::new(input_rows));

    let output_matrix = howzat_poly.output();
    let output_rows = output_matrix.row_count();
    let output_linearity = output_matrix.linearity().clone();
    let mut active_facets_mask = vec![true; output_rows];
    for idx in output_linearity.iter() {
        active_facets_mask[idx.as_index()] = false;
    }

    let incidence = howzat_poly
        .incidence()
        .ok_or_else(|| anyhow!("howzat incidence missing (output_incidence not requested)"))?;

    // De-duplicate facets with identical vertex sets, while also dropping linearity rows.
    let mut buckets: HashMap<u64, Vec<usize>> = HashMap::new();
    let mut old_to_new: Vec<Option<usize>> = vec![None; output_rows];
    let active_facets = active_facets_mask.iter().filter(|&&a| a).count();
    let mut facets_to_vertices: Vec<RowSet> = Vec::with_capacity(active_facets);

    for (old_idx, &active) in active_facets_mask.iter().enumerate() {
        if !active {
            continue;
        }

        let face = incidence
            .set(old_idx)
            .cloned()
            .unwrap_or_else(|| RowSet::new(input_rows));
        let hash = hullabaloo::types::hash_rowset_signature_u64(&face);

        if let Some(candidates) = buckets.get(&hash)
            && let Some(&existing_idx) =
                candidates.iter().find(|&&idx| facets_to_vertices[idx] == face)
        {
            old_to_new[old_idx] = Some(existing_idx);
            continue;
        }

        let new_idx = facets_to_vertices.len();
        facets_to_vertices.push(face);
        old_to_new[old_idx] = Some(new_idx);
        buckets.entry(hash).or_default().push(new_idx);
    }

    let poly_dim = howzat_poly.dimension();
    ensure!(poly_dim > 0, "polyhedron dimension must be positive");
    let vertex_count =
        howzat_rows.row_count() - redundant_input.cardinality() - dominant_input.cardinality();

    if let Some(start) = start_incidence {
        detail.incidence = start.elapsed();
    }

    let start_vertex_adjacency = timing.then(Instant::now);
    let vertex_adjacency: Vec<RowSet> = if let Some(adj) = howzat_poly.input_adjacency()
        && adj.sets().iter().any(|s| s.cardinality() > 0)
    {
        adj.sets().to_vec()
    } else {
        let mut builder =
            hullabaloo::set_family::SetFamily::builder(input_rows, facets_to_vertices.len());
        for (facet_idx, face) in facets_to_vertices.iter().enumerate() {
            for v in face.iter() {
                builder.insert_into_set(v.as_index(), RowId::new(facet_idx));
            }
        }
        let input_incidence = builder.build();
        hullabaloo::adjacency::input_adjacency_from_incidence_set_family(
            &input_incidence,
            &redundant_input,
            &dominant_input,
        )
        .sets()
        .to_vec()
    };

    if let Some(start) = start_vertex_adjacency {
        detail.vertex_adjacency = start.elapsed();
    }

    let start_facet_adjacency = timing.then(Instant::now);
    let mut facet_adjacency: Vec<RowSet> =
        vec![RowSet::new(facets_to_vertices.len()); facets_to_vertices.len()];
    if poly_dim >= 2 {
        if let Some(facet_adjacency_sf) = howzat_poly.adjacency() {
            for (old_i, neighbors) in facet_adjacency_sf.sets().iter().enumerate() {
                let Some(new_i) = old_to_new.get(old_i).copied().flatten() else {
                    continue;
                };
                for old_j in neighbors.iter().map(|j| j.as_index()) {
                    let Some(new_j) = old_to_new.get(old_j).copied().flatten() else {
                        continue;
                    };
                    if new_i == new_j {
                        continue;
                    }
                    facet_adjacency[new_i].insert(new_j);
                }
            }
        } else {
            let rows_by_facet = facets_to_vertices
                .iter()
                .map(rowset_to_vec)
                .collect::<Vec<_>>();
            let adj = hullabaloo::adjacency::adjacency_from_rows_by_node_with::<
                hullabaloo::set_family::SetFamilyBuilder,
            >(
                &rows_by_facet,
                input_rows,
                output_matrix.col_count(),
                hullabaloo::adjacency::RowsByNodeAdjacencyOptions::default(),
            );
            facet_adjacency = adj.sets().to_vec();
        }
    }
    let ridges = edge_count(&facet_adjacency);

    if let Some(start) = start_facet_adjacency {
        detail.facet_adjacency = start.elapsed();
    }

    Ok((
        HowzatGeometrySummary {
            stats: Stats {
                dimension: poly_dim,
                vertices: vertex_count,
                facets: facets_to_vertices.len(),
                ridges,
            },
            vertex_adjacency,
            facets_to_vertices,
            facet_adjacency,
        },
        detail,
    ))
}

fn is_cddlib_error_code(err: &anyhow::Error, code: cddlib_rs::CddErrorCode) -> bool {
    use cddlib_rs::{CddError, CddWrapperError};

    err.chain().any(|cause| {
        if let Some(wrapper) = cause.downcast_ref::<CddWrapperError>() {
            matches!(
                wrapper,
                CddWrapperError::Cdd(CddError::Cdd(raw)) if *raw == code
            )
        } else if let Some(cdd) = cause.downcast_ref::<CddError>() {
            matches!(cdd, CddError::Cdd(raw) if *raw == code)
        } else {
            false
        }
    })
}

fn backend_error_run(
    spec: Backend,
    dimension: usize,
    vertices: usize,
    duration: Duration,
    error: String,
) -> BackendRun {
    BackendRun {
        spec,
        stats: Stats {
            dimension,
            vertices,
            facets: 0,
            ridges: 0,
        },
        timing: BackendTiming {
            total: duration,
            fast: None,
            resolve: None,
            exact: None,
        },
        geometry: BackendGeometry::Input(InputGeometry {
            vertex_adjacency: Vec::new(),
            facets_to_vertices: Vec::new(),
            facet_adjacency: Vec::new(),
        }),
        fails: 1,
        fallbacks: 0,
        error: Some(error),
        detail: None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn split_howzat_dd_brackets_supports_nested_eps() {
        let (base, brackets) = split_howzat_dd_brackets("f64[eps[1e-12],max]").unwrap();
        assert_eq!(base, "f64");
        assert_eq!(brackets, vec!["eps[1e-12],max"]);
    }

    #[test]
    fn parse_howzat_dd_compute_parses_f64_builtin_eps() {
        let compute = parse_howzat_dd_compute("f64[eps[1e-12]]")
            .unwrap()
            .expect("expected f64 compute stage");
        assert_eq!(compute.num, HowzatDdNum::F64);
        assert_eq!(compute.f64_eps, Some(HowzatDdF64Eps::BuiltinEm12));
        assert_eq!(compute.normalizer, None);
    }

    #[test]
    fn parse_backend_spec_accepts_f64_eps_syntax() {
        let spec: Backend = "snap@howzat-dd:f64[min,eps[1e-12]]".parse().unwrap();
        assert_eq!(spec.to_string(), "snap@howzat-dd:f64[eps[1e-12],min]");

        let spec: Backend = "howzat-dd:f64[eps[0.0]]".parse().unwrap();
        assert!(spec.is_howzat_dd());
    }

    #[test]
    fn parse_backend_arg_accepts_marker_prefixes() {
        let arg: BackendArg = "cddlib:f64".parse().unwrap();
        assert_eq!(arg.spec.to_string(), "cddlib:f64");
        assert!(!arg.authoritative);
        assert!(!arg.perf_baseline);

        let arg: BackendArg = "^cddlib:f64".parse().unwrap();
        assert!(arg.authoritative);
        assert!(!arg.perf_baseline);

        let arg: BackendArg = "%cddlib:f64".parse().unwrap();
        assert!(!arg.authoritative);
        assert!(arg.perf_baseline);

        let arg: BackendArg = "^%snap@howzat-dd:f64".parse().unwrap();
        assert_eq!(arg.spec.to_string(), "snap@howzat-dd:f64");
        assert!(arg.authoritative);
        assert!(arg.perf_baseline);

        let arg: BackendArg = "%^cddlib:gmprational".parse().unwrap();
        assert!(arg.authoritative);
        assert!(arg.perf_baseline);
    }

    #[test]
    fn parse_backend_arg_rejects_duplicate_marker_prefixes() {
        let err = "^^cddlib:f64".parse::<BackendArg>().unwrap_err();
        assert!(err.contains("multiple '^'"), "expected '^'-prefix error, got: {err}");

        let err = "%%cddlib:f64".parse::<BackendArg>().unwrap_err();
        assert!(err.contains("multiple '%'"), "expected '%'-prefix error, got: {err}");
    }

    #[test]
    fn parse_howzat_dd_compute_rejects_conflicting_f64_options() {
        let err = parse_howzat_dd_compute("f64[min,max]")
            .unwrap_err()
            .to_ascii_lowercase();
        assert!(
            err.contains("at most one normalizer"),
            "expected normalizer conflict error, got: {err}"
        );
    }
}
