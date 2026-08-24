use wasm_bindgen::prelude::*;

const G: f64 = 9.80665;

#[wasm_bindgen]
#[derive(Clone)]
pub struct TrainSim {
    s: f64, v: f64, a: f64, traction: u8, brake: u8,
    mass: f64, energy_used_j: f64, energy_regen_j: f64,
}

#[wasm_bindgen]
impl TrainSim {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self { Self { s: 0.0, v: 0.0, a: 0.0, traction: 0, brake: 0, mass: 290_000.0, energy_used_j: 0.0, energy_regen_j: 0.0 } }
    pub fn reset(&mut self) { *self = Self::new(); }
    pub fn set_controls(&mut self, traction: u8, brake: u8) { self.traction = traction.min(5); self.brake = brake.min(6); if self.brake > 0 { self.traction = 0; } }
    pub fn step(&mut self, dt: f64, gradient_permille: f64) {
        let dt = dt.clamp(0.0, 0.05);
        let max_force = 240_000.0 * self.traction as f64 / 5.0;
        let power_force = if self.v > 0.5 { 4_000_000.0 / self.v } else { max_force };
        let traction_force = max_force.min(power_force);
        let brake_force = if self.brake == 6 { self.mass * 1.25 } else { self.mass * 0.9 * self.brake as f64 / 5.0 };
        let resistance = 5_000.0 + 180.0 * self.v + 8.0 * self.v * self.v;
        let gradient_force = self.mass * G * gradient_permille / 1000.0;
        let net = traction_force - brake_force - resistance.min(self.v * self.mass / dt.max(0.001)) - gradient_force;
        self.a = net / self.mass;
        let old_v = self.v;
        self.v = (self.v + self.a * dt).max(0.0);
        self.s += (old_v + self.v) * 0.5 * dt;
        self.energy_used_j += traction_force * self.v * dt;
        if brake_force > 0.0 { self.energy_regen_j += brake_force * self.v * dt * 0.25; }
    }
    pub fn position(&self) -> f64 { self.s }
    pub fn speed(&self) -> f64 { self.v }
    pub fn acceleration(&self) -> f64 { self.a }
    pub fn energy_used_kwh(&self) -> f64 { self.energy_used_j / 3_600_000.0 }
    pub fn energy_regen_kwh(&self) -> f64 { self.energy_regen_j / 3_600_000.0 }
}

impl Default for TrainSim { fn default() -> Self { Self::new() } }

pub fn lv95_to_local(e: f64, n: f64, h: f64, origin: (f64,f64,f64)) -> (f64,f64,f64) { (e-origin.0, h-origin.2, -(n-origin.1)) }

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn coordinate_origin() { assert_eq!(lv95_to_local(2_600_010.,1_200_020.,510.,(2_600_000.,1_200_000.,500.)), (10.,10.,-20.)); }
    #[test] fn traction_accelerates() { let mut s=TrainSim::new(); s.set_controls(5,0); for _ in 0..120 { s.step(1./120.,0.); } assert!(s.speed()>0.5); }
    #[test] fn braking_decelerates() { let mut s=TrainSim::new(); s.set_controls(5,0); for _ in 0..1200{s.step(1./120.,0.)} let v=s.speed(); s.set_controls(0,5); for _ in 0..120{s.step(1./120.,0.)} assert!(s.speed()<v); }
    #[test] fn uphill_reduces_acceleration() { let mut a=TrainSim::new(); let mut b=TrainSim::new(); a.set_controls(5,0); b.set_controls(5,0); a.step(0.01,0.); b.step(0.01,20.); assert!(b.acceleration()<a.acceleration()); }
    #[test] fn deterministic() { let mut a=TrainSim::new(); let mut b=TrainSim::new(); a.set_controls(3,0); b.set_controls(3,0); for _ in 0..1000 { a.step(1./120.,7.); b.step(1./120.,7.); } assert_eq!(a.position(),b.position()); }
}
