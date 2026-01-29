use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[derive(Debug, Serialize, Deserialize, ToSchema, Clone)]
pub struct DistributedLoad {
    pub member: u32,
    pub load_case: u32,
    pub magnitude: f64,
    pub direction: (f64, f64, f64),
    pub start_frac: f64,
    pub end_frac: f64,
    pub end_magnitude: f64,
}
