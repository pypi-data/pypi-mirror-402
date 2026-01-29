use std::ffi::CString;

use rug::{Integer, integer::Order};

use crate::{LrsResult, sys};

unsafe extern "C" {
    fn mpz_get_d(op: *const sys::__mpz_struct) -> f64;
}

#[inline]
pub(crate) fn mp_ptr_from_vec(vec: sys::lrs_mp_vector, idx: usize) -> *mut sys::__mpz_struct {
    unsafe { (*vec.add(idx)).as_mut_ptr() }
}

#[inline]
pub(crate) fn mp_ptr_from_matrix_row(row: *mut sys::lrs_mp, idx: usize) -> *mut sys::__mpz_struct {
    unsafe { (*row.add(idx)).as_mut_ptr() }
}

pub(crate) fn set_mp_from_integer(
    target: *mut sys::__mpz_struct,
    value: &Integer,
) -> LrsResult<()> {
    let s = value.to_string();
    let c = CString::new(s).expect("integer string contained NUL");
    unsafe {
        sys::atomp(c.as_ptr(), target);
    }
    Ok(())
}

#[inline]
pub(crate) fn mp_is_zero(mp: *mut sys::__mpz_struct) -> bool {
    // Mini-GMP uses _mp_size==0 for zero.
    unsafe { (*mp)._mp_size == 0 }
}

pub(crate) fn mp_rat_to_f64(num: *mut sys::__mpz_struct, den: *mut sys::__mpz_struct) -> f64 {
    let mut out = 0.0;
    unsafe {
        sys::rattodouble(num, den, &mut out);
    }
    out
}

pub(crate) fn mp_int_to_f64(mp: *mut sys::__mpz_struct) -> LrsResult<f64> {
    Ok(unsafe { mpz_get_d(mp.cast_const()) })
}

pub(crate) fn mp_int_to_integer(mp: *mut sys::__mpz_struct) -> LrsResult<Integer> {
    let size = unsafe { (*mp)._mp_size };
    if size == 0 {
        return Ok(Integer::new());
    }

    let limb_count = size.unsigned_abs() as usize;
    let limbs = unsafe { std::slice::from_raw_parts((*mp)._mp_d, limb_count) };
    let mut out = Integer::from_digits(limbs, Order::Lsf);
    if size < 0 {
        out = -out;
    }
    Ok(out)
}
