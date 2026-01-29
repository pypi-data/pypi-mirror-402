use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

use crate::models::supports::supportconditiontype::SupportConditionType;

#[derive(Debug, Serialize, Deserialize, ToSchema, Clone)]
pub struct SupportCondition {
    pub condition_type: SupportConditionType,
    pub stiffness: Option<f64>,
}

impl SupportCondition {
    pub fn normalize_translation_units(&mut self, f: f64, l: f64) {
        if let Some(k) = &mut self.stiffness {
            *k *= f / l;
        }
    }

    pub fn normalize_rotation_units(&mut self, f: f64, l: f64) {
        if let Some(k) = &mut self.stiffness {
            *k *= f * l;
        }
    }
}
