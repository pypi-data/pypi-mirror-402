use nalgebra::DMatrix;
use serde::Serialize;

#[derive(Serialize)]
#[serde(tag = "type")]
pub enum SolverEvent {
    Iteration {
        phase: &'static str,
        iteration: usize,
        residual: Option<f64>,
        relative_du: Option<f64>,
        changed_active_set: bool,
    },
    ActiveDecision {
        member_id: u32,
        member_kind: &'static str, // "Tension" or "Compression"
        axial_force: f64,          // N
        was_active: bool,
        now_active: bool,
        reason: &'static str, // e.g. "n < -tol → OFF"
        tol: f64,
        reactivation_buffer: f64,
    },
    RigidEdge {
        master: u32,
        slave: u32,
        rx: f64,
        ry: f64,
        rz: f64,
    },
    LineSearch {
        alpha: f64,
        residual_before: f64,
        residual_after: f64,
    },
    Constraint {
        node_id: u32,
        dof: &'static str, // "UX","UY","UZ","RX","RY","RZ"
        retained_in_reduced: bool,
        method: &'static str, // "ExactOneHot", "ExactRetained", "Penalty"
        penalty_alpha: Option<f64>,
        pivot_index: Option<usize>,
    },
    MatrixDiag {
        location: &'static str, // e.g. "first_order_solve" / "second_order_step"
        n: usize,
        min_diag: f64,
        max_diag: f64,
        zero_rows: usize,
        near_zero_rows: usize,
    },
    Step {
        step_index: usize,
        steps_total: usize,
        lambda: f64,
        substep_multiplier: usize,
    },
    SubstepRefined {
        old_multiplier: usize,
        new_multiplier: usize,
        reason: &'static str, // "tangent_singular" / "line_search_non_descent" / "step_failed"
    },
    ActiveMapSummary {
        ties_on: usize,
        ties_off: usize,
        struts_on: usize,
        struts_off: usize,
    },
}

pub fn log_event(ev: SolverEvent) {
    if log::log_enabled!(log::Level::Debug) {
        if let Ok(s) = serde_json::to_string(&ev) {
            log::debug!(target: "fers::diagnostics", "{}", s);
        }
    }
}

pub fn matrix_stats(k: &DMatrix<f64>) -> (f64, f64, usize, usize) {
    let n = k.nrows();
    let mut min_d = f64::INFINITY;
    let mut max_d = 0.0f64;
    let mut zero_rows = 0usize;
    let mut near_zero_rows = 0usize;

    let eps_row = 1.0e-12;
    for i in 0..n {
        let mut sum = 0.0;
        for j in 0..n {
            sum += k[(i, j)].abs();
        }
        if sum == 0.0 {
            zero_rows += 1;
        } else if sum < eps_row {
            near_zero_rows += 1;
        }
    }
    let diag_n = n.min(k.ncols());
    for i in 0..diag_n {
        let d = k[(i, i)].abs();
        if d < min_d {
            min_d = d;
        }
        if d > max_d {
            max_d = d;
        }
    }
    (min_d, max_d, zero_rows, near_zero_rows)
}

pub fn dof_label(local_dof: usize) -> &'static str {
    match local_dof {
        0 => "UX",
        1 => "UY",
        2 => "UZ",
        3 => "RX",
        4 => "RY",
        5 => "RZ",
        _ => "UNKNOWN",
    }
}
