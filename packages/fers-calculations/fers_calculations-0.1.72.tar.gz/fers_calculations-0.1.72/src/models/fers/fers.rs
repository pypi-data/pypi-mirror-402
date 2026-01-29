// src/models/fers/fers.rs
use crate::functions::geometry::{
    compute_num_dofs_from_members, dof_index, local_to_global_with_releases,
};
use crate::functions::results::{compute_member_results_from_displacement, extract_displacements};
use crate::functions::rigid_graph::RigidGraph;
use crate::functions::support_utils::{
    add_support_springs_to_operator, constrain_single_dof, detect_zero_energy_dofs,
};
use crate::models::settings::analysissettings::RigidStrategy;
use nalgebra::DMatrix;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap, HashSet};
use utoipa::ToSchema;

use crate::functions::hinge_and_release_operations::{
    build_local_truss_translational_spring_k, modes_from_single_ends,
};
use crate::functions::load_assembler::{
    assemble_distributed_loads, assemble_nodal_loads, assemble_nodal_moments,
};
use crate::functions::reactions::{
    compose_support_reaction_vector_equilibrium, extract_reaction_nodes,
};

use crate::diagnostics::diagnostics::{dof_label, log_event, SolverEvent};
use crate::models::imperfections::imperfectioncase::ImperfectionCase;
use crate::models::loads::loadcase::LoadCase;
use crate::models::loads::loadcombination::LoadCombination;
use crate::models::members::enums::MemberType;
use crate::models::members::memberset::MemberSet;
use crate::models::members::{
    material::Material, memberhinge::MemberHinge, section::Section, shapepath::ShapePath,
};

use crate::models::results::resultbundle::ResultsBundle;
use crate::models::results::results::{ResultType, Results};
use crate::models::results::resultssummary::ResultsSummary;
use crate::models::settings::settings::Settings;
use crate::models::supports::nodalsupport::NodalSupport;
use crate::models::supports::supportconditiontype::SupportConditionType;

pub struct UnitFactors {
    l: f64,
    f: f64,
    #[allow(dead_code)]
    p: f64,
}

#[derive(Serialize, Deserialize, ToSchema, Debug, Clone)]
pub struct FERS {
    pub member_sets: Vec<MemberSet>,
    pub load_cases: Vec<LoadCase>,
    pub load_combinations: Vec<LoadCombination>,
    pub imperfection_cases: Vec<ImperfectionCase>,
    pub settings: Settings,
    pub results: Option<ResultsBundle>,
    pub memberhinges: Option<Vec<MemberHinge>>,
    pub materials: Vec<Material>,
    pub sections: Vec<Section>,
    pub nodal_supports: Vec<NodalSupport>,
    pub shape_paths: Option<Vec<ShapePath>>,
}

// ------------------------------
// Tunable constants (see notes):
// ------------------------------

// Convergence (relative)
const REL_DU_TOL: f64 = 1.0e-6; // ||Δu|| / max(1, ||u||)

// Incremental loading for second-order
// Increased default to improve robustness near limit points
const LOAD_STEPS_DEFAULT: usize = 4;

// Boundary-condition handling on slave DOFs
// (reduced to ease conditioning; we also relax ONE_HOT_TOL_RATIO)
const BC_PENALTY_FACTOR: f64 = 1.0e3; // much stronger constraint when not exactly one-hot
const ONE_HOT_TOL_RATIO: f64 = 5.0e-2;

struct RigidElimination {
    s: DMatrix<f64>,
    full_to_red: HashMap<usize, usize>,
}

pub struct AssemblyContext<'a> {
    pub material_by_id: HashMap<u32, &'a Material>,
    pub section_by_id: HashMap<u32, &'a Section>,
    pub hinge_by_id: HashMap<u32, &'a MemberHinge>,
    pub support_by_id: HashMap<u32, &'a NodalSupport>,
}

impl<'a> AssemblyContext<'a> {
    pub fn new(model: &'a FERS) -> Self {
        let (material_by_id, section_by_id, hinge_by_id, support_by_id) = model.build_lookup_maps();
        Self {
            material_by_id,
            section_by_id,
            hinge_by_id,
            support_by_id,
        }
    }
}

pub const TRANSLATION_AXES: [(&str, usize); 3] = [("X", 0), ("Y", 1), ("Z", 2)];
pub const ROTATION_AXES: [(&str, usize); 3] = [("X", 3), ("Y", 4), ("Z", 5)];

impl FERS {
    pub fn unit_factors(&self) -> UnitFactors {
        let u = &self.settings.unit_settings;
        UnitFactors {
            l: u.length_to_m(),
            f: u.force_to_n(),
            p: u.pressure_to_pa(),
        }
    }

    pub fn normalize_units(&mut self) {
        let units = &self.settings.unit_settings;

        let l = units.length_to_m(); // length  -> m
        let f = units.force_to_n(); // force   -> N
        let p = units.pressure_to_pa(); // stress  -> Pa
        let rho = units.density_to_kg_per_m3(); // dens.   -> kg/m3

        // Shape paths
        if let Some(paths) = &mut self.shape_paths {
            for path in paths {
                path.normalize_units(l);
            }
        }

        // Nodal supports: stiffness in displacement_conditions is [F/L],
        // stiffness in rotation_conditions is [F·L].
        if (f - 1.0).abs() > 1.0e-12 || (l - 1.0).abs() > 1.0e-12 {
            for support in &mut self.nodal_supports {
                for condition in support.displacement_conditions.values_mut() {
                    condition.normalize_translation_units(f, l);
                }
                for condition in support.rotation_conditions.values_mut() {
                    condition.normalize_rotation_units(f, l);
                }
            }
        }

        // 1) Geometry: node coordinates
        if (l - 1.0).abs() > 1e-12 {
            for ms in &mut self.member_sets {
                for m in &mut ms.members {
                    m.start_node.X *= l;
                    m.start_node.Y *= l;
                    m.start_node.Z *= l;
                    m.end_node.X *= l;
                    m.end_node.Y *= l;
                    m.end_node.Z *= l;
                }
            }
        }

        // 2) Sections: A ~ L², I,J ~ L⁴
        if (l - 1.0).abs() > 1e-12 {
            let l2 = l * l;
            let l4 = l2 * l2;
            for sec in &mut self.sections {
                sec.area *= l2;
                sec.i_y *= l4;
                sec.i_z *= l4;
                sec.j *= l4;
            }
        }

        // 3) Materials: E,G,fy in pressure units; density in density units
        if (p - 1.0).abs() > 1e-12 {
            for mat in &mut self.materials {
                mat.e_mod *= p;
                mat.g_mod *= p;
                mat.yield_stress *= p;
            }
        }

        if (rho - 1.0).abs() > 1e-12 {
            for mat in &mut self.materials {
                mat.density *= rho;
            }
        }

        // 4) Loads
        if (f - 1.0).abs() > 1e-12 || (l - 1.0).abs() > 1e-12 {
            for lc in &mut self.load_cases {
                // nodal forces: F
                for nl in &mut lc.nodal_loads {
                    nl.magnitude *= f;
                }

                // nodal moments: F·L
                for nm in &mut lc.nodal_moments {
                    nm.magnitude *= f * l;
                }

                // distributed loads: F / L
                for dl in &mut lc.distributed_loads {
                    dl.magnitude *= f / l;
                    dl.end_magnitude *= f / l;
                }
            }
        }

        // 5) Member hinges
        for h in self.memberhinges.iter_mut().flatten() {
            // translational springs: F/L
            if let Some(k) = &mut h.translational_release_vx {
                *k *= f / l;
            }
            if let Some(k) = &mut h.translational_release_vy {
                *k *= f / l;
            }
            if let Some(k) = &mut h.translational_release_vz {
                *k *= f / l;
            }

            // rotational springs: F·L
            if let Some(k) = &mut h.rotational_release_mx {
                *k *= f * l;
            }
            if let Some(k) = &mut h.rotational_release_my {
                *k *= f * l;
            }
            if let Some(k) = &mut h.rotational_release_mz {
                *k *= f * l;
            }

            // capacities: forces
            if let Some(v) = &mut h.max_tension_vx {
                *v *= f;
            }
            if let Some(v) = &mut h.max_tension_vy {
                *v *= f;
            }
            if let Some(v) = &mut h.max_tension_vz {
                *v *= f;
            }

            // capacities: moments
            if let Some(v) = &mut h.max_moment_mx {
                *v *= f * l;
            }
            if let Some(v) = &mut h.max_moment_my {
                *v *= f * l;
            }
            if let Some(v) = &mut h.max_moment_mz {
                *v *= f * l;
            }
        }
    }

    pub fn denormalize_results(mut bundle: ResultsBundle, uf: &UnitFactors) -> ResultsBundle {
        let inv_l: f64 = 1.0 / uf.l;
        let inv_f: f64 = 1.0 / uf.f;
        let inv_m: f64 = 1.0 / (uf.f * uf.l);

        // Apply to all loadcases & combinations
        for res in bundle
            .loadcases
            .values_mut()
            .chain(bundle.loadcombinations.values_mut())
        {
            // Nodal displacements: [L]
            for d in res.displacement_nodes.values_mut() {
                d.dx *= inv_l;
                d.dy *= inv_l;
                d.dz *= inv_l;
            }

            // Reactions: [F], [F·L]
            for r in res.reaction_nodes.values_mut() {
                // println!(
                //     "[DL DEBUG] rfx={} rfy={} rfz={} rmx={} rmy={} rmz={}",
                //     r.nodal_forces.fx,
                //     r.nodal_forces.fy,
                //     r.nodal_forces.fz,
                //     r.nodal_forces.mx,
                //     r.nodal_forces.my,
                //     r.nodal_forces.mz
                // );
                r.nodal_forces.fx *= inv_f;
                r.nodal_forces.fy *= inv_f;
                r.nodal_forces.fz *= inv_f;
                r.nodal_forces.mx *= inv_m;
                r.nodal_forces.my *= inv_m;
                r.nodal_forces.mz *= inv_m;
            }

            // Member forces/stresses — adjust field names to your struct
            for m in res.member_results.values_mut() {
                m.end_node_forces.fx *= inv_f;
                m.end_node_forces.fy *= inv_f;
                m.end_node_forces.fz *= inv_f;
                m.end_node_forces.mx *= inv_m;
                m.end_node_forces.my *= inv_m;
                m.end_node_forces.mz *= inv_m;

                m.start_node_forces.fx *= inv_f;
                m.start_node_forces.fy *= inv_f;
                m.start_node_forces.fz *= inv_f;
                m.start_node_forces.mx *= inv_m;
                m.start_node_forces.my *= inv_m;
                m.start_node_forces.mz *= inv_m;

                m.maximums.fx *= inv_f;
                m.maximums.fy *= inv_f;
                m.maximums.fz *= inv_f;
                m.maximums.mx *= inv_m;
                m.maximums.my *= inv_m;
                m.maximums.mz *= inv_m;

                m.minimums.fx *= inv_f;
                m.minimums.fy *= inv_f;
                m.minimums.fz *= inv_f;
                m.minimums.mx *= inv_m;
                m.minimums.my *= inv_m;
                m.minimums.mz *= inv_m;
            }
        }

        bundle
    }

    pub fn build_lookup_maps(
        &self,
    ) -> (
        HashMap<u32, &Material>,
        HashMap<u32, &Section>,
        HashMap<u32, &MemberHinge>,
        HashMap<u32, &NodalSupport>,
    ) {
        let material_map: HashMap<u32, &Material> =
            self.materials.iter().map(|m| (m.id, m)).collect();
        let section_map: HashMap<u32, &Section> = self.sections.iter().map(|s| (s.id, s)).collect();
        let memberhinge_map: HashMap<u32, &MemberHinge> = self
            .memberhinges
            .iter()
            .flatten()
            .map(|mh| (mh.id, mh))
            .collect();
        let support_map: HashMap<u32, &NodalSupport> =
            self.nodal_supports.iter().map(|s| (s.id, s)).collect();

        (material_map, section_map, memberhinge_map, support_map)
    }

    fn build_operator_with_supports(
        &self,
        active_map: &std::collections::HashMap<u32, bool>,
        displacement: Option<&nalgebra::DMatrix<f64>>,
    ) -> Result<nalgebra::DMatrix<f64>, String> {
        let mut k = self.assemble_global_stiffness_matrix(active_map)?;
        if let Some(u) = displacement {
            let k_geo = self.assemble_geometric_stiffness_matrix_with_active(u, active_map)?;
            k += k_geo;
        }
        add_support_springs_to_operator(&self.member_sets, &self.nodal_supports, &mut k)?;
        Ok(k)
    }

    fn final_sign_slack(&self) -> f64 {
        self.settings.analysis_options.axial_slack
    }

    // Internal: used while iterating the active set
    #[inline]
    fn axial_slack_tolerance(&self) -> f64 {
        0.5 * self.final_sign_slack()
    }

    // Internal: hysteresis to reactivate a member after it was turned off
    #[inline]
    fn axial_reactivation_buffer(&self) -> f64 {
        10.0 * self.axial_slack_tolerance()
    }

    fn finalize_tie_strut_consistency(
        &self,
        u_full: &nalgebra::DMatrix<f64>,
        active_map: &mut std::collections::HashMap<u32, bool>,
        material_map: &std::collections::HashMap<u32, &Material>,
        section_map: &std::collections::HashMap<u32, &Section>,
    ) -> bool {
        use crate::models::members::enums::MemberType;
        let mut changed = false;
        let eps = self.final_sign_slack();

        for ms in &self.member_sets {
            for m in &ms.members {
                match m.member_type {
                    MemberType::Tension | MemberType::Compression => {
                        // If it's already OFF, skip
                        if !*active_map.get(&m.id).unwrap_or(&true) {
                            continue;
                        }
                        let n = m.calculate_axial_force_3d(u_full, material_map, section_map);
                        match m.member_type {
                            MemberType::Tension => {
                                if n < -eps {
                                    active_map.insert(m.id, false);
                                    changed = true;
                                }
                            }
                            MemberType::Compression => {
                                if n > eps {
                                    active_map.insert(m.id, false);
                                    changed = true;
                                }
                            }
                            _ => {}
                        }
                    }
                    _ => {}
                }
            }
        }
        changed
    }

    fn first_order_predictor_state(
        &self,
        load_vector_full: &nalgebra::DMatrix<f64>,
    ) -> Result<(nalgebra::DMatrix<f64>, std::collections::HashMap<u32, bool>), String> {
        use nalgebra::DMatrix;

        let tolerance: f64 = self.settings.analysis_options.tolerance;
        let max_it: usize = self.settings.analysis_options.max_iterations.unwrap_or(20) as usize;

        let mut active_map = self.init_active_map_tie_comp();
        let mut u_full = DMatrix::<f64>::zeros(
            crate::functions::geometry::compute_num_dofs_from_members(&self.member_sets),
            1,
        );

        let assembly_context = AssemblyContext::new(self);
        let elim = self.build_rigid_elimination_partial_using_hinges()?;
        let axial_slack_tolerance: f64 = self.axial_slack_tolerance();

        let mut converged = false;
        for _iter in 0..max_it {
            // Linear operator (no geometric stiffness) for the predictor
            let k_full = self.build_operator_with_supports(&active_map, None)?;

            // Reduce, apply BCs, solve
            let (mut k_red, mut f_red) = Self::reduce_system(&k_full, load_vector_full, &elim);
            self.apply_boundary_conditions_reduced(&elim, &mut k_red, &mut f_red)?;
            let u_red = k_red
                .lu()
                .solve(&f_red)
                .ok_or_else(|| "Reduced stiffness matrix is singular in predictor.".to_string())?;

            // Expand
            let u_full_new = Self::expand_solution(&elim, &u_red);
            let delta = &u_full_new - &u_full;
            u_full = u_full_new;

            // Update active set for ties/struts
            let changed = self.update_active_set(
                &u_full,
                &mut active_map,
                axial_slack_tolerance,
                &assembly_context.material_by_id,
                &assembly_context.section_by_id,
                true,
            );

            // Relative (and fallback absolute) convergence on predictor
            let u_norm = u_full.norm().max(1.0);
            if (delta.norm() / u_norm) < REL_DU_TOL && !changed {
                converged = true;
                break;
            }
            if delta.norm() < tolerance && !changed {
                converged = true;
                break;
            }
        }

        if !converged {
            return Err(format!(
                "First-order predictor did not converge within {} iterations",
                max_it
            ));
        }

        // Enforce final tie/strut consistency and re-solve once if needed
        if self.finalize_tie_strut_consistency(
            &u_full,
            &mut active_map,
            &assembly_context.material_by_id,
            &assembly_context.section_by_id,
        ) {
            let k_full = self.build_operator_with_supports(&active_map, None)?;
            let (mut k_red, mut f_red) = Self::reduce_system(&k_full, load_vector_full, &elim);
            self.apply_boundary_conditions_reduced(&elim, &mut k_red, &mut f_red)?;
            let u_red = k_red
                .lu()
                .solve(&f_red)
                .ok_or_else(|| "Predictor finalization solve failed (singular).".to_string())?;
            u_full = Self::expand_solution(&elim, &u_red);
        }

        Ok((u_full, active_map))
    }

    fn build_rigid_elimination_partial_using_hinges(&self) -> Result<RigidElimination, String> {
        use std::collections::{HashMap, HashSet};
        if matches!(
            self.settings.analysis_options.rigid_strategy,
            RigidStrategy::RigidMember
        ) {
            let number_of_dofs = compute_num_dofs_from_members(&self.member_sets);
            let s = DMatrix::<f64>::identity(number_of_dofs, number_of_dofs);
            let mut full_to_red = std::collections::HashMap::new();
            for i in 0..number_of_dofs {
                full_to_red.insert(i, i);
            }
            return Ok(RigidElimination { s, full_to_red });
        }

        #[derive(Clone, Copy)]
        struct RigidInfo {
            a: u32,
            b: u32,
            r: (f64, f64, f64),
        }

        let node_has_elastic_or_support = |node_id: u32| -> bool {
            if self.nodal_supports.iter().any(|s| s.id == node_id) {
                return true;
            }
            for ms in &self.member_sets {
                for m in &ms.members {
                    if (m.start_node.id == node_id || m.end_node.id == node_id)
                        && !matches!(m.member_type, MemberType::Rigid)
                    {
                        return true;
                    }
                }
            }
            false
        };

        // Build rigid edges once
        let rigid = RigidGraph::build(&self.member_sets)?;
        let mut rigid_elems: Vec<RigidInfo> = rigid
            .edges_sorted_master_first()
            .into_iter()
            .map(|e| RigidInfo {
                a: e.master,
                b: e.slave,
                r: e.r,
            })
            .collect();

        // Prefer the anchored end as master
        for info in &mut rigid_elems {
            let a_anchored = node_has_elastic_or_support(info.a);
            let b_anchored = node_has_elastic_or_support(info.b);
            if !a_anchored && b_anchored {
                std::mem::swap(&mut info.a, &mut info.b);
                info.r = (-info.r.0, -info.r.1, -info.r.2);
            }
        }

        let number_of_dofs = compute_num_dofs_from_members(&self.member_sets);

        // Eliminate slave DOFs and zero-energy DOFs (except masters)
        let mut eliminated: HashSet<usize> = HashSet::new();
        for info in &rigid_elems {
            for d in 0..6 {
                eliminated.insert(dof_index(info.b, d));
            }
        }

        let zero_energy = detect_zero_energy_dofs(self);
        let master_nodes: HashSet<u32> = rigid_elems.iter().map(|ri| ri.a).collect();
        for idx in zero_energy {
            let node_id: u32 = (idx / 6) as u32 + 1;
            if !master_nodes.contains(&node_id) {
                eliminated.insert(idx);
            }
        }

        // Map FULL→RED
        let mut full_to_red: HashMap<usize, usize> = HashMap::new();
        let mut red_to_full: Vec<usize> = Vec::new();
        let mut seen: HashSet<usize> = HashSet::new();
        for set in &self.member_sets {
            for member in &set.members {
                for node in [&member.start_node, &member.end_node] {
                    for d in 0..6 {
                        let fi = dof_index(node.id, d);
                        if !eliminated.contains(&fi) && seen.insert(fi) {
                            full_to_red.insert(fi, red_to_full.len());
                            red_to_full.push(fi);
                        }
                    }
                }
            }
        }

        let n_red = red_to_full.len();
        let mut s = DMatrix::<f64>::zeros(number_of_dofs, n_red);

        // Identity for retained DOFs
        for (fi, &col) in &full_to_red {
            s[(*fi, col)] = 1.0;
        }

        // Slave rows: [u_b;θ_b] = C(r)[u_a;θ_a]
        for info in &rigid_elems {
            let c = FERS::rigid_map_c(info.r.0, info.r.1, info.r.2);
            for i in 0..6 {
                let row_b = dof_index(info.b, i);
                for j in 0..6 {
                    let row_a_j = dof_index(info.a, j);
                    let coeff = c[(i, j)];
                    if coeff == 0.0 {
                        continue;
                    }
                    for col in 0..n_red {
                        s[(row_b, col)] += coeff * s[(row_a_j, col)];
                    }
                }
            }
        }

        Ok(RigidElimination { s, full_to_red })
    }

    pub fn get_member_count(&self) -> usize {
        self.member_sets.iter().map(|ms| ms.members.len()).sum()
    }

    fn assemble_element_into_global_12(
        global: &mut nalgebra::DMatrix<f64>,
        i0: usize,
        j0: usize,
        ke: &nalgebra::DMatrix<f64>,
    ) {
        debug_assert_eq!(ke.nrows(), 12);
        debug_assert_eq!(ke.ncols(), 12);
        for i in 0..6 {
            for j in 0..6 {
                global[(i0 + i, i0 + j)] += ke[(i, j)];
                global[(i0 + i, j0 + j)] += ke[(i, j + 6)];
                global[(j0 + i, i0 + j)] += ke[(i + 6, j)];
                global[(j0 + i, j0 + j)] += ke[(i + 6, j + 6)];
            }
        }
    }

    pub fn assemble_global_stiffness_matrix(
        &self,
        active_map: &std::collections::HashMap<u32, bool>,
    ) -> Result<nalgebra::DMatrix<f64>, String> {
        use crate::models::members::enums::MemberType;

        // Tiny axial stiffness factor when a Tension/Compression member is inactive.
        // Modern nonlinear solvers typically use very small values (1e-10 to 1e-12) to minimize
        // the effect of inactive slack elements while maintaining numerical stability.
        let off_scale: f64 = 1.0e-10;

        self.validate_node_ids()?;
        let assembly_context = AssemblyContext::new(self);

        let number_of_dofs: usize = compute_num_dofs_from_members(&self.member_sets);
        let mut global_stiffness_matrix =
            nalgebra::DMatrix::<f64>::zeros(number_of_dofs, number_of_dofs);

        for member_set in &self.member_sets {
            for member in &member_set.members {
                // Build a 12x12 GLOBAL element matrix according to the member behavior
                let element_global_opt: Option<nalgebra::DMatrix<f64>> = match member.member_type {
                    MemberType::Normal => {
                        let Some(_) = member.section else {
                            return Err(format!(
                                "Member {} (Normal) is missing a section id.",
                                member.id
                            ));
                        };

                        // 1) Local base K
                        let k_local_base = member
                            .calculate_stiffness_matrix_3d(
                                &assembly_context.material_by_id,
                                &assembly_context.section_by_id,
                            )
                            .ok_or_else(|| {
                                format!("Member {} failed to build local stiffness.", member.id)
                            })?;

                        // 2) Apply end releases / semi-rigid springs and transform to GLOBAL in one place
                        let k_global = local_to_global_with_releases(
                            member,
                            &k_local_base,
                            &assembly_context.hinge_by_id,
                        )?;

                        Some(k_global)
                    }

                    MemberType::Truss => {
                        let mut k_global: nalgebra::Matrix<
                            f64,
                            nalgebra::Dyn,
                            nalgebra::Dyn,
                            nalgebra::VecStorage<f64, nalgebra::Dyn, nalgebra::Dyn>,
                        > = member
                            .calculate_truss_stiffness_matrix_3d(
                                &assembly_context.material_by_id,
                                &assembly_context.section_by_id,
                            )
                            .ok_or_else(|| {
                                format!(
                                    "Member {} (Truss) failed to build truss stiffness.",
                                    member.id
                                )
                            })?;

                        // Optional: translational node-to-ground springs from hinges (LOCAL → GLOBAL)
                        let a_h = member
                            .start_hinge
                            .and_then(|id| assembly_context.hinge_by_id.get(&id).copied());
                        let b_h = member
                            .end_hinge
                            .and_then(|id| assembly_context.hinge_by_id.get(&id).copied());
                        let (a_trans, _a_rot, b_trans, _b_rot) = modes_from_single_ends(a_h, b_h);

                        let k_s_local = build_local_truss_translational_spring_k(a_trans, b_trans);
                        if k_s_local.iter().any(|v| *v != 0.0) {
                            let t = member.calculate_transformation_matrix_3d();
                            let k_s_global = t.transpose() * k_s_local * t;
                            k_global += k_s_global;
                        }

                        Some(k_global)
                    }

                    // >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                    // Ties/Struts: keep a tiny stiffness when "inactive".
                    // >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                    MemberType::Tension | MemberType::Compression => {
                        let is_active: bool = *active_map.get(&member.id).unwrap_or(&true);

                        // Build the base (axial) truss stiffness in GLOBAL
                        let k_opt = member.calculate_truss_stiffness_matrix_3d(
                            &assembly_context.material_by_id,
                            &assembly_context.section_by_id,
                        );

                        if let Some(mut k) = k_opt {
                            if is_active {
                                Some(k)
                            } else {
                                // When inactive, keep a tiny axial stiffness to avoid K-jumps
                                k *= off_scale;
                                Some(k)
                            }
                        } else {
                            None
                        }
                    }

                    MemberType::Rigid => match self.settings.analysis_options.rigid_strategy {
                        // handled via MPC/elimination
                        crate::models::settings::analysissettings::RigidStrategy::LinearMpc => None,

                        // Very stiff "real" member
                        crate::models::settings::analysissettings::RigidStrategy::RigidMember => {
                            // ------------- pick a base section id -------------
                            let pick_base_section =
                                |m: &crate::models::members::member::Member| -> Option<u32> {
                                    // 1) explicit
                                    if let Some(id) = m.section {
                                        return Some(id);
                                    }
                                    // 2) neighbor section
                                    for ms2 in &self.member_sets {
                                        for mn in &ms2.members {
                                            if !matches!(mn.member_type, MemberType::Rigid)
                                                && (mn.start_node.id == m.start_node.id
                                                    || mn.start_node.id == m.end_node.id
                                                    || mn.end_node.id == m.start_node.id
                                                    || mn.end_node.id == m.end_node.id)
                                            {
                                                if let Some(sec) = mn.section {
                                                    return Some(sec);
                                                }
                                            }
                                        }
                                    }
                                    // 3) first section in the model
                                    self.sections.first().map(|s| s.id)
                                };

                            let base_sec_id = pick_base_section(member).ok_or_else(|| {
                            format!(
                                "RigidMember needs at least one section in the model or a section on rigid member {}.",
                                member.id
                            )
                        })?;

                            // ------------- get E of that base section -------------
                            let e_member = self
                                .sections
                                .iter()
                                .find(|s| s.id == base_sec_id)
                                .and_then(|sec| {
                                    self.materials.iter().find(|mat| mat.id == sec.material)
                                })
                                .map(|mat| mat.e_mod)
                                .unwrap_or(210.0e9);

                            let e_target = self.max_e_mod_in_model() * 1.0e4; // toned down from 1e6
                            let factor = (e_target / e_member.max(1.0)).clamp(1.0, 1.0e8);

                            // ------------- build local K using the base section -------------
                            let mut tmp: crate::models::members::member::Member = (*member).clone();
                            tmp.section = Some(base_sec_id);

                            let k_local_base = tmp
                                .calculate_stiffness_matrix_3d(
                                    &assembly_context.material_by_id,
                                    &assembly_context.section_by_id,
                                )
                                .ok_or_else(|| {
                                    format!("Rigid member {} failed to build local K.", member.id)
                                })?;

                            let k_local_scaled = k_local_base * factor;

                            // No geometric stiffness for rigid members
                            let k_global = local_to_global_with_releases(
                                &tmp,
                                &k_local_scaled,
                                &assembly_context.hinge_by_id,
                            )?;

                            Some(k_global)
                        }
                    },
                };

                if let Some(element_global) = element_global_opt {
                    let start_index = (member.start_node.id as usize - 1) * 6;
                    let end_index = (member.end_node.id as usize - 1) * 6;

                    Self::assemble_element_into_global_12(
                        &mut global_stiffness_matrix,
                        start_index,
                        end_index,
                        &element_global,
                    );
                }
            }
        }

        Ok(global_stiffness_matrix)
    }

    fn max_e_mod_in_model(&self) -> f64 {
        let mut e_max = 0.0_f64;
        for m in &self.materials {
            if m.e_mod.is_finite() && m.e_mod > e_max {
                e_max = m.e_mod;
            }
        }
        if e_max <= 0.0 {
            210.0e9_f64
        } else {
            e_max
        }
    }

    fn assemble_geometric_stiffness_matrix_with_active(
        &self,
        displacement: &nalgebra::DMatrix<f64>,
        active_map: &std::collections::HashMap<u32, bool>,
    ) -> Result<nalgebra::DMatrix<f64>, String> {
        use crate::models::members::enums::MemberType;
        let assembly_context: AssemblyContext<'_> = AssemblyContext::new(self);
        let n = compute_num_dofs_from_members(&self.member_sets);
        let mut k_geo = nalgebra::DMatrix::<f64>::zeros(n, n);

        for member_set in &self.member_sets {
            for member in &member_set.members {
                // Skip rigid: enforced by MPC; contributes no element geometry
                if matches!(member.member_type, MemberType::Rigid) {
                    continue;
                }
                // Skip deactivated tension/compression
                if matches!(
                    member.member_type,
                    MemberType::Tension | MemberType::Compression
                ) && !*active_map.get(&member.id).unwrap_or(&true)
                {
                    continue;
                }

                let mut n_axial = member.calculate_axial_force_3d(
                    displacement,
                    &assembly_context.material_by_id,
                    &assembly_context.section_by_id,
                );
                let n_tol = self.axial_slack_tolerance().max(1.0e-6);
                if n_axial.abs() < n_tol {
                    n_axial = 0.0;
                }

                let k_g_local_base = member.calculate_geometric_stiffness_matrix_3d(n_axial);

                let k_g_global = local_to_global_with_releases(
                    member,
                    &k_g_local_base,
                    &assembly_context.hinge_by_id,
                )?;

                let i0 = (member.start_node.id as usize - 1) * 6;
                let j0 = (member.end_node.id as usize - 1) * 6;
                Self::assemble_element_into_global_12(&mut k_geo, i0, j0, &k_g_global);
            }
        }
        Ok(k_geo)
    }

    pub fn validate_node_ids(&self) -> Result<(), String> {
        // Collect all node IDs in a HashSet for quick lookup
        let mut node_ids: HashSet<u32> = HashSet::new();

        // Populate node IDs from all members
        for member_set in &self.member_sets {
            for member in &member_set.members {
                node_ids.insert(member.start_node.id);
                node_ids.insert(member.end_node.id);
            }
        }

        // Ensure IDs start at 1 and are consecutive
        let max_id = *node_ids.iter().max().unwrap_or(&0);
        for id in 1..=max_id {
            if !node_ids.contains(&id) {
                return Err(format!(
                    "Node ID {} is missing. Node IDs must be consecutive starting from 1.",
                    id
                ));
            }
        }

        Ok(())
    }

    fn update_active_set(
        &self,
        displacement: &nalgebra::DMatrix<f64>,
        active_map: &mut std::collections::HashMap<u32, bool>,
        axial_slack_tolerance: f64,
        material_map: &std::collections::HashMap<u32, &Material>,
        section_map: &std::collections::HashMap<u32, &Section>,
        allow_reactivation: bool,
    ) -> bool {
        use crate::models::members::enums::MemberType;

        let mut changed = false;
        let axial_reactivation_buffer = if allow_reactivation {
            self.axial_reactivation_buffer()
        } else {
            f64::INFINITY
        };

        let mut ties_on = 0usize;
        let mut ties_off = 0usize;
        let mut struts_on = 0usize;
        let mut struts_off = 0usize;

        for ms in &self.member_sets {
            for m in &ms.members {
                if !matches!(m.member_type, MemberType::Tension | MemberType::Compression) {
                    continue;
                }
                let n = m.calculate_axial_force_3d(displacement, material_map, section_map);
                let was = active_map.get(&m.id).copied().unwrap_or(true);
                let mut now = was;
                let mut reason: &'static str = "unchanged";

                match m.member_type {
                    MemberType::Tension => {
                        if was {
                            now = n >= -axial_slack_tolerance;
                            if !now {
                                reason = "n < -tol → OFF";
                            }
                        } else {
                            now = allow_reactivation && n >= axial_reactivation_buffer;
                            if now {
                                reason = "n ≥ reactivate_buffer → ON";
                            }
                        }
                    }
                    MemberType::Compression => {
                        if was {
                            now = n <= axial_slack_tolerance;
                            if !now {
                                reason = "n > +tol → OFF";
                            }
                        } else {
                            now = allow_reactivation && n <= -axial_reactivation_buffer;
                            if now {
                                reason = "n ≤ -reactivate_buffer → ON";
                            }
                        }
                    }
                    _ => {}
                }

                if now != was {
                    active_map.insert(m.id, now);
                    changed = true;
                    log_event(SolverEvent::ActiveDecision {
                        member_id: m.id,
                        member_kind: match m.member_type {
                            MemberType::Tension => "Tension",
                            MemberType::Compression => "Compression",
                            _ => "Other",
                        },
                        axial_force: n,
                        was_active: was,
                        now_active: now,
                        reason,
                        tol: axial_slack_tolerance,
                        reactivation_buffer: axial_reactivation_buffer,
                    });
                }

                match m.member_type {
                    MemberType::Tension => {
                        if now {
                            ties_on += 1
                        } else {
                            ties_off += 1
                        }
                    }
                    MemberType::Compression => {
                        if now {
                            struts_on += 1
                        } else {
                            struts_off += 1
                        }
                    }
                    _ => {}
                }
            }
        }

        log_event(SolverEvent::ActiveMapSummary {
            ties_on,
            ties_off,
            struts_on,
            struts_off,
        });

        changed
    }

    pub fn assemble_load_vector_for_combination(
        &self,
        combination_id: u32,
    ) -> Result<DMatrix<f64>, String> {
        let num_dofs = compute_num_dofs_from_members(&self.member_sets);
        let mut f_comb = DMatrix::<f64>::zeros(num_dofs, 1);

        // Find the combination by its id field
        let combo = self
            .load_combinations
            .iter()
            .find(|lc| lc.id == combination_id)
            .ok_or_else(|| format!("LoadCombination {} not found.", combination_id))?;

        // Now iterate the HashMap<u32, f64>
        for (&case_id, &factor) in &combo.load_cases_factors {
            let f_case = self.assemble_load_vector_for_case(case_id);
            f_comb += f_case * factor;
        }

        Ok(f_comb)
    }

    fn rigid_map_c(r_x: f64, r_y: f64, r_z: f64) -> nalgebra::SMatrix<f64, 6, 6> {
        use nalgebra::{Matrix3, SMatrix};

        let i3 = Matrix3::<f64>::identity();
        let skew = Matrix3::<f64>::new(0.0, -r_z, r_y, r_z, 0.0, -r_x, -r_y, r_x, 0.0);

        // [u_b; θ_b] = [I  -[r]_x; 0  I] [u_a; θ_a]
        let mut c = SMatrix::<f64, 6, 6>::zeros();
        c.fixed_view_mut::<3, 3>(0, 0).copy_from(&i3);
        c.fixed_view_mut::<3, 3>(0, 3).copy_from(&(-skew));
        c.fixed_view_mut::<3, 3>(3, 3).copy_from(&i3);
        c
    }

    fn reduce_system(
        k_full: &DMatrix<f64>,
        f_full: &DMatrix<f64>,
        elim: &RigidElimination,
    ) -> (DMatrix<f64>, DMatrix<f64>) {
        let k_red = elim.s.transpose() * k_full * &elim.s;
        let f_red = elim.s.transpose() * f_full;
        (k_red, f_red)
    }

    fn expand_solution(elim: &RigidElimination, u_red: &DMatrix<f64>) -> DMatrix<f64> {
        &elim.s * u_red
    }

    fn constrain_linear_constraint_penalty(
        &self,
        k_red: &mut nalgebra::DMatrix<f64>,
        rhs_red: &mut nalgebra::DMatrix<f64>,
        a_column: &nalgebra::DMatrix<f64>,
        prescribed: f64,
        penalty_factor: f64,
    ) -> f64 {
        let n = k_red.nrows();
        debug_assert_eq!(n, k_red.ncols());
        debug_assert_eq!(a_column.nrows(), n);
        debug_assert_eq!(a_column.ncols(), 1);

        // ||a||
        let mut norm_a_sq = 0.0;
        for i in 0..n {
            norm_a_sq += a_column[(i, 0)] * a_column[(i, 0)];
        }
        let inv_norm_a = if norm_a_sq > 0.0 {
            1.0 / norm_a_sq.sqrt()
        } else {
            0.0
        };

        // aᵀ K a  (use current K; if zero, fall back to max_diag)
        for i in 0..n {
            let ai = a_column[(i, 0)];
            if ai == 0.0 {
                continue;
            }
            for j in 0..n {
                let aj = a_column[(j, 0)];
                if aj == 0.0 {
                    continue;
                }
            }
        }
        let mut max_diag = 0.0_f64;
        for i in 0..n {
            max_diag = max_diag.max(k_red[(i, i)].abs());
        }
        if max_diag <= 0.0 {
            max_diag = 1.0;
        }

        let alpha_base = penalty_factor * max_diag;
        let alpha = alpha_base.clamp(1.0e-6 * max_diag, 1.0e3 * max_diag);

        // K += alpha * (â âᵀ)
        for i in 0..n {
            let ai = a_column[(i, 0)] * inv_norm_a;
            if ai == 0.0 {
                continue;
            }
            for j in 0..n {
                let aj = a_column[(j, 0)] * inv_norm_a;
                if aj == 0.0 {
                    continue;
                }
                k_red[(i, j)] += alpha * ai * aj;
            }
        }

        if prescribed != 0.0 && inv_norm_a != 0.0 {
            let rhs_scale = alpha * prescribed * inv_norm_a;
            for i in 0..n {
                rhs_red[(i, 0)] += rhs_scale * a_column[(i, 0)];
            }
        }

        alpha
    }

    /// Try to detect whether a constraint vector is essentially "one-hot" on a single reduced DOF.
    /// Returns Some(pivot_index) if exactly or approximately one-hot, otherwise None.
    fn detect_one_hot_constraint(
        &self,
        a_column: &nalgebra::DMatrix<f64>,
        tolerance_ratio: f64,
    ) -> Option<usize> {
        debug_assert_eq!(a_column.ncols(), 1, "Constraint vector must be a column.");
        let n: usize = a_column.nrows();

        // Find the entry with the largest absolute value
        let mut max_val: f64 = 0.0;
        let mut max_idx: usize = 0;
        for i in 0..n {
            let v: f64 = a_column[(i, 0)].abs();
            if v > max_val {
                max_val = v;
                max_idx = i;
            }
        }
        if max_val == 0.0 {
            return None;
        }

        // Sum of squares of all other coefficients
        let mut sum_sq_other: f64 = 0.0;
        for i in 0..n {
            if i == max_idx {
                continue;
            }
            let v: f64 = a_column[(i, 0)];
            sum_sq_other += v * v;
        }

        // If the energy of others is small relative to the pivot, treat it as one-hot
        if sum_sq_other <= (tolerance_ratio * tolerance_ratio) * (max_val * max_val) {
            Some(max_idx)
        } else {
            None
        }
    }

    fn apply_boundary_conditions_reduced(
        &self,
        elim: &RigidElimination,
        k_red: &mut nalgebra::DMatrix<f64>,
        rhs_red: &mut nalgebra::DMatrix<f64>,
    ) -> Result<(), String> {
        use std::collections::{HashMap, HashSet};

        let support_map: HashMap<u32, &NodalSupport> =
            self.nodal_supports.iter().map(|s| (s.id, s)).collect();

        let n_red: usize = k_red.nrows();
        debug_assert_eq!(n_red, k_red.ncols(), "Reduced stiffness must be square.");
        debug_assert_eq!(
            rhs_red.nrows(),
            n_red,
            "RHS size must match reduced system size."
        );
        debug_assert_eq!(rhs_red.ncols(), 1, "RHS must be a column vector.");

        let mut constrained_full_dofs: HashSet<usize> = HashSet::new();

        for ms in &self.member_sets {
            for m in &ms.members {
                for node in [&m.start_node, &m.end_node] {
                    let Some(support_id) = node.nodal_support else {
                        continue;
                    };

                    let Some(support) = support_map.get(&support_id) else {
                        continue;
                    };

                    let base_full = (node.id as usize - 1) * 6;

                    for (axis_label, local_dof) in TRANSLATION_AXES {
                        let cond_opt =
                            support.displacement_conditions.get(axis_label).or_else(|| {
                                support
                                    .displacement_conditions
                                    .get(&axis_label.to_ascii_lowercase())
                            });
                        let is_fixed: bool = cond_opt
                            .map(|c| matches!(c.condition_type, SupportConditionType::Fixed))
                            .unwrap_or(true);
                        if !is_fixed {
                            continue;
                        }

                        let fi: usize = base_full + local_dof;
                        if !constrained_full_dofs.insert(fi) {
                            continue;
                        }

                        if let Some(ri) = elim.full_to_red.get(&fi).copied() {
                            constrain_single_dof(k_red, rhs_red, ri, 0.0);
                        } else {
                            let mut a_column = nalgebra::DMatrix::<f64>::zeros(n_red, 1);
                            for j in 0..n_red {
                                a_column[(j, 0)] = elim.s[(fi, j)];
                            }

                            if let Some(pivot_j) =
                                self.detect_one_hot_constraint(&a_column, ONE_HOT_TOL_RATIO)
                            {
                                constrain_single_dof(k_red, rhs_red, pivot_j, 0.0);
                            } else {
                                let alpha = self.constrain_linear_constraint_penalty(
                                    k_red,
                                    rhs_red,
                                    &a_column,
                                    0.0,
                                    BC_PENALTY_FACTOR,
                                );
                                log_event(SolverEvent::Constraint {
                                    node_id: node.id,
                                    dof: dof_label(local_dof),
                                    retained_in_reduced: false,
                                    method: "Penalty",
                                    penalty_alpha: Some(alpha),
                                    pivot_index: None,
                                });
                            }
                        }
                    }

                    // Handle rotations
                    for (axis_label, local_dof) in ROTATION_AXES {
                        let cond_opt = support.rotation_conditions.get(axis_label).or_else(|| {
                            support
                                .rotation_conditions
                                .get(&axis_label.to_ascii_lowercase())
                        });
                        let is_fixed: bool = cond_opt
                            .map(|c| matches!(c.condition_type, SupportConditionType::Fixed))
                            .unwrap_or(true);
                        if !is_fixed {
                            continue;
                        }

                        let fi: usize = base_full + local_dof;
                        // Skip duplicates
                        if !constrained_full_dofs.insert(fi) {
                            continue;
                        }

                        if let Some(ri) = elim.full_to_red.get(&fi).copied() {
                            constrain_single_dof(k_red, rhs_red, ri, 0.0);
                            log_event(SolverEvent::Constraint {
                                node_id: node.id,
                                dof: dof_label(local_dof),
                                retained_in_reduced: true,
                                method: "ExactRetained",
                                penalty_alpha: None,
                                pivot_index: Some(ri),
                            });
                        } else {
                            let mut a_column = nalgebra::DMatrix::<f64>::zeros(n_red, 1);
                            for j in 0..n_red {
                                a_column[(j, 0)] = elim.s[(fi, j)];
                            }

                            if let Some(pivot_j) =
                                self.detect_one_hot_constraint(&a_column, ONE_HOT_TOL_RATIO)
                            {
                                constrain_single_dof(k_red, rhs_red, pivot_j, 0.0);
                                log_event(SolverEvent::Constraint {
                                    node_id: node.id,
                                    dof: dof_label(local_dof),
                                    retained_in_reduced: false,
                                    method: "ExactOneHot",
                                    penalty_alpha: None,
                                    pivot_index: Some(pivot_j),
                                });
                            } else {
                                self.constrain_linear_constraint_penalty(
                                    k_red,
                                    rhs_red,
                                    &a_column,
                                    0.0,
                                    BC_PENALTY_FACTOR,
                                );
                            }
                        }
                    }
                }
            }
        }

        Ok(())
    }

    pub fn assemble_load_vector_for_case(&self, load_case_id: u32) -> DMatrix<f64> {
        let num_dofs = compute_num_dofs_from_members(&self.member_sets);
        let mut f = DMatrix::<f64>::zeros(num_dofs, 1);

        if let Some(load_case) = self.load_cases.iter().find(|lc| lc.id == load_case_id) {
            assemble_nodal_loads(load_case, &mut f);
            assemble_nodal_moments(load_case, &mut f);
            assemble_distributed_loads(load_case, &self.member_sets, &mut f, load_case_id);
        }
        f
    }

    fn init_active_map_tie_comp(&self) -> HashMap<u32, bool> {
        let mut map = HashMap::new();
        for ms in &self.member_sets {
            for member in &ms.members {
                if matches!(
                    member.member_type,
                    MemberType::Tension | MemberType::Compression
                ) {
                    map.insert(member.id, true);
                }
            }
        }
        map
    }

    fn solve_first_order_common(
        &mut self,
        load_vector_full: nalgebra::DMatrix<f64>,
        name: String,
        result_type: ResultType,
    ) -> Result<Results, String> {
        let tolerance: f64 = self.settings.analysis_options.tolerance;
        let max_it: usize = self.settings.analysis_options.max_iterations.unwrap_or(20) as usize;
        let axial_slack_tolerance: f64 = self.axial_slack_tolerance();
        let allow_reactivation_in_loop = !matches!(result_type, ResultType::Loadcombination(_));
        let mut active_map = self.init_active_map_tie_comp();
        let mut u_full =
            nalgebra::DMatrix::<f64>::zeros(compute_num_dofs_from_members(&self.member_sets), 1);

        let assembly_context: AssemblyContext<'_> = AssemblyContext::new(self);

        // Build rigid elimination (S) once; it depends only on topology/hinges
        let elim = self.build_rigid_elimination_partial_using_hinges()?;

        let mut converged = false;
        for _iter in 0..max_it {
            // Linear operator (no geometric stiffness) for first-order analysis
            let k_full = self.build_operator_with_supports(&active_map, None)?;

            // Reduce system: K_r = Sᵀ K S,  f_r = Sᵀ f
            let (mut k_red, mut f_red) = Self::reduce_system(&k_full, &load_vector_full, &elim);

            // Apply boundary conditions in REDUCED space
            self.apply_boundary_conditions_reduced(&elim, &mut k_red, &mut f_red)?;

            // Solve reduced system
            let u_red = k_red.lu().solve(&f_red).ok_or_else(|| {
                "Reduced stiffness matrix is singular or near-singular".to_string()
            })?;

            // Expand to FULL space
            let u_full_new = Self::expand_solution(&elim, &u_red);

            // Active-set update (Tension/Compression) uses FULL displacement
            let delta = &u_full_new - &u_full;
            u_full = u_full_new;

            let changed = self.update_active_set(
                &u_full,
                &mut active_map,
                axial_slack_tolerance,
                &assembly_context.material_by_id,
                &assembly_context.section_by_id,
                allow_reactivation_in_loop,
            );

            #[cfg(debug_assertions)]
            {
                if matches!(result_type, ResultType::Loadcombination(_)) {
                    use crate::models::members::enums::MemberType;
                    for ms in &self.member_sets {
                        for m in &ms.members {
                            if matches!(
                                m.member_type,
                                MemberType::Tension | MemberType::Compression
                            ) {
                                let assembly_context = AssemblyContext::new(self);
                                let n = m.calculate_axial_force_3d(
                                    &u_full,
                                    &assembly_context.material_by_id,
                                    &assembly_context.section_by_id,
                                );
                                let is_on = *active_map.get(&m.id).unwrap_or(&true);
                                eprintln!(
                                    "[combination] tie/strut id={} N={:.2} N   active={}",
                                    m.id, n, is_on
                                );
                            }
                        }
                    }
                }
            }

            // Relative convergence on displacement increment
            let u_norm = u_full.norm().max(1.0);
            if (delta.norm() / u_norm) < REL_DU_TOL && !changed {
                converged = true;
                break;
            }

            // Keep older absolute tolerance as a fallback if user set it tighter
            if delta.norm() < tolerance && !changed {
                converged = true;
                break;
            }
        }

        if !converged {
            return Err(format!(
                "Active-set iteration did not converge within {} iterations",
                max_it
            ));
        }

        let reactivated = self.update_active_set(
            &u_full,
            &mut active_map,
            axial_slack_tolerance,
            &assembly_context.material_by_id,
            &assembly_context.section_by_id,
            true, // allow reactivation exactly once here
        );

        if reactivated {
            let k_full = self.build_operator_with_supports(&active_map, None)?;
            let (mut k_red, mut f_red) = Self::reduce_system(&k_full, &load_vector_full, &elim);
            self.apply_boundary_conditions_reduced(&elim, &mut k_red, &mut f_red)?;
            let u_red = k_red.lu().solve(&f_red).ok_or_else(|| {
                "Reduced stiffness matrix is singular after reactivation pass.".to_string()
            })?;
            u_full = Self::expand_solution(&elim, &u_red);
        }

        // --- STRICT FINALIZATION (no compression in ties / no tension in struts) ---
        if self.finalize_tie_strut_consistency(
            &u_full,
            &mut active_map,
            &assembly_context.material_by_id,
            &assembly_context.section_by_id,
        ) {
            // Re-solve once with frozen active_map (no active-set updates here)
            let k_full = self.build_operator_with_supports(&active_map, None)?;
            let (mut k_red, mut f_red) = Self::reduce_system(&k_full, &load_vector_full, &elim);
            self.apply_boundary_conditions_reduced(&elim, &mut k_red, &mut f_red)?;
            let u_red = k_red.lu().solve(&f_red).ok_or_else(|| {
                "Reduced stiffness matrix is singular or near-singular in finalization.".to_string()
            })?;
            u_full = Self::expand_solution(&elim, &u_red);
        }

        // ---------------------------
        // Build reactions including MPCs
        // ---------------------------
        let r_support = compose_support_reaction_vector_equilibrium(
            self,
            &result_type,      // result type you're solving
            &u_full,           // final full displacement vector
            Some(&active_map), // ties/struts respect active set
        )?;

        // Store masked reactions (optional debug)
        let mut sum_rx = 0.0;
        let mut sum_ry = 0.0;
        let mut sum_rz = 0.0;
        for (i, val) in r_support.iter().enumerate() {
            match i % 6 {
                0 => sum_rx += val,
                1 => sum_ry += val,
                2 => sum_rz += val,
                _ => {}
            }
        }

        let mut sum_fx = 0.0;
        let mut sum_fy = 0.0;
        let mut sum_fz = 0.0;
        for (i, val) in load_vector_full.iter().enumerate() {
            match i % 6 {
                0 => sum_fx += val,
                1 => sum_fy += val,
                2 => sum_fz += val,
                _ => {}
            }
        }

        let results = self
            .build_and_store_results(
                name.clone(),
                result_type.clone(),
                &u_full,
                &r_support,
                Some(&active_map),
            )?
            .clone();

        Ok(results)
    }

    fn solve_second_order_common(
        &mut self,
        load_vector_full: nalgebra::DMatrix<f64>,
        name: String,
        result_type: ResultType,
        max_iterations: usize,
        initial_u_full: Option<nalgebra::DMatrix<f64>>,
        initial_active_map: Option<std::collections::HashMap<u32, bool>>,
    ) -> Result<Results, String> {
        use nalgebra::DMatrix;

        let assembly_context: AssemblyContext<'_> = AssemblyContext::new(self);
        let elim = self.build_rigid_elimination_partial_using_hinges()?;

        // Precompute (Sᵀ S)⁻¹ once for robust full→reduced projection
        let st_s = elim.s.transpose() * &elim.s;
        let st_s_inv = st_s
            .clone()
            .cholesky()
            .map(|c| c.inverse())
            .or_else(|| st_s.lu().try_inverse())
            .ok_or_else(|| {
                "SᵀS is singular; check rigid MPC topology (cycles/duplicates).".to_string()
            })?;

        // ---- Initialize state (warm or cold) ----
        // Active map: from warm start if provided, else default
        let mut active_map = initial_active_map.unwrap_or_else(|| self.init_active_map_tie_comp());

        // Reduced displacement:
        let mut u_red = if let Some(u0_full) = initial_u_full.as_ref() {
            // project given full-space warm start into reduced coordinates
            &st_s_inv * (&elim.s.transpose() * u0_full)
        } else {
            DMatrix::<f64>::zeros(elim.s.ncols(), 1)
        };

        let mut u_full = FERS::expand_solution(&elim, &u_red);

        // If no explicit warm start was provided, fall back to the old predictor logic
        if initial_u_full.is_none() {
            if let Ok((u_pred_full, act_pred)) = self.first_order_predictor_state(&load_vector_full)
            {
                let u_pred_red = &st_s_inv * (&elim.s.transpose() * &u_pred_full);
                u_red = u_pred_red.clone();
                u_full = FERS::expand_solution(&elim, &u_red);
                active_map = act_pred;
            }
        }

        let tol_res: f64 = self.settings.analysis_options.tolerance.max(1.0e-6);
        let axial_slack_tolerance: f64 = self.axial_slack_tolerance();

        let mut n_steps = LOAD_STEPS_DEFAULT.max(2);
        if matches!(result_type, ResultType::Loadcombination(_)) {
            n_steps = n_steps.max(8);
        }

        let max_substeps: usize = 4;
        const ALPHA_MIN: f64 = 1.0 / 2048.0;
        let mut substep_multiplier: usize = 1;
        const MAX_ACTIVE_OUTER: usize = 8;

        'outer_load: loop {
            for step in 1..=n_steps * substep_multiplier {
                let lambda = step as f64 / (n_steps * substep_multiplier) as f64;
                let f_lambda_full = &load_vector_full * lambda;

                // Save state for rollback
                let u_red_before_step = u_red.clone();
                let u_full_before_step = u_full.clone();
                let mut step_finished = false;

                for _outer in 0..MAX_ACTIVE_OUTER {
                    let mut converged_step = false;

                    'newton: for _iter in 0..max_iterations {
                        // Tangent in FULL at current state (material + geometric + springs)
                        let k_tangent_full =
                            self.build_operator_with_supports(&active_map, Some(&u_full))?;
                        // Reduce once
                        let (mut k_red, mut f_red) =
                            Self::reduce_system(&k_tangent_full, &f_lambda_full, &elim);
                        self.apply_boundary_conditions_reduced(&elim, &mut k_red, &mut f_red)?;

                        // Residual in REDUCED space at current u_red
                        let r_red = &k_red * &u_red - &f_red;
                        let rhs_norm = f_red.norm().max(1.0);
                        let res_now = r_red.norm() / rhs_norm;
                        if res_now < tol_res {
                            converged_step = true;
                            break 'newton;
                        }

                        // Solve for Δu_red
                        let delta_red_raw = if let Some(x) = k_red.clone().lu().solve(&(-&r_red)) {
                            x
                        } else {
                            // LM damping retries on a fresh damped copy
                            let mut damp = 1.0e-6;
                            let max_diag = (0..k_red.nrows())
                                .map(|i| k_red[(i, i)].abs())
                                .fold(0.0, f64::max)
                                .max(1.0);
                            let mut solved = None;
                            for _ in 0..4 {
                                let mut k_damped = k_red.clone();
                                for i in 0..k_damped.nrows() {
                                    k_damped[(i, i)] += damp * max_diag;
                                }
                                if let Some(x) = k_damped.lu().solve(&(-&r_red)) {
                                    solved = Some(x);
                                    break;
                                }
                                damp *= 10.0;
                            }
                            match solved {
                                Some(x) => x,
                                None => {
                                    if substep_multiplier < (1 << max_substeps) {
                                        substep_multiplier *= 2;
                                        log::debug!(
                                            "  tangent singular ⇒ substep multiplier -> {}",
                                            substep_multiplier
                                        );
                                        continue 'outer_load;
                                    } else {
                                        return Err(
                                            "Second-order: tangent singular even after LM damping + max substepping"
                                                .into(),
                                        );
                                    }
                                }
                            }
                        };

                        // Backtracking Armijo line search (residual-based)
                        let mut alpha = 1.0_f64;
                        const C_ARM: f64 = 1.0e-2;

                        let trial_res = |u_trial_red: &DMatrix<f64>| -> Result<f64, String> {
                            let u_full_trial = FERS::expand_solution(&elim, u_trial_red);
                            let k_full2 = self
                                .build_operator_with_supports(&active_map, Some(&u_full_trial))?;
                            let (mut k_red2, mut f_red2) =
                                Self::reduce_system(&k_full2, &f_lambda_full, &elim);
                            self.apply_boundary_conditions_reduced(
                                &elim,
                                &mut k_red2,
                                &mut f_red2,
                            )?;
                            let r2 = &k_red2 * u_trial_red - &f_red2;
                            Ok(r2.norm() / f_red2.norm().max(1.0))
                        };

                        let mut u_red_trial = &u_red + &(alpha * &delta_red_raw);
                        let mut res_trial = trial_res(&u_red_trial)?;
                        while res_trial > (1.0 - C_ARM * alpha) * res_now && alpha > ALPHA_MIN {
                            alpha *= 0.5;
                            u_red_trial = &u_red + &(alpha * &delta_red_raw);
                            res_trial = trial_res(&u_red_trial)?;
                        }

                        if res_trial > res_now && alpha <= ALPHA_MIN {
                            // Try flip-left once; otherwise substep
                            let u_red_trial_flip = &u_red - &(alpha * &delta_red_raw);
                            let res_flip = trial_res(&u_red_trial_flip)?;

                            if res_flip <= (1.0 - C_ARM * alpha) * res_now {
                                u_red_trial = u_red_trial_flip;
                            } else if substep_multiplier < (1 << max_substeps) {
                                substep_multiplier *= 2;
                                log::debug!(
                                    "  line-search failed at αmin → substep multiplier -> {}",
                                    substep_multiplier
                                );
                                continue 'outer_load;
                            } else {
                                return Err(
            "Second-order: non-descent at αmin; flip-left failed; max substepping reached"
                .into(),
        );
                            }
                        }

                        // Accept update
                        let delta_red = &u_red_trial - &u_red;
                        let du_rel = delta_red.norm() / u_red.norm().max(1.0);
                        u_red = u_red_trial;
                        u_full = FERS::expand_solution(&elim, &u_red);

                        // Active-set update (deactivation inside Newton)
                        let changed = self.update_active_set(
                            &u_full,
                            &mut active_map,
                            axial_slack_tolerance,
                            &assembly_context.material_by_id,
                            &assembly_context.section_by_id,
                            false,
                        );
                        if changed {
                            continue 'newton;
                        }

                        if res_now < tol_res || du_rel < 1.0e-4 {
                            converged_step = true;
                            break 'newton;
                        }
                    } // newton

                    if !converged_step {
                        // rollback & refine substeps
                        u_red = u_red_before_step.clone();
                        u_full = u_full_before_step.clone();
                        if substep_multiplier < (1 << max_substeps) {
                            substep_multiplier *= 2;
                            log::debug!(
                                "  step {}/{} failed ⇒ refining substeps to {}",
                                step,
                                n_steps * (substep_multiplier / 2),
                                n_steps * substep_multiplier
                            );
                            continue 'outer_load;
                        } else {
                            return Err(format!(
                            "Second-order: step {}/{} did not converge and max substepping reached",
                            step,
                            n_steps * substep_multiplier
                        ));
                        }
                    }

                    // Post-convergence reactivation
                    let reactivated = self.update_active_set(
                        &u_full,
                        &mut active_map,
                        axial_slack_tolerance,
                        &assembly_context.material_by_id,
                        &assembly_context.section_by_id,
                        true,
                    );
                    if reactivated {
                        log::debug!("  post-convergence reactivation → repeating current substep");
                        continue;
                    }

                    step_finished = true;
                    break;
                } // outer

                if !step_finished {
                    u_red = u_red_before_step;
                    u_full = u_full_before_step;
                    if substep_multiplier < (1 << max_substeps) {
                        substep_multiplier *= 2;
                        log::debug!(
                        "  step {}/{}: active-set outer loop hit limit ⇒ refining substeps to {}",
                        step,
                        n_steps * (substep_multiplier / 2),
                        n_steps * substep_multiplier
                    );
                        continue 'outer_load;
                    } else {
                        return Err(format!(
                        "Second-order: step {}/{} active-set outer loop did not converge; max substepping reached",
                        step,
                        n_steps * substep_multiplier
                    ));
                    }
                }
            } // steps

            break 'outer_load;
        }

        // Final strict tie/strut consistency + one linear re-solve
        if self.finalize_tie_strut_consistency(
            &u_full,
            &mut active_map,
            &assembly_context.material_by_id,
            &assembly_context.section_by_id,
        ) {
            let k_full = self.build_operator_with_supports(&active_map, None)?;
            let (mut k_red, mut f_red) = Self::reduce_system(&k_full, &load_vector_full, &elim);
            self.apply_boundary_conditions_reduced(&elim, &mut k_red, &mut f_red)?;
            let u_red_final = k_red
                .lu()
                .solve(&f_red)
                .ok_or_else(|| "Reduced stiffness singular in finalization.".to_string())?;
            u_full = FERS::expand_solution(&elim, &u_red_final);
        }

        let r_support = compose_support_reaction_vector_equilibrium(
            self,
            &result_type,
            &u_full,
            Some(&active_map),
        )?;
        let results = self
            .build_and_store_results(
                name.clone(),
                result_type.clone(),
                &u_full,
                &r_support,
                Some(&active_map),
            )?
            .clone();
        Ok(results)
    }

    pub fn solve_for_load_case(&mut self, load_case_id: u32) -> Result<Results, String> {
        let load_vector = self.assemble_load_vector_for_case(load_case_id);
        let load_case = self
            .load_cases
            .iter()
            .find(|lc| lc.id == load_case_id)
            .ok_or_else(|| format!("LoadCase {} not found.", load_case_id))?;
        let res_si = self.solve_first_order_common(
            load_vector,
            load_case.name.clone(),
            ResultType::Loadcase(load_case_id),
        )?;
        Ok(res_si)
    }

    pub fn solve_for_load_case_second_order(
        &mut self,
        load_case_id: u32,
        max_iterations: usize,
    ) -> Result<Results, String> {
        let load_vector = self.assemble_load_vector_for_case(load_case_id);
        let load_case = self
            .load_cases
            .iter()
            .find(|lc| lc.id == load_case_id)
            .ok_or_else(|| format!("LoadCase {} not found.", load_case_id))?;

        let res_si = self.solve_second_order_common(
            load_vector,
            load_case.name.clone(),
            ResultType::Loadcase(load_case_id),
            max_iterations,
            None,
            None,
        )?;
        Ok(res_si)
    }

    fn pack_displacement_vector_from_saved_case(
        &self,
        case_name: &str,
    ) -> Option<nalgebra::DMatrix<f64>> {
        use nalgebra::DMatrix;
        let num_dofs = crate::functions::geometry::compute_num_dofs_from_members(&self.member_sets);
        let mut u = DMatrix::<f64>::zeros(num_dofs, 1);
        let bundle = self.results.as_ref()?;
        let res = bundle.loadcases.get(case_name)?;
        for (node_id, d) in &res.displacement_nodes {
            let base = ((*node_id as usize) - 1) * 6;
            u[(base + 0, 0)] = d.dx;
            u[(base + 1, 0)] = d.dy;
            u[(base + 2, 0)] = d.dz;
            u[(base + 3, 0)] = d.rx;
            u[(base + 4, 0)] = d.ry;
            u[(base + 5, 0)] = d.rz;
        }
        Some(u)
    }

    fn build_combination_displacement_predictor(
        &self,
        combination_id: u32,
    ) -> Option<nalgebra::DMatrix<f64>> {
        use nalgebra::DMatrix;
        let combo = self
            .load_combinations
            .iter()
            .find(|c| c.id == combination_id)?;
        let mut u_pred = DMatrix::<f64>::zeros(
            crate::functions::geometry::compute_num_dofs_from_members(&self.member_sets),
            1,
        );
        for (case_id, factor) in &combo.load_cases_factors {
            let lc = self.load_cases.iter().find(|lc| lc.id == *case_id)?;
            let u_case = self.pack_displacement_vector_from_saved_case(&lc.name)?;
            u_pred += u_case * *factor;
        }
        Some(u_pred)
    }

    /// Build an initial active map for Tension/Compression members from a trial displacement.
    fn active_map_from_trial_displacement(
        &self,
        trial_u_full: &nalgebra::DMatrix<f64>,
    ) -> std::collections::HashMap<u32, bool> {
        use crate::models::members::enums::MemberType;
        use std::collections::HashMap;

        let assembly_context = AssemblyContext::new(self);
        let mut active_map: HashMap<u32, bool> = HashMap::new();
        let tol = self.axial_slack_tolerance();

        for member_set in &self.member_sets {
            for member in &member_set.members {
                match member.member_type {
                    MemberType::Tension => {
                        let n = member.calculate_axial_force_3d(
                            trial_u_full,
                            &assembly_context.material_by_id,
                            &assembly_context.section_by_id,
                        );
                        // Start ACTIVE unless clearly in compression (below -tol).
                        active_map.insert(member.id, n >= -tol);
                    }
                    MemberType::Compression => {
                        let n = member.calculate_axial_force_3d(
                            trial_u_full,
                            &assembly_context.material_by_id,
                            &assembly_context.section_by_id,
                        );
                        // Start ACTIVE unless clearly in tension (above +tol).
                        active_map.insert(member.id, n <= tol);
                    }
                    _ => {}
                }
            }
        }
        active_map
    }

    fn solve_first_order_common_warm(
        &mut self,
        load_vector_full: nalgebra::DMatrix<f64>,
        name: String,
        result_type: ResultType,
        initial_u_full: Option<nalgebra::DMatrix<f64>>,
        initial_active_map: Option<std::collections::HashMap<u32, bool>>,
    ) -> Result<Results, String> {
        use nalgebra::DMatrix;

        let tolerance: f64 = self.settings.analysis_options.tolerance;
        let max_it: usize = self.settings.analysis_options.max_iterations.unwrap_or(20) as usize;

        // Seed from warm start if provided
        let mut active_map = initial_active_map.unwrap_or_else(|| self.init_active_map_tie_comp());
        let mut u_full = initial_u_full.unwrap_or_else(|| {
            DMatrix::<f64>::zeros(
                crate::functions::geometry::compute_num_dofs_from_members(&self.member_sets),
                1,
            )
        });

        let assembly_context = AssemblyContext::new(self);
        let elim = self.build_rigid_elimination_partial_using_hinges()?;
        let axial_slack_tolerance: f64 = self.axial_slack_tolerance();

        let mut converged = false;
        for _iter in 0..max_it {
            let k_full = self.build_operator_with_supports(&active_map, None)?;
            let (mut k_red, mut f_red) = Self::reduce_system(&k_full, &load_vector_full, &elim);
            self.apply_boundary_conditions_reduced(&elim, &mut k_red, &mut f_red)?;

            // Solve and expand
            let u_red = k_red.lu().solve(&f_red).ok_or_else(|| {
                "Reduced stiffness matrix is singular or near-singular".to_string()
            })?;
            let u_full_new = Self::expand_solution(&elim, &u_red);
            let delta = &u_full_new - &u_full;
            u_full = u_full_new;
            let allow_reactivation_in_loop = !matches!(result_type, ResultType::Loadcombination(_));
            // One active-set update
            let changed = self.update_active_set(
                &u_full,
                &mut active_map,
                axial_slack_tolerance,
                &assembly_context.material_by_id,
                &assembly_context.section_by_id,
                allow_reactivation_in_loop,
            );

            let u_norm = u_full.norm().max(1.0);
            if !changed && (delta.norm() / u_norm) < REL_DU_TOL {
                converged = true;
                break;
            }
            if !changed && delta.norm() < tolerance {
                converged = true;
                break;
            }
        }

        if !converged {
            return Err(format!(
                "Active-set iteration did not converge within {} iterations",
                max_it
            ));
        }

        let reactivated = self.update_active_set(
            &u_full,
            &mut active_map,
            axial_slack_tolerance,
            &assembly_context.material_by_id,
            &assembly_context.section_by_id,
            true, // allow reactivation exactly once here
        );

        if reactivated {
            let k_full = self.build_operator_with_supports(&active_map, None)?;
            let (mut k_red, mut f_red) = Self::reduce_system(&k_full, &load_vector_full, &elim);
            self.apply_boundary_conditions_reduced(&elim, &mut k_red, &mut f_red)?;
            let u_red = k_red.lu().solve(&f_red).ok_or_else(|| {
                "Reduced stiffness matrix is singular after reactivation pass.".to_string()
            })?;
            u_full = Self::expand_solution(&elim, &u_red);
        }

        // Strict finalization and reactions (unchanged)
        if self.finalize_tie_strut_consistency(
            &u_full,
            &mut active_map,
            &assembly_context.material_by_id,
            &assembly_context.section_by_id,
        ) {
            let k_full = self.build_operator_with_supports(&active_map, None)?;
            let (mut k_red, mut f_red) = Self::reduce_system(&k_full, &load_vector_full, &elim);
            self.apply_boundary_conditions_reduced(&elim, &mut k_red, &mut f_red)?;
            let u_red = k_red.lu().solve(&f_red).ok_or_else(|| {
                "Reduced stiffness matrix is singular or near-singular in finalization.".to_string()
            })?;
            u_full = Self::expand_solution(&elim, &u_red);
        }

        let r_support = compose_support_reaction_vector_equilibrium(
            self,
            &result_type,
            &u_full,
            Some(&active_map),
        )?;

        let results = self
            .build_and_store_results(
                name.clone(),
                result_type.clone(),
                &u_full,
                &r_support,
                Some(&active_map),
            )?
            .clone();

        Ok(results)
    }

    pub fn solve_for_load_combination(&mut self, combination_id: u32) -> Result<Results, String> {
        use crate::models::results::results::ResultType;

        // 1) Unit factors for scaling displacements user -> SI and back
        let uf = self.unit_factors();

        // 2) Work on a cloned, normalized model in SI

        // 3) Assemble combination load vector in SI
        let load_vector = self.assemble_load_vector_for_combination(combination_id)?;
        let combo = self
            .load_combinations
            .iter()
            .find(|lc| lc.id == combination_id)
            .ok_or_else(|| format!("LoadCombination {} not found.", combination_id))?;

        // 4) Warm-start attempt:
        //    Build predictor from existing (user-unit) load case results on *self*
        let warm_user = self.build_combination_displacement_predictor(combination_id);

        let (initial_u_full, initial_active_map) = if let Some(mut u_user) = warm_user {
            // Scale translations to SI; rotations remain as-is (assumed radians)
            for i in (0..u_user.nrows()).step_by(6) {
                u_user[(i + 0, 0)] *= uf.l;
                u_user[(i + 1, 0)] *= uf.l;
                u_user[(i + 2, 0)] *= uf.l;
            }
            // Build active-map guess based on that trial state (now in SI)
            let active = self.active_map_from_trial_displacement(&u_user);
            (Some(u_user), Some(active))
        } else {
            (None, None)
        };

        // 5) Solve first-order for the combination (warm if possible)
        let res_si = if initial_u_full.is_some() {
            self.solve_first_order_common_warm(
                load_vector,
                combo.name.clone(),
                ResultType::Loadcombination(combination_id),
                initial_u_full,
                initial_active_map,
            )?
        } else {
            self.solve_first_order_common(
                load_vector,
                combo.name.clone(),
                ResultType::Loadcombination(combination_id),
            )?
        };
        Ok(res_si)
    }

    pub fn solve_for_load_combination_second_order(
        &mut self,
        combination_id: u32,
        max_iterations: usize,
    ) -> Result<Results, String> {
        let uf = self.unit_factors();

        // Work in normalized space

        let load_vector = self.assemble_load_vector_for_combination(combination_id)?;
        let combo = self
            .load_combinations
            .iter()
            .find(|lc| lc.id == combination_id)
            .ok_or_else(|| format!("LoadCombination {} not found.", combination_id))?;

        // Try build predictor from existing results (in *user units* on self)
        let warm_user = self.build_combination_displacement_predictor(combination_id);

        let (initial_u_full, initial_active_map) = if let Some(mut u_user) = warm_user {
            // Scale translations to SI (rotations untouched)
            for i in (0..u_user.nrows()).step_by(6) {
                u_user[(i + 0, 0)] *= uf.l;
                u_user[(i + 1, 0)] *= uf.l;
                u_user[(i + 2, 0)] *= uf.l;
            }
            let active = self.active_map_from_trial_displacement(&u_user);
            (Some(u_user), Some(active))
        } else {
            (None, None)
        };

        // Second-order solve with optional warm start
        let res_si = self.solve_second_order_common(
            load_vector,
            combo.name.clone(),
            ResultType::Loadcombination(combination_id),
            max_iterations,
            initial_u_full,
            initial_active_map,
        )?;
        Ok(res_si)
    }

    pub fn build_and_store_results(
        &mut self,
        name: String,
        result_type: ResultType,
        displacement_vector: &DMatrix<f64>,
        global_reaction_vector: &DMatrix<f64>,
        active_map: Option<&std::collections::HashMap<u32, bool>>,
    ) -> Result<&Results, String> {
        // 1) Element/member results
        let member_results = compute_member_results_from_displacement(
            self,
            &result_type,
            displacement_vector,
            active_map,
        );

        // 2) Node displacements
        let displacement_nodes = extract_displacements(self, displacement_vector);

        // 3) Reactions
        let reaction_nodes: BTreeMap<u32, crate::models::results::reaction::ReactionNodeResult> =
            extract_reaction_nodes(self, global_reaction_vector);

        // 4) Pack results & store
        let total_members: usize = self.member_sets.iter().map(|set| set.members.len()).sum();
        let total_supports: usize = self.nodal_supports.len();

        let results = Results {
            name: name.clone(),
            result_type: result_type.clone(),
            displacement_nodes,
            reaction_nodes,
            member_results,
            summary: ResultsSummary {
                total_displacements: total_members,
                total_reaction_forces: total_supports,
                total_member_forces: total_members,
            },
            unity_checks: None,
        };

        let bundle = self.results.get_or_insert_with(|| ResultsBundle {
            loadcases: BTreeMap::new(),
            loadcombinations: BTreeMap::new(),
            unity_checks_overview: None,
        });

        match result_type {
            ResultType::Loadcase(_) => {
                if bundle.loadcases.insert(name.clone(), results).is_some() {
                    return Err(format!("Duplicate load case name `{}`", name));
                }
                Ok(bundle.loadcases.get(&name).unwrap())
            }
            ResultType::Loadcombination(_) => {
                if bundle
                    .loadcombinations
                    .insert(name.clone(), results)
                    .is_some()
                {
                    return Err(format!("Duplicate load combination name `{}`", name));
                }
                Ok(bundle.loadcombinations.get(&name).unwrap())
            }
        }
    }

    pub fn save_results_to_json(fers_data: &FERS, file_path: &str) -> Result<(), std::io::Error> {
        let json = serde_json::to_string_pretty(fers_data)?;
        std::fs::write(file_path, json)
    }
}
