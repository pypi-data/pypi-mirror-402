use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[derive(Debug, Serialize, Deserialize, ToSchema, Clone)]
pub struct TranslationImperfection {
    pub memberset_ids: Vec<usize>,
    pub magnitude: f64,
    pub axis: (f64, f64, f64),
}
