use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[derive(Debug, Serialize, Deserialize, ToSchema, Clone)]
pub struct GeneralInfo {
    pub project_name: String,
    pub author: String,
    pub version: String,
}
