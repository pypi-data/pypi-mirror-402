use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

use crate::models::imperfections::rotationimperfection::RotationImperfection;
use crate::models::imperfections::translationimperfection::TranslationImperfection;

#[derive(Debug, Serialize, Deserialize, ToSchema, Clone)]
pub struct ImperfectionCase {
    pub imperfection_case_id: u32,
    pub load_combinations: Vec<u32>,
    pub rotation_imperfections: Vec<RotationImperfection>,
    pub translation_imperfections: Vec<TranslationImperfection>,
}
