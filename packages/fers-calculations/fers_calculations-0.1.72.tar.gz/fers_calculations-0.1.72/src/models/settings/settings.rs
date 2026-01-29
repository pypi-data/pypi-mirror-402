use crate::models::settings::generalinfo::GeneralInfo;
use crate::models::settings::{analysissettings::AnalysisOptions, unitsettings::UnitSettings};
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[derive(Debug, Serialize, Deserialize, ToSchema, Clone)]

pub struct Settings {
    pub id: u32,
    pub analysis_options: AnalysisOptions,
    pub general_info: GeneralInfo,
    pub unit_settings: UnitSettings,
}
