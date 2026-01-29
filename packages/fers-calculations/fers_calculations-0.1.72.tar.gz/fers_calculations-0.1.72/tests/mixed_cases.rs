#[path = "test_support/mod.rs"]
mod test_support;

use fers_calculations::models::fers::fers::FERS;
use fers_calculations::models::members::memberhinge::MemberHinge;
use fers_calculations::models::settings::analysissettings::RigidStrategy;
use fers_calculations::models::settings::unitenums::{ForceUnit, LengthUnit, PressureUnit};
use fers_calculations::models::supports::supportconditiontype::SupportConditionType;

use test_support::formulas::*;
use test_support::helpers::*;
use test_support::*;

// ---------------------------------------------------------
// Shared helpers
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

// Tolerances mapped from SI → current user units

fn tol_disp_user(tol_m: f64, length_to_m: f64) -> f64 {
    tol_m / length_to_m
}

fn tol_force_user(tol_n: f64, force_to_n: f64) -> f64 {
    tol_n / force_to_n
}

fn tol_moment_user(tol_nm: f64, force_to_n: f64, length_to_m: f64) -> f64 {
    tol_nm / (force_to_n * length_to_m)
}

// ---------------------------------------------------------
// 041: Rigid member at end
// ---------------------------------------------------------

fn test_041_rigid_member_end_load_case(
    strategy: RigidStrategy,
    length_unit: LengthUnit,
    force_unit: ForceUnit,
    pressure_unit: PressureUnit,
) {
    let ctx = make_ctx(
        "test_041_rigid_member_end_load",
        strategy,
        length_unit,
        force_unit,
        pressure_unit,
    );
    let mut model =
        make_fers_with_strategy_and_units(strategy, length_unit, force_unit, pressure_unit);

    // Physical problem in SI
    let length_elastic_si = 5.0_f64; // m
    let length_rigid_si = 5.0_f64; // m
    let force_si = 1000.0_f64; // N
    let e_si = 210.0e9_f64; // Pa

    // Unit scaling
    let u = &model.settings.unit_settings;
    let l = u.length_to_m(); // [user L] -> m
    let f = u.force_to_n(); // [user F] -> N

    // User units
    let length_elastic = length_elastic_si / l;
    let length_rigid = length_rigid_si / l;
    let force_user = force_si / f;

    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, SECOND_MOMENT_STRONG_AXIS_IN_M4);

    model.nodal_supports.push(make_fixed_support(1));

    let n1 = make_node(1, 0.0, 0.0, 0.0, Some(1));
    let n2 = make_node(2, length_elastic, 0.0, 0.0, None);
    let n3 = make_node(3, length_elastic + length_rigid, 0.0, 0.0, None);

    let m_el = make_beam_member(1, &n1, &n2, sec_id);
    let m_rg = make_rigid_member(2, &n2, &n3);
    add_member_set(&mut model, 1, vec![m_el, m_rg]);

    let lc_id = add_load_case(&mut model, 1, "End Load");
    add_nodal_load(&mut model, 1, lc_id, 2, force_user, (0.0, -1.0, 0.0));
    model.normalize_units();
    model.solve_for_load_case(lc_id).expect("Analysis failed");
    denorm_results_in_place(&mut model);
    let res = model
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("End Load")
        .unwrap();

    let dy_2 = res.displacement_nodes.get(&2).unwrap().dy;
    let dy_3 = res.displacement_nodes.get(&3).unwrap().dy;
    let rz_2 = res.displacement_nodes.get(&2).unwrap().rz;
    let rz_3 = res.displacement_nodes.get(&3).unwrap().rz;
    let mz_1 = res.reaction_nodes.get(&1).unwrap().nodal_forces.mz;

    // Expected in SI
    let dy_expected_si = cantilever_end_point_load_deflection_at_free_end(
        force_si,
        length_elastic_si,
        e_si,
        SECOND_MOMENT_STRONG_AXIS_IN_M4,
    );
    let mz_expected_si =
        cantilever_end_point_load_fixed_end_moment_magnitude(force_si, length_elastic_si);
    let rz_expected =
        -force_si * length_elastic_si.powi(2) / (2.0 * e_si * SECOND_MOMENT_STRONG_AXIS_IN_M4);

    // Convert expectations to user units
    let dy_expected = dy_expected_si / l;
    let mz_expected = mz_expected_si / (f * l);

    let tol_dy = tol_disp_user(TOL_ABSOLUTE_DISPLACEMENT_IN_METER, l);
    let tol_mz = tol_moment_user(TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER, f, l);
    let tol_rz = TOL_ABSOLUTE_ROTATION_IN_RADIAN;

    assert_close_ctx(&ctx, dy_2, dy_expected, tol_dy, "deflection at node 2");
    assert_close_ctx(
        &ctx,
        mz_1.abs(),
        mz_expected,
        tol_mz,
        "moment at fixed support",
    );
    assert!((rz_2 - rz_3).abs() < tol_rz);
    assert!((rz_2 - rz_expected).abs() < tol_rz);

    let r_x = length_rigid;
    assert_close_ctx(
        &ctx,
        dy_3,
        dy_2 + rz_2 * r_x,
        tol_dy,
        "deflection at node 3",
    );
}

#[test]
fn test_041_rigid_member_end_load() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_041_rigid_member_end_load_case(strategy, lu, fu, pu);
        }
    }
}

// ---------------------------------------------------------
// 042: Rigid member reversed
// ---------------------------------------------------------

fn test_042_rigid_member_reversed_end_load_case(
    strategy: RigidStrategy,
    length_unit: LengthUnit,
    force_unit: ForceUnit,
    pressure_unit: PressureUnit,
) {
    let ctx = make_ctx(
        "test_042_rigid_member_reversed_end_load",
        strategy,
        length_unit,
        force_unit,
        pressure_unit,
    );
    let mut model =
        make_fers_with_strategy_and_units(strategy, length_unit, force_unit, pressure_unit);

    // Physical SI
    let length_elastic_si = 5.0_f64;
    let length_rigid_si = 5.0_f64;
    let total_length_si = length_elastic_si + length_rigid_si;
    let force_si = 1000.0_f64;
    let e_si = 210.0e9_f64;
    let i_zz = SECOND_MOMENT_STRONG_AXIS_IN_M4;

    let u = &model.settings.unit_settings;
    let l = u.length_to_m();
    let f = u.force_to_n();

    let length_elastic = length_elastic_si / l;
    let length_rigid = length_rigid_si / l;
    let total_length = total_length_si / l;
    let force_user = force_si / f;

    let material_id = add_material_s235(&mut model, 1);
    let section_id = add_section_ipe180_like(&mut model, 1, material_id, i_zz);

    model.nodal_supports.push(make_fixed_support(1));

    let node1 = make_node(1, 0.0, 0.0, 0.0, Some(1));
    let node2 = make_node(2, length_elastic, 0.0, 0.0, None);
    let node3 = make_node(3, total_length, 0.0, 0.0, None);

    let beam_member = make_beam_member(1, &node1, &node2, section_id);
    let rigid_member_reversed = make_rigid_member(2, &node3, &node2);
    add_member_set(&mut model, 1, vec![beam_member, rigid_member_reversed]);

    let load_case_id = add_load_case(&mut model, 1, "End Load");
    add_nodal_load(&mut model, 1, load_case_id, 2, force_user, (0.0, -1.0, 0.0));
    model.normalize_units();
    model
        .solve_for_load_case(load_case_id)
        .expect("Analysis failed");
    denorm_results_in_place(&mut model);
    let results = model
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("End Load")
        .unwrap();

    let dy_2 = results.displacement_nodes.get(&2).unwrap().dy;
    let dy_3 = results.displacement_nodes.get(&3).unwrap().dy;
    let rz_2 = results.displacement_nodes.get(&2).unwrap().rz;
    let rz_3 = results.displacement_nodes.get(&3).unwrap().rz;
    let mz_1 = results.reaction_nodes.get(&1).unwrap().nodal_forces.mz;

    // Expected in SI
    let dy_expected_si =
        cantilever_end_point_load_deflection_at_free_end(force_si, length_elastic_si, e_si, i_zz);
    let mz_expected_si =
        cantilever_end_point_load_fixed_end_moment_magnitude(force_si, length_elastic_si);
    let rz_expected = -force_si * length_elastic_si.powi(2) / (2.0 * e_si * i_zz);

    // Back to user
    let dy_expected = dy_expected_si / l;
    let mz_expected = mz_expected_si / (f * l);
    let dy_end_from_mid = dy_2 + length_rigid * rz_2;

    let tol_dy = tol_disp_user(TOL_ABSOLUTE_DISPLACEMENT_IN_METER, l);
    let tol_mz = tol_moment_user(TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER, f, l);
    let tol_rz = TOL_ABSOLUTE_ROTATION_IN_RADIAN;

    assert_close_ctx(&ctx, dy_2, dy_expected, tol_dy, "deflection at node 2");
    assert_close_ctx(
        &ctx,
        mz_1.abs(),
        mz_expected,
        tol_mz,
        "moment at fixed support",
    );
    assert!((rz_2 - rz_3).abs() < tol_rz);
    assert!((rz_2 - rz_expected).abs() < tol_rz);
    assert_close_ctx(&ctx, dy_3, dy_end_from_mid, tol_dy, "deflection at node 3");
}

#[test]
fn test_042_rigid_member_reversed_end_load() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_042_rigid_member_reversed_end_load_case(strategy, lu, fu, pu);
        }
    }
}

// ---------------------------------------------------------
// 051: Member hinge with root rotational spring
// ---------------------------------------------------------

fn test_051_member_hinge_root_rotational_spring_case(
    strategy: RigidStrategy,
    length_unit: LengthUnit,
    force_unit: ForceUnit,
    pressure_unit: PressureUnit,
) {
    // First-order model
    let ctx = make_ctx(
        "test_051_member_hinge_root_rotational_spring",
        strategy,
        length_unit,
        force_unit,
        pressure_unit,
    );
    let mut model =
        make_fers_with_strategy_and_units(strategy, length_unit, force_unit, pressure_unit);

    // Physical SI
    let length_rigid_si = 2.5_f64;
    let length_elastic_si = 2.5_f64;
    let total_length_si = length_rigid_si + length_elastic_si;
    let force_si = 1000.0_f64;
    let target_root_rotation_rad = 0.1_f64;
    let e_si = 210.0e9_f64;
    let i_zz = SECOND_MOMENT_STRONG_AXIS_IN_M4;

    let u = &model.settings.unit_settings;
    let l = u.length_to_m();
    let f = u.force_to_n();

    let length_rigid = length_rigid_si / l;
    let total_length = total_length_si / l;
    let force_user = force_si / f;

    // Material and section
    let material_id = add_material_s235(&mut model, 1);
    let section_id = add_section_ipe180_like(&mut model, 1, material_id, i_zz);

    model.nodal_supports.push(make_fixed_support(1));

    let node1 = make_node(1, 0.0, 0.0, 0.0, Some(1));
    let node2 = make_node(2, length_rigid, 0.0, 0.0, None);
    let node3 = make_node(3, total_length, 0.0, 0.0, None);

    let rigid_member = make_rigid_member(1, &node1, &node2);
    let mut elastic_member = make_beam_member(2, &node2, &node3, section_id);

    // Rotational spring stiffness: define in SI, store in user units.
    let k_phi_z_si = (force_si * length_elastic_si) / target_root_rotation_rad; // [N·m/rad]
    let k_phi_z_user = k_phi_z_si / (f * l); // inverse of normalize (which multiplies by f*l)

    let hinge_id = 1_u32;
    let hinge = MemberHinge {
        id: hinge_id,
        hinge_type: "SPRING_Z".to_string(),
        translational_release_vx: None,
        translational_release_vy: None,
        translational_release_vz: None,
        rotational_release_mx: None,
        rotational_release_my: None,
        rotational_release_mz: Some(k_phi_z_user),
        max_tension_vx: None,
        max_tension_vy: None,
        max_tension_vz: None,
        max_moment_mx: None,
        max_moment_my: None,
        max_moment_mz: None,
    };

    if model.memberhinges.is_none() {
        model.memberhinges = Some(Vec::new());
    }
    model.memberhinges.as_mut().unwrap().push(hinge);
    elastic_member.start_hinge = Some(hinge_id);

    add_member_set(&mut model, 1, vec![rigid_member, elastic_member]);

    let load_case_id = add_load_case(&mut model, 1, "End Load");
    add_nodal_load(&mut model, 1, load_case_id, 3, force_user, (0.0, -1.0, 0.0));
    model.normalize_units();
    model
        .solve_for_load_case(load_case_id)
        .expect("First-order analysis failed");
    denorm_results_in_place(&mut model);
    let results = model
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("End Load")
        .unwrap();

    let dy_3 = results.displacement_nodes.get(&3).unwrap().dy;
    let rz_3 = results.displacement_nodes.get(&3).unwrap().rz;
    let mz_1 = results.reaction_nodes.get(&1).unwrap().nodal_forces.mz;
    let fy_1 = results.reaction_nodes.get(&1).unwrap().nodal_forces.fy;

    // Expected in SI (your original formulas)
    let phi_root_expected = (force_si * length_elastic_si) / k_phi_z_si;
    let phi_tip_expected =
        -((force_si * length_elastic_si.powi(2)) / (2.0 * e_si * i_zz) + phi_root_expected);
    let deflection_tip_expected_si = -((force_si * length_elastic_si.powi(3))
        / (3.0 * e_si * i_zz)
        + phi_root_expected * length_elastic_si);
    let reaction_mz_expected_si = force_si * (length_elastic_si + length_rigid_si);

    // Convert expectations to user units
    let deflection_tip_expected = deflection_tip_expected_si / l;
    let reaction_mz_expected = reaction_mz_expected_si / (f * l);
    let force_expected_user = force_si / f; // should equal fy_1

    let tol_dy = tol_disp_user(TOL_ABSOLUTE_DISPLACEMENT_IN_METER, l);
    let tol_mz = tol_moment_user(TOL_ABSOLUTE_MOMENT_IN_NEWTON_METER, f, l);
    let tol_f = tol_force_user(TOL_ABSOLUTE_FORCE_IN_NEWTON, f);
    let tol_rz = TOL_ABSOLUTE_ROTATION_IN_RADIAN;

    // First-order assertions
    assert_close_ctx(
        &ctx,
        dy_3,
        deflection_tip_expected,
        tol_dy,
        "deflection at node 3",
    );
    assert_close_ctx(
        &ctx,
        fy_1,
        force_expected_user,
        tol_f,
        "force at fixed support",
    );
    assert_close_ctx(&ctx, rz_3, phi_tip_expected, tol_rz, "rotation at node 3");
    assert_close_ctx(
        &ctx,
        mz_1.abs(),
        reaction_mz_expected,
        tol_mz,
        "moment at fixed support",
    );

    // Second-order sanity (same setup, second-order solver)
    let mut model_so =
        make_fers_with_strategy_and_units(strategy, length_unit, force_unit, pressure_unit);

    let material_id_so = add_material_s235(&mut model_so, 1);
    let section_id_so = add_section_ipe180_like(&mut model_so, 1, material_id_so, i_zz);

    model_so.nodal_supports.push(make_fixed_support(1));

    let node1_so = make_node(1, 0.0, 0.0, 0.0, Some(1));
    let node2_so = make_node(2, length_rigid, 0.0, 0.0, None);
    let node3_so = make_node(3, total_length, 0.0, 0.0, None);

    let rigid_member_so = make_rigid_member(1, &node1_so, &node2_so);
    let mut elastic_member_so = make_beam_member(2, &node2_so, &node3_so, section_id_so);

    let hinge_so = MemberHinge {
        id: hinge_id,
        hinge_type: "SPRING_Z".to_string(),
        translational_release_vx: None,
        translational_release_vy: None,
        translational_release_vz: None,
        rotational_release_mx: None,
        rotational_release_my: None,
        rotational_release_mz: Some(k_phi_z_user),
        max_tension_vx: None,
        max_tension_vy: None,
        max_tension_vz: None,
        max_moment_mx: None,
        max_moment_my: None,
        max_moment_mz: None,
    };

    model_so.memberhinges = Some(vec![hinge_so]);
    elastic_member_so.start_hinge = Some(hinge_id);

    add_member_set(&mut model_so, 1, vec![rigid_member_so, elastic_member_so]);

    let load_case_id_so = add_load_case(&mut model_so, 1, "End Load SO");
    add_nodal_load(
        &mut model_so,
        1,
        load_case_id_so,
        3,
        force_user,
        (0.0, -1.0, 0.0),
    );
    model_so.normalize_units();
    model_so
        .solve_for_load_case_second_order(load_case_id_so, 30)
        .expect("Second-order analysis failed");
    denorm_results_in_place(&mut model_so);
    let results_so = model_so
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("End Load SO")
        .unwrap();

    let dy_3_so = results_so.displacement_nodes.get(&3).unwrap().dy;
    let rz_3_so = results_so.displacement_nodes.get(&3).unwrap().rz;

    assert_close_ctx(
        &ctx,
        dy_3,
        dy_3_so,
        10.0 * tol_dy,
        "Second-order dy differs more than expected",
    );

    assert_close_ctx(
        &ctx,
        rz_3,
        rz_3_so,
        10.0 * tol_rz,
        "Second-order rz differs more than expected",
    );
}

#[test]
fn test_051_member_hinge_root_rotational_spring() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_051_member_hinge_root_rotational_spring_case(strategy, lu, fu, pu);
        }
    }
}

// ---------------------------------------------------------
// 061: Two colinear tension-only members with mid load
// ---------------------------------------------------------

fn test_061_two_colinear_tension_only_members_with_mid_load_case(
    strategy: RigidStrategy,
    length_unit: LengthUnit,
    force_unit: ForceUnit,
    pressure_unit: PressureUnit,
) {
    let ctx = make_ctx(
        "test_061_two_colinear_tension_only_members_with_mid_load",
        strategy,
        length_unit,
        force_unit,
        pressure_unit,
    );
    let mut model =
        make_fers_with_strategy_and_units(strategy, length_unit, force_unit, pressure_unit);

    // Physical SI
    let member_length_si = 2.5_f64;
    let force_si = 1.0_f64; // keep as 1 N to match original test
    let e_si = 210.0e9_f64;
    let area_si = 26.2e-4_f64;

    let u = &model.settings.unit_settings;
    let l = u.length_to_m();
    let f = u.force_to_n();

    let member_length = member_length_si / l;
    let force_user = force_si / f;

    let mat_id = add_material_s235(&mut model, 1);
    let sec_id = add_section_ipe180_like(&mut model, 1, mat_id, SECOND_MOMENT_STRONG_AXIS_IN_M4);

    model.nodal_supports.push(make_fixed_support(1));
    model.nodal_supports.push(make_support_custom(
        2,
        SupportConditionType::Free,
        SupportConditionType::Fixed,
        SupportConditionType::Fixed,
        SupportConditionType::Fixed,
        SupportConditionType::Fixed,
        SupportConditionType::Fixed,
    ));
    model.nodal_supports.push(make_fixed_support(3));

    let n1 = make_node(1, 0.0, 0.0, 0.0, Some(1));
    let n2 = make_node(2, member_length, 0.0, 0.0, Some(2));
    let n3 = make_node(3, 2.0 * member_length, 0.0, 0.0, Some(3));

    let m_left = make_tension_only_member(1, &n1, &n2, sec_id);
    let m_right = make_tension_only_member(2, &n2, &n3, sec_id);
    add_member_set(&mut model, 1, vec![m_left, m_right]);

    let lc_id = add_load_case(&mut model, 1, "Mid Load");
    add_nodal_load(&mut model, 1, lc_id, 2, force_user, (1.0, 0.0, 0.0));
    model.normalize_units();
    model.solve_for_load_case(lc_id).expect("Analysis failed");
    denorm_results_in_place(&mut model);
    let res = model
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("Mid Load")
        .unwrap();

    let dx_2 = res.displacement_nodes.get(&2).unwrap().dx;
    let fx_1 = res.reaction_nodes.get(&1).unwrap().nodal_forces.fx;
    let fx_3 = res.reaction_nodes.get(&3).unwrap().nodal_forces.fx;

    // Expected in SI
    let expected_dx_2_si = force_si * member_length_si / (area_si * e_si);

    // To user units
    let expected_dx_2 = expected_dx_2_si / l;
    let tol_dx = tol_disp_user(TOL_ABSOLUTE_DISPLACEMENT_IN_METER, l);
    let tol_f = tol_force_user(TOL_ABSOLUTE_FORCE_IN_NEWTON, f);

    assert_close_ctx(&ctx, dx_2, expected_dx_2, tol_dx, "deflection at node 2");
    assert!((fx_1 - (-force_user)).abs() < tol_f);
    assert!(fx_3.abs() < tol_f);
}

#[test]
fn test_061_two_colinear_tension_only_members_with_mid_load() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_061_two_colinear_tension_only_members_with_mid_load_case(strategy, lu, fu, pu);
        }
    }
}

// ---------------------------------------------------------
// 082: Two base supports horizontal tip load
// ---------------------------------------------------------

fn test_082_two_base_supports_horizontal_tip_load_reaction_signs_and_equilibrium_case(
    strategy: RigidStrategy,
    length_unit: LengthUnit,
    force_unit: ForceUnit,
    pressure_unit: PressureUnit,
) {
    let ctx = make_ctx(
        "test_082_two_base_supports_horizontal_tip_load_reaction_signs_and_equilibrium",
        strategy,
        length_unit,
        force_unit,
        pressure_unit,
    );
    let mut model =
        make_fers_with_strategy_and_units(strategy, length_unit, force_unit, pressure_unit);

    // Physical SI
    let length_horizontal_si = 5.0_f64;
    let length_vertical_si = 5.0_f64;
    let force_si = 1000.0_f64;

    let u = &model.settings.unit_settings;
    let l = u.length_to_m();
    let f = u.force_to_n();

    let length_horizontal = length_horizontal_si / l;
    let length_vertical = length_vertical_si / l;
    let force_user = force_si / f;

    let material_id = add_material_s235(&mut model, 1);
    let section_id =
        add_section_ipe180_like(&mut model, 1, material_id, SECOND_MOMENT_STRONG_AXIS_IN_M4);

    // Support 1: fully fixed
    model.nodal_supports.push(make_fixed_support(1));

    // Support 2: X free, Y free, Z fixed; rotations all free
    model.nodal_supports.push(make_support_custom(
        2,
        SupportConditionType::Free,
        SupportConditionType::Free,
        SupportConditionType::Fixed,
        SupportConditionType::Free,
        SupportConditionType::Free,
        SupportConditionType::Free,
    ));

    // Geometry
    let node1 = make_node(1, 0.0, 0.0, 0.0, Some(1));
    let node2 = make_node(2, length_horizontal, 0.0, 0.0, Some(1));
    let node3 = make_node(3, length_horizontal, length_vertical, 0.0, Some(2));

    let member_horizontal = make_beam_member(1, &node1, &node2, section_id);
    let member_vertical = make_beam_member(2, &node2, &node3, section_id);
    add_member_set(&mut model, 1, vec![member_horizontal, member_vertical]);

    let load_case_id = add_load_case(&mut model, 1, "Horizontal Tip Load");
    add_nodal_load(&mut model, 1, load_case_id, 3, force_user, (-1.0, 0.0, 0.0));
    model.normalize_units();
    model
        .solve_for_load_case(load_case_id)
        .expect("Analysis failed");
    denorm_results_in_place(&mut model);
    let results = model
        .results
        .as_ref()
        .unwrap()
        .loadcases
        .get("Horizontal Tip Load")
        .unwrap();

    let reactions_node1 = results.reaction_nodes.get(&1).unwrap().nodal_forces;
    let reactions_node2 = results.reaction_nodes.get(&2).unwrap().nodal_forces;
    let reactions_node3 = results.reaction_nodes.get(&3).unwrap().nodal_forces;

    let reaction_fx_sum = reactions_node1.fx + reactions_node2.fx + reactions_node3.fx;
    let reaction_fy_sum = reactions_node1.fy + reactions_node2.fy + reactions_node3.fy;
    let reaction_fz_sum = reactions_node1.fz + reactions_node2.fz + reactions_node3.fz;

    let tol_f = tol_force_user(TOL_ABSOLUTE_FORCE_IN_NEWTON, f);

    // Global equilibrium in X: reactions must balance applied -F → sum Rx = +F
    assert_close_ctx(
        &ctx,
        reaction_fx_sum,
        force_user,
        tol_f,
        "global Fx equilibrium",
    );

    // Global equilibrium in Y: no Y loads
    assert_close_ctx(&ctx, reaction_fy_sum, 0.0, tol_f, "global Fy equilibrium");

    // No parasitic Z reactions
    assert_close_ctx(&ctx, reaction_fz_sum, 0.0, tol_f, "global Fz equilibrium");

    // Opposite vertical reactions at bases
    let fy1 = reactions_node1.fy;
    let fy2 = reactions_node2.fy;
    assert!(
        fy1 * fy2 <= 0.0,
        "Expected opposite signs for Fy at nodes 1 and 2, got Fy1={}, Fy2={}",
        fy1,
        fy2
    );
    assert_close_ctx(&ctx, fy1 + fy2, 0.0, tol_f, "Fy at bases sum to zero");

    // Node 3 only Uz fixed → negligible Fx, Fy
    assert!(reactions_node3.fx.abs() < tol_f);
    assert!(reactions_node3.fy.abs() < tol_f);
}

#[test]
fn test_082_two_base_supports_horizontal_tip_load_reaction_signs_and_equilibrium() {
    for strategy in all_strategies() {
        for (lu, fu, pu) in unit_scenarios() {
            test_082_two_base_supports_horizontal_tip_load_reaction_signs_and_equilibrium_case(
                strategy, lu, fu, pu,
            );
        }
    }
}
