use std::ffi::CString;

use rug::Integer;

use crate::{LrsError, LrsResult, sys};

#[inline]
pub(crate) fn mp_ptr_from_vec(vec: sys::lrs_mp_vector, idx: usize) -> *mut i128 {
    unsafe { *vec.add(idx) }
}

#[inline]
pub(crate) fn mp_ptr_from_matrix_row(row: *mut *mut i128, idx: usize) -> *mut i128 {
    unsafe { *row.add(idx) }
}

pub(crate) fn set_mp_from_integer(target: *mut i128, value: &Integer) -> LrsResult<()> {
    let s = value.to_string();
    // Non-GMP backend uses fixed-width arithmetic; reject coefficients that don't fit.
    s.parse::<i128>()
        .map_err(|_| LrsError::Unsupported("coefficient too large for non-GMP backend"))?;
    let c = CString::new(s).expect("integer string contained NUL");
    unsafe {
        sys::atomp(c.as_ptr(), target);
    }
    Ok(())
}

#[inline]
pub(crate) fn mp_is_zero(mp: *mut i128) -> bool {
    unsafe { *mp == 0 }
}

pub(crate) fn mp_rat_to_f64(num: *mut i128, den: *mut i128) -> f64 {
    let mut out = 0.0;
    unsafe {
        sys::rattodouble(num, den, &mut out);
    }
    out
}

pub(crate) fn mp_int_to_f64(mp: *mut i128) -> LrsResult<f64> {
    Ok(unsafe { *mp as f64 })
}

pub(crate) fn mp_int_to_integer(mp: *mut i128) -> LrsResult<Integer> {
    Ok(Integer::from(unsafe { *mp }))
}
