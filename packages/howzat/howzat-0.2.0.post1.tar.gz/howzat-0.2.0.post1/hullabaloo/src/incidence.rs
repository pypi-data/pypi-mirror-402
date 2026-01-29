use crate::set_family::SetFamily;
use crate::types::RowId;

pub fn transpose_incidence(incidence: &SetFamily) -> SetFamily {
    let mut fam = SetFamily::builder(incidence.set_capacity(), incidence.family_size());
    for (row_idx, set) in incidence.sets().iter().enumerate() {
        for elem in set.iter() {
            fam.insert_into_set(elem.as_index(), RowId::new(row_idx));
        }
    }
    fam.build()
}

pub fn invert_incidence_lists(
    output_to_input: &[Vec<usize>],
    input_size: usize,
) -> Vec<Vec<usize>> {
    let mut degrees = vec![0usize; input_size];
    for set in output_to_input {
        debug_assert!(set.windows(2).all(|w| w[0] < w[1]));
        for &in_idx in set {
            debug_assert!(in_idx < input_size);
            degrees[in_idx] += 1;
        }
    }

    let mut input_to_output: Vec<Vec<usize>> =
        degrees.into_iter().map(Vec::with_capacity).collect();

    for (out_idx, set) in output_to_input.iter().enumerate() {
        for &in_idx in set {
            debug_assert!(in_idx < input_to_output.len());
            input_to_output[in_idx].push(out_idx);
        }
    }

    input_to_output
}
