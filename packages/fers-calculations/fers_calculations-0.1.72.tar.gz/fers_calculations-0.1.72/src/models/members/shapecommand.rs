use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[derive(Serialize, Deserialize, ToSchema, Debug, Clone)]
pub struct ShapeCommand {
    pub command: String,
    pub y: Option<f64>,
    pub z: Option<f64>,
    pub r: Option<f64>,
    pub control_y1: Option<f64>,
    pub control_z1: Option<f64>,
    pub control_y2: Option<f64>,
    pub control_z2: Option<f64>,
}

impl ShapeCommand {
    pub fn normalize_units(&mut self, length_factor: f64) {
        if (length_factor - 1.0).abs() <= 1.0e-12 {
            return;
        }

        if let Some(ref mut y) = self.y {
            *y *= length_factor;
        }
        if let Some(ref mut z) = self.z {
            *z *= length_factor;
        }
        if let Some(ref mut r) = self.r {
            *r *= length_factor;
        }
        if let Some(ref mut y1) = self.control_y1 {
            *y1 *= length_factor;
        }
        if let Some(ref mut z1) = self.control_z1 {
            *z1 *= length_factor;
        }
        if let Some(ref mut y2) = self.control_y2 {
            *y2 *= length_factor;
        }
        if let Some(ref mut z2) = self.control_z2 {
            *z2 *= length_factor;
        }
    }
}
