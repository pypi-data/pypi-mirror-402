// tests/test_support/mod.rs
#![allow(dead_code)]

use fers_calculations::models::settings::{
    analysissettings::RigidStrategy,
    unitenums::{ForceUnit, LengthUnit, PressureUnit},
};

pub mod formulas;
pub mod helpers;
pub mod materials;
pub mod sections;

pub const TOL_ABSOLUTE_DISPLACEMENT_IN_METER: f64 = 1.0e-3;
pub const TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER: f64 = 1.0e-3;
pub const TOL_ABSOLUTE_FORCE_IN_NEWTON: f64 = 1.0e-3;
pub const TOL_ABSOLUTE_ROTATION_IN_RADIAN: f64 = 1.0e-3;

/// Strong-axis inertia used by your analytic helpers (about local z for vertical loading).
pub const SECOND_MOMENT_STRONG_AXIS_IN_M4: f64 = 10.63e-6;

pub fn make_ctx(
    test_name: &str,
    strategy: RigidStrategy,
    lu: LengthUnit,
    fu: ForceUnit,
    pu: PressureUnit,
) -> String {
    format!(
        "{} [strategy={:?}, length_unit={:?}, force_unit={:?}, pressure_unit={:?}]",
        test_name, strategy, lu, fu, pu
    )
}

pub fn assert_close_ctx(ctx: &str, expected: f64, actual: f64, tol: f64, title: &str) {
    let diff = (expected - actual).abs();
    assert!(
        diff <= tol,
        "[{ctx}] {title}: Expected {expected}, got {actual}, |diff|={diff} > {tol}",
    );
}

pub fn assert_close(expected: f64, actual: f64, tol: f64) {
    assert_close_ctx("no-context", expected, actual, tol, "no-title");
}
