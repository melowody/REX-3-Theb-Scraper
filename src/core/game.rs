use crate::core::game::cave::Cave;
use crate::core::game::layer::Layer;
use crate::core::game::ore::Ore;
use crate::core::game::world::World;

pub mod world;
pub mod tier;
pub mod ore;
pub mod layer;
pub mod cave;
pub mod variant;
pub mod multiplier;
pub mod spawn;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub enum Location {
    Cave(Cave),
    Layer(Layer)
}

impl Location {

    pub fn name(&self) -> String {
        match self {
            Location::Cave(cave) => cave.cave_name.clone(),
            Location::Layer(layer) => layer.layer_name.clone()
        }
    }

    pub fn world(&self) -> &World {
        match self {
            Location::Cave(cave) => &cave.world,
            Location::Layer(layer) => &layer.world
        }
    }

    pub fn ore(&self) -> &Ore {
        match self {
            Location::Cave(cave) => &cave.cave_ore,
            Location::Layer(layer) => &layer.layer_ore
        }
    }
    
    pub fn from(cave: Option<Cave>, layer: Option<Layer>) -> Location {
        if cave.is_some() { Location::Cave(cave.unwrap()) } else { Location::Layer(layer.unwrap()) }
    }

}