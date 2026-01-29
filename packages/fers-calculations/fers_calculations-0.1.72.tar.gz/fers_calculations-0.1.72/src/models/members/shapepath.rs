use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

use crate::models::members::shapecommand::ShapeCommand;

#[derive(Serialize, Deserialize, ToSchema, Debug, Clone)]
pub struct ShapePath {
    pub id: u32,
    pub name: String,
    pub shape_commands: Vec<ShapeCommand>,
}

impl ShapePath {
    pub fn normalize_units(&mut self, length_factor: f64) {
        if (length_factor - 1.0).abs() <= 1.0e-12 {
            return;
        }

        for command in &mut self.shape_commands {
            command.normalize_units(length_factor);
        }
    }
}
