use fers_calculations::models::fers::fers::FERS;
use fers_calculations::models::settings::analysissettings::RigidStrategy;

#[path = "test_support/mod.rs"]
mod test_support;
use fers_calculations::models::settings::unitenums::{ForceUnit, LengthUnit, PressureUnit};

use test_support::helpers::*;
use test_support::*;

// ---------------------------------------------------------
// shared (if not already defined above in this file)
// ---------------------------------------------------------

fn make_fers_with_strategy_and_units(
    strategy: RigidStrategy,
    length_unit: LengthUnit,
    force_unit: ForceUnit,
    pressure_unit: PressureUnit,
) -> FERS {
    let mut model = make_fers_with_strategy(strategy);
    model.settings.unit_settings.length_unit = length_unit;
    model.settings.unit_settings.force_unit = force_unit;
    model.settings.unit_settings.pressure_unit = pressure_unit;
    model
}

fn tol_disp_user(tol_m: f64, length_to_m: f64) -> f64 {
    tol_m / length_to_m
}

fn tol_force_user(tol_n: f64, force_to_n: f64) -> f64 {
    tol_n / force_to_n
}

fn tol_moment_user(tol_nm: f64, force_to_n: f64, length_to_m: f64) -> f64 {
    tol_nm / (force_to_n * length_to_m)
}

fn test_001_cantilever_end_point_load_case(
    strategy: RigidStrategy,
    lu: LengthUnit,
    fu: ForceUnit,
    pu: PressureUnit,
) {
    let ctx = make_ctx("test_001_cantilever_end_point_load", strategy, lu, fu, pu);

    let mut model = make_fers_with_strategy_and_units(strategy, lu, fu, pu);

    // Physical (SI)
    let l_si = 5.0_f64;
    let f_si = 1000.0_f64;
    let e_si = 210.0e9_f64;
    let i_zz = 10.63e-6_f64;

    // Units
    let u = &model.settings.unit_settings;
    let l = u.length_to_m();
    let f = u.force_to_n();

    // Geometry / load in user units
    let x1 = 0.0;
    let x2 = l_si / l;
    let p_user = f_si / f;

    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, i_zz);

    model.nodal_supports.push(make_fixed_support(1));
    let n1 = make_node(1, x1, 0.0, 0.0, Some(1));
    let n2 = make_node(2, x2, 0.0, 0.0, None);

    let m = make_beam_member(1, &n1, &n2, sec_id);
    add_member_set(&mut model, 1, vec![m]);

    let lc_id = add_load_case(&mut model, 1, "End Load");
    add_nodal_load(&mut model, 1, lc_id, 2, p_user, (0.0, -1.0, 0.0));
    model.normalize_units();

    model.solve_for_load_case(lc_id).expect("Analysis failed");
    denorm_results_in_place(&mut model);

    let res = &model.results.as_ref().unwrap().loadcases["End Load"];

    let dy_end = res.displacement_nodes[&2].dy;
    let mz_fixed = res.reaction_nodes[&1].nodal_forces.mz;

    // Analytical (SI)
    let dy_si = -(f_si * l_si.powi(3)) / (3.0 * e_si * i_zz);
    let mz_si = f_si * l_si;

    let dy_exp = dy_si / l;
    let mz_exp = mz_si / (f * l);

    let tol_d = tol_disp_user(TOL_ABSOLUTE_DISPLACEMENT_IN_METER, l);
    let tol_m = tol_moment_user(TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER, f, l);

    // expected, actual, tol
    assert_close_ctx(&ctx, dy_exp, dy_end, tol_d, "deflection at free end");
    assert_close_ctx(&ctx, mz_exp, mz_fixed, tol_m, "moment at fixed support");
}

#[test]
fn test_001_cantilever_end_point_load() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_001_cantilever_end_point_load_case(strategy, lu, fu, pu);
        }
    }
}

// =========================================================
// 002: Cantilever with intermediate point load
// =========================================================

fn test_002_cantilever_intermediate_point_load_case(
    strategy: RigidStrategy,
    lu: LengthUnit,
    fu: ForceUnit,
    pu: PressureUnit,
) {
    let ctx = make_ctx(
        "test_002_cantilever_intermediate_point_load",
        strategy,
        lu,
        fu,
        pu,
    );

    let mut model = make_fers_with_strategy_and_units(strategy, lu, fu, pu);

    // Physical (SI)
    let l_si = 5.0_f64;
    let a_si = 3.0_f64;
    let f_si = 1000.0_f64;
    let e_si = 210.0e9_f64;
    let i_zz = 10.63e-6_f64;

    // Units
    let u = &model.settings.unit_settings;
    let l = u.length_to_m(); // [user L] -> m
    let f = u.force_to_n(); // [user F] -> N

    // User units geometry / load
    let x1 = 0.0;
    let x_int = a_si / l;
    let x2 = l_si / l;
    let p_user = f_si / f;

    // Model
    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, i_zz);

    let support_id = 1_u32;
    model.nodal_supports.push(make_fixed_support(support_id));

    let n1 = make_node(1, x1, 0.0, 0.0, Some(support_id));
    let n_int = make_node(3, x_int, 0.0, 0.0, None);
    let n2 = make_node(2, x2, 0.0, 0.0, None);

    let m1 = make_beam_member(1, &n1, &n_int, sec_id);
    let m2 = make_beam_member(2, &n_int, &n2, sec_id);
    add_member_set(&mut model, 1, vec![m1, m2]);

    let lc_id = add_load_case(&mut model, 1, "Intermediate Load");
    add_nodal_load(&mut model, 1, lc_id, 3, p_user, (0.0, -1.0, 0.0));
    model.normalize_units();
    model.solve_for_load_case(lc_id).expect("Analysis failed");
    denorm_results_in_place(&mut model);

    let res = &model.results.as_ref().unwrap().loadcases["Intermediate Load"];

    let dy_int = res.displacement_nodes[&3].dy;
    let dy_end = res.displacement_nodes[&2].dy;
    let mz_fixed = res.reaction_nodes[&1].nodal_forces.mz;

    // Analytical (SI)
    // defl at x=a
    let dy_int_si = -(f_si * a_si.powi(3)) / (3.0 * e_si * i_zz);
    // defl at x=L
    let dy_end_si = -(f_si * a_si.powi(2) * (3.0 * l_si - a_si)) / (6.0 * e_si * i_zz);
    // fixed end moment
    let mz_si = f_si * a_si;

    // Convert expectations
    let dy_int_exp = dy_int_si / l;
    let dy_end_exp = dy_end_si / l;
    let mz_exp = mz_si / (f * l);

    let tol_d = tol_disp_user(TOL_ABSOLUTE_DISPLACEMENT_IN_METER, l);
    let tol_m = tol_moment_user(TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER, f, l);

    assert_close_ctx(
        &ctx,
        dy_int,
        dy_int_exp,
        tol_d,
        "deflection at intermediate point",
    );
    assert_close_ctx(&ctx, dy_end, dy_end_exp, tol_d, "deflection at free end");
    assert_close_ctx(&ctx, mz_fixed, mz_exp, tol_m, "moment at fixed support");
}

#[test]
fn test_002_cantilever_intermediate_point_load() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_002_cantilever_intermediate_point_load_case(strategy, lu, fu, pu);
        }
    }
}

// =========================================================
// 003: Cantilever with full uniform distributed load
// =========================================================

fn test_003_cantilever_uniform_distributed_load_case(
    strategy: RigidStrategy,
    lu: LengthUnit,
    fu: ForceUnit,
    pu: PressureUnit,
) {
    let ctx = make_ctx(
        "test_003_cantilever_uniform_distributed_load",
        strategy,
        lu,
        fu,
        pu,
    );

    let mut model = make_fers_with_strategy_and_units(strategy, lu, fu, pu);

    // Physical (SI)
    let l_si = 5.0_f64;
    let w_si = 1000.0_f64; // N/m
    let e_si = 210.0e9_f64;
    let i_zz = 10.63e-6_f64;

    // Units
    let u = &model.settings.unit_settings;
    let l = u.length_to_m();
    let f = u.force_to_n();

    // geometry in user units
    let x1 = 0.0;
    let x2 = l_si / l;

    // w_user such that w_user * f / l = w_si
    let w_user = w_si * l / f;

    // Model
    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, i_zz);

    model.nodal_supports.push(make_fixed_support(1));

    let n1 = make_node(1, x1, 0.0, 0.0, Some(1));
    let n2 = make_node(2, x2, 0.0, 0.0, None);

    let m = make_beam_member(1, &n1, &n2, sec_id);
    add_member_set(&mut model, 1, vec![m]);

    let lc_id = add_load_case(&mut model, 1, "Uniform Load");

    // helper from test_support; implement it to create a global-y uniform load on member 1
    add_member_distributed_load_global_y(&mut model, 1, lc_id, 1, w_user, w_user, 0.0, 1.0);
    model.normalize_units();
    model.solve_for_load_case(lc_id).expect("Analysis failed");
    denorm_results_in_place(&mut model);

    let res = &model.results.as_ref().unwrap().loadcases["Uniform Load"];

    let dy_end = res.displacement_nodes[&2].dy;
    let mz_fixed = res.reaction_nodes[&1].nodal_forces.mz;

    // Analytical in SI:
    // δ(L) = -w L^4 / (8 E I)
    // M_fixed = w L^2 / 2
    let dy_si = w_si * l_si.powi(4) / (8.0 * e_si * i_zz);
    let mz_si = w_si * l_si.powi(2) / 2.0;

    let dy_exp = dy_si / l;
    let mz_exp = -mz_si / (f * l);

    let tol_d = tol_disp_user(TOL_ABSOLUTE_DISPLACEMENT_IN_METER, l);
    let tol_m = tol_moment_user(TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER, f, l);

    assert_close_ctx(&ctx, dy_end, dy_exp, tol_d, "deflection at free end");
    assert_close_ctx(&ctx, mz_fixed, mz_exp, tol_m, "moment at fixed support");
}

#[test]
fn test_003_cantilever_uniform_distributed_load() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_003_cantilever_uniform_distributed_load_case(strategy, lu, fu, pu);
        }
    }
}

// =========================================================
// 004: Cantilever with partial uniform distributed load
// (check reaction moment)
// =========================================================

fn test_004_cantilever_partial_uniform_distributed_load_case(
    strategy: RigidStrategy,
    lu: LengthUnit,
    fu: ForceUnit,
    pu: PressureUnit,
) {
    let ctx = make_ctx(
        "test_004_cantilever_partial_uniform_distributed_load",
        strategy,
        lu,
        fu,
        pu,
    );
    let mut model = make_fers_with_strategy_and_units(strategy, lu, fu, pu);

    // Physical (SI)
    let l_si = 5.0_f64;
    let w_si = 1000.0_f64;
    let start_frac = 0.4_f64; // 2.0 m
    let end_frac = 0.7_f64; // 3.5 m

    let u = &model.settings.unit_settings;
    let l = u.length_to_m();
    let f = u.force_to_n();

    let x1 = 0.0;
    let x2 = l_si / l;
    let w_user = w_si * l / f;

    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, 10.63e-6_f64);

    model.nodal_supports.push(make_fixed_support(1));

    let n1 = make_node(1, x1, 0.0, 0.0, Some(1));
    let n2 = make_node(2, x2, 0.0, 0.0, None);

    let m = make_beam_member(1, &n1, &n2, sec_id);
    add_member_set(&mut model, 1, vec![m]);

    let lc_id = add_load_case(&mut model, 1, "Partial Uniform Load");

    add_member_distributed_load_global_y(
        &mut model, 1, lc_id, 1, w_user, w_user, start_frac, end_frac,
    );
    model.normalize_units();
    model.solve_for_load_case(lc_id).expect("Analysis failed");
    denorm_results_in_place(&mut model);

    let res = &model.results.as_ref().unwrap().loadcases["Partial Uniform Load"];

    let mz_fixed = res.reaction_nodes[&1].nodal_forces.mz;

    // Analytical: equivalent resultant and its lever arm
    let x_start = start_frac * l_si;
    let x_end = end_frac * l_si;
    let w_len = x_end - x_start;
    let r_si = w_si * w_len;
    let x_res = 0.5 * (x_start + x_end);
    let mz_si = r_si * x_res;

    let mz_exp = -mz_si / (f * l);
    let tol_m = tol_moment_user(TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER, f, l);

    assert_close_ctx(&ctx, mz_fixed, mz_exp, tol_m, "moment at fixed support");
}

#[test]
fn test_004_cantilever_partial_uniform_distributed_load() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_004_cantilever_partial_uniform_distributed_load_case(strategy, lu, fu, pu);
        }
    }
}

// =========================================================
// 005: Cantilever with full triangular & inverse triangular load
// (check deflection / reactions, as in your Python script)
// =========================================================

fn test_005_cantilever_triangular_full_case(
    strategy: RigidStrategy,
    lu: LengthUnit,
    fu: ForceUnit,
    pu: PressureUnit,
) {
    let ctx = make_ctx("test_005_cantilever_triangular_full", strategy, lu, fu, pu);
    let mut model = make_fers_with_strategy_and_units(strategy, lu, fu, pu);

    // Physical
    let l_si = 5.0_f64;
    let w_si = 1000.0_f64;
    let e_si = 210.0e9_f64;
    let i_zz: f64 = 10.63e-6_f64;

    let u = &model.settings.unit_settings;
    let l = u.length_to_m();
    let f = u.force_to_n();

    let x1 = 0.0;
    let x2 = l_si / l;
    let w_user = w_si * l / f;

    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, i_zz);

    model.nodal_supports.push(make_fixed_support(1));
    let n1 = make_node(1, x1, 0.0, 0.0, Some(1));
    let n2 = make_node(2, x2, 0.0, 0.0, None);
    let m = make_beam_member(1, &n1, &n2, sec_id);
    add_member_set(&mut model, 1, vec![m]);

    let lc_tri = add_load_case(&mut model, 1, "Triangular Load");
    let lc_inv = add_load_case(&mut model, 2, "Inverse Triangular Load");

    // Helpers should create distribution-shaped loads on member 1:
    add_member_distributed_load_global_y(&mut model, 1, lc_tri, 1, w_user, 0.0, 0.0, 1.0);

    // Inverse triangular: zero at fixed, max at free
    add_member_distributed_load_global_y(&mut model, 2, lc_inv, 1, 0.0, w_user, 0.0, 1.0);
    model.normalize_units();
    model
        .solve_for_load_case(lc_tri)
        .expect("Triangular analysis failed");
    model
        .solve_for_load_case(lc_inv)
        .expect("Inverse triangular analysis failed");
    denorm_results_in_place(&mut model);

    let res_tri = &model.results.as_ref().unwrap().loadcases["Triangular Load"];
    let res_inv = &model.results.as_ref().unwrap().loadcases["Inverse Triangular Load"];

    let dy_tri = res_tri.displacement_nodes[&2].dy;
    let mz_tri = res_tri.reaction_nodes[&1].nodal_forces.mz;
    let mz_inv = res_inv.reaction_nodes[&1].nodal_forces.mz;

    // Analytical:
    // Triangular (zero at free, max w at fixed):
    //   R = w L / 2, M_fixed = w L^2 / 6, δ(L) = -w L^4 / (30 E I)
    let dy_tri_si = -w_si * l_si.powi(4) / (30.0 * e_si * i_zz); // m
    let mz_tri_si = -w_si * l_si.powi(2) / 6.0;
    //   R = w L / 2, M_fixed = w L^2 / 3
    let mz_inv_si = -w_si * l_si.powi(2) / 3.0;

    // Print l for debug
    let dy_tri_exp = -dy_tri_si / l;
    let mz_tri_exp = mz_tri_si / (f * l);
    let mz_inv_exp = mz_inv_si / (f * l);

    let tol_d = tol_disp_user(TOL_ABSOLUTE_DISPLACEMENT_IN_METER, l);
    let tol_m = tol_moment_user(TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER, f, l);

    println!("f = {}, l = {}", f, l);
    println!("w_user = {}", w_user);
    println!("mz_tri_si = {}", mz_tri_si);
    println!("mz_tri_exp = {}", mz_tri_exp);
    println!("dy_tri = {}", dy_tri);
    println!("mz_inv = {}", mz_inv);
    println!("mz_tri = {}", mz_tri);

    assert_close_ctx(&ctx, dy_tri_exp, dy_tri, tol_d, "deflection at free end");
    assert_close_ctx(
        &ctx,
        mz_tri_exp,
        mz_tri,
        tol_m,
        "moment at fixed support triangle",
    );
    assert_close_ctx(
        &ctx,
        mz_inv_exp,
        mz_inv,
        tol_m,
        "moment at fixed support inverse",
    );
}

#[test]
fn test_005_cantilever_triangular_full() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_005_cantilever_triangular_full_case(strategy, lu, fu, pu);
        }
    }
}

// =========================================================
// 006: Cantilever with partial triangular / inverse triangular
//      (check shear + moment at fixed as in Python example)
// =========================================================

fn test_006_cantilever_partial_triangular_reactions_case(
    strategy: RigidStrategy,
    lu: LengthUnit,
    fu: ForceUnit,
    pu: PressureUnit,
) {
    let ctx = make_ctx(
        "test_006_cantilever_partial_triangular_reactions",
        strategy,
        lu,
        fu,
        pu,
    );
    let mut model = make_fers_with_strategy_and_units(strategy, lu, fu, pu);

    let l_si = 5.0_f64;
    let w_si = 1000.0_f64;

    let u = &model.settings.unit_settings;
    let l = u.length_to_m();
    let f = u.force_to_n();

    let x1 = 0.0;
    let x2 = l_si / l;
    let w_user = w_si * l / f;

    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, 10.63e-6_f64);

    model.nodal_supports.push(make_fixed_support(1));
    let n1 = make_node(1, x1, 0.0, 0.0, Some(1));
    let n2 = make_node(2, x2, 0.0, 0.0, None);
    let m = make_beam_member(1, &n1, &n2, sec_id);
    add_member_set(&mut model, 1, vec![m]);

    let lc_tri = add_load_case(&mut model, 1, "Triangular Load");
    let lc_inv = add_load_case(&mut model, 2, "Inverse Triangular Load");

    // InverseTriangular: 0 -> 0.6 L
    add_member_distributed_load_global_y(&mut model, 1, lc_tri, 1, w_user, 0.0, 0.0, 0.6);

    // Inverse triangular: 0.3 L -> 0.7 L
    add_member_distributed_load_global_y(&mut model, 2, lc_inv, 1, 0.0, w_user, 0.3, 0.7);
    model.normalize_units();
    model
        .solve_for_load_case(lc_tri)
        .expect("Triangular analysis failed");
    model
        .solve_for_load_case(lc_inv)
        .expect("Inverse triangular analysis failed");
    denorm_results_in_place(&mut model);

    let res_tri = &model.results.as_ref().unwrap().loadcases["Triangular Load"];
    let res_inv = &model.results.as_ref().unwrap().loadcases["Inverse Triangular Load"];

    let fy_tri = res_tri.reaction_nodes[&1].nodal_forces.fy;
    let fy_inv = res_inv.reaction_nodes[&1].nodal_forces.fy;
    let mz_tri = res_tri.reaction_nodes[&1].nodal_forces.mz;
    let mz_inv = res_inv.reaction_nodes[&1].nodal_forces.mz;

    // Analytical (mirroring your Python expressions):

    // Triangular 0..0.6L (zero at free, max at fixed over that segment)
    let shear_tri_si = w_si * 0.5 * l_si * (0.6 - 0.0); // note: your python used L factor; adjust as in script
    let mz_tri_si = (w_si * l_si * 0.5 * (0.6 - 0.0)) * l_si * (1.0 / 3.0) * (0.6 - 0.0); // centroid of triangle from fixed

    // Inverse triangular 0.3L..0.7L (zero at fixed, max at free over that segment)
    let shear_inv_si = w_si * 0.5 * l_si * (0.7 - 0.3);
    let mz_inv_si = shear_inv_si * ((0.3 + (2.0 / 3.0) * (0.7 - 0.3)) * l_si);

    let fy_tri_exp = -shear_tri_si / (f);
    let fy_inv_exp = -shear_inv_si / (f);
    let mz_tri_exp = -mz_tri_si / (f * l);
    let mz_inv_exp = -mz_inv_si / (f * l);

    let tol_f = tol_force_user(TOL_ABSOLUTE_FORCE_IN_NEWTON, f);
    let tol_m = tol_moment_user(TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER, f, l);

    assert_close_ctx(
        &ctx,
        fy_tri_exp,
        fy_tri,
        tol_f,
        "shear at fixed support triangle",
    );
    assert_close_ctx(
        &ctx,
        fy_inv_exp,
        fy_inv,
        tol_f,
        "shear at fixed support inverse",
    );
    assert_close_ctx(
        &ctx,
        mz_tri_exp,
        mz_tri,
        tol_m,
        "moment at fixed support triangle",
    );
    assert_close_ctx(
        &ctx,
        mz_inv_exp,
        mz_inv,
        tol_m,
        "moment at fixed support inverse",
    );
}

#[test]
fn test_006_cantilever_partial_triangular_reactions() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_006_cantilever_partial_triangular_reactions_case(strategy, lu, fu, pu);
        }
    }
}

// =========================================================
// 007: Cantilever with end moment
// =========================================================

fn test_007_cantilever_end_moment_case(
    strategy: RigidStrategy,
    lu: LengthUnit,
    fu: ForceUnit,
    pu: PressureUnit,
) {
    let ctx = make_ctx("test_007_cantilever_end_moment", strategy, lu, fu, pu);
    let mut model = make_fers_with_strategy_and_units(strategy, lu, fu, pu);

    // Physical (SI)
    let l_si = 5.0_f64;
    let m_si = 500.0_f64;
    let e_si = 210.0e9_f64;
    let i_zz = 10.63e-6_f64;

    let u = &model.settings.unit_settings;
    let l = u.length_to_m();
    let f = u.force_to_n();

    let x1 = 0.0;
    let x2 = l_si / l;

    // Nodal moment unit conversion:
    // M_user * f * l = M_si  =>  M_user = M_si / (f * l)
    let m_user = m_si / (f * l);

    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, i_zz);

    model.nodal_supports.push(make_fixed_support(1));
    let n1 = make_node(1, x1, 0.0, 0.0, Some(1));
    let n2 = make_node(2, x2, 0.0, 0.0, None);
    let m = make_beam_member(1, &n1, &n2, sec_id);
    add_member_set(&mut model, 1, vec![m]);

    let lc_id = add_load_case(&mut model, 1, "End Moment");

    add_nodal_moment(&mut model, 1, lc_id, 2, m_user, (0.0, 0.0, -1.0));
    model.normalize_units();
    model.solve_for_load_case(lc_id).expect("Analysis failed");
    denorm_results_in_place(&mut model);

    let res = &model.results.as_ref().unwrap().loadcases["End Moment"];

    let dy_end = res.displacement_nodes[&2].dy;
    let mz_fixed = res.reaction_nodes[&1].nodal_forces.mz;

    // Analytical:
    // δ(L) = -M L^2 / (2 E I)
    // M_fixed = M
    let dy_si = -m_si * l_si.powi(2) / (2.0 * e_si * i_zz);

    let dy_exp = dy_si / l;
    let mz_exp = m_si / (f * l);

    let tol_d = tol_disp_user(TOL_ABSOLUTE_DISPLACEMENT_IN_METER, l);
    let tol_m = tol_moment_user(TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER, f, l);

    assert_close_ctx(&ctx, dy_end, dy_exp, tol_d, "deflection at free end");
    assert_close_ctx(&ctx, mz_fixed, mz_exp, tol_m, "moment at fixed support");
}

#[test]
fn test_007_cantilever_end_moment() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_007_cantilever_end_moment_case(strategy, lu, fu, pu);
        }
    }
}
