use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[derive(Debug, Serialize, Deserialize, ToSchema, Clone, Copy)]
#[serde(rename_all = "lowercase")]
pub enum LengthUnit {
    #[serde(rename = "mm")]
    Mm,
    #[serde(rename = "cm")]
    Cm,
    #[serde(rename = "m")]
    M,
}

impl LengthUnit {
    pub fn to_m(self) -> f64 {
        match self {
            LengthUnit::M => 1.0,
            LengthUnit::Cm => 0.01,
            LengthUnit::Mm => 0.001,
        }
    }
}
#[derive(Debug, Serialize, Deserialize, ToSchema, Clone, Copy)]
#[serde(rename_all = "lowercase")]
pub enum DensityUnit {
    #[serde(rename = "kg/m3")]
    KgPerM3,
    #[serde(rename = "kg/mm3")]
    KgPerMm3,
}

#[allow(non_camel_case_types)]
#[derive(Debug, Serialize, Deserialize, ToSchema, Clone, Copy)]
#[serde(rename_all = "lowercase")]
pub enum ForceUnit {
    #[serde(rename = "N", alias = "n")]
    N,
    #[serde(rename = "kN", alias = "kn")]
    kN,
}

impl ForceUnit {
    pub fn to_n(self) -> f64 {
        match self {
            ForceUnit::N => 1.0,
            ForceUnit::kN => 1000.0,
        }
    }
}

#[allow(non_camel_case_types)]
#[derive(Debug, Serialize, Deserialize, ToSchema, Clone, Copy)]
#[serde(rename_all = "lowercase")]
pub enum PressureUnit {
    #[serde(rename = "Pa", alias = "pa")]
    Pa,
    #[serde(rename = "kPa", alias = "kpa")]
    kPa,
    #[serde(rename = "MPa", alias = "mpa")]
    MPa,
    #[serde(rename = "GPa", alias = "gpa")]
    GPa,
}

impl PressureUnit {
    pub fn to_pa(self) -> f64 {
        match self {
            PressureUnit::Pa => 1.0,
            PressureUnit::kPa => 1.0e3,
            PressureUnit::MPa => 1.0e6,
            PressureUnit::GPa => 1.0e9,
        }
    }
}

impl DensityUnit {
    pub fn to_kg_per_m3(self) -> f64 {
        match self {
            DensityUnit::KgPerM3 => 1.0,
            DensityUnit::KgPerMm3 => 1.0e9, // 1 mm^3 = 1e-9 m^3
        }
    }
}
