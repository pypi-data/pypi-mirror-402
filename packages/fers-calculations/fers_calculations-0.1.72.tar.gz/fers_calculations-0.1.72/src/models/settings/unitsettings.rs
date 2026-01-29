use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

use crate::models::settings::unitenums::{DensityUnit, ForceUnit, LengthUnit, PressureUnit};

#[derive(Debug, Serialize, Deserialize, ToSchema, Clone)]
pub struct UnitSettings {
    #[serde(default = "default_system")]
    pub system: String,

    #[serde(default = "default_length_unit", rename = "lengthUnit")]
    pub length_unit: LengthUnit,

    #[serde(default = "default_force_unit", rename = "forceUnit")]
    pub force_unit: ForceUnit,

    #[serde(default = "default_density_unit", rename = "densityUnit")]
    pub density_unit: DensityUnit,

    #[serde(default = "default_pressure_unit", rename = "pressureUnit")]
    pub pressure_unit: PressureUnit,
}

fn default_system() -> String {
    "metric".to_string()
}
fn default_length_unit() -> LengthUnit {
    LengthUnit::M
}
fn default_force_unit() -> ForceUnit {
    ForceUnit::N
}
fn default_density_unit() -> DensityUnit {
    DensityUnit::KgPerM3
}
fn default_pressure_unit() -> PressureUnit {
    PressureUnit::Pa
}
impl Default for UnitSettings {
    fn default() -> Self {
        Self {
            system: default_system(),
            length_unit: default_length_unit(),
            force_unit: default_force_unit(),
            density_unit: default_density_unit(),
            pressure_unit: default_pressure_unit(),
        }
    }
}

impl UnitSettings {
    pub fn length_to_m(&self) -> f64 {
        self.length_unit.to_m()
    }

    pub fn force_to_n(&self) -> f64 {
        self.force_unit.to_n()
    }

    pub fn pressure_to_pa(&self) -> f64 {
        self.pressure_unit.to_pa()
    }

    pub fn density_to_kg_per_m3(&self) -> f64 {
        self.density_unit.to_kg_per_m3()
    }
}
