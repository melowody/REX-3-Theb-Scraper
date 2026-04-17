use sqlx::{Arguments, Pool, Postgres};
use sqlx::postgres::PgArguments;
use crate::core::game::Location;
use crate::core::game::ore::Ore;
use crate::core::{PostgresJsonHolder, TableMapping};
use crate::core::game::cave::Cave;
use crate::core::game::layer::Layer;
use crate::impl_json;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Spawn {
    pub ore: Ore,
    pub location: Location,
    pub spawn_rarity: i64
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct Intermediate {
    pub ore: Ore,
    pub cave: Option<Cave>,
    pub layer: Option<Layer>,
    pub spawn_rarity: i64
}

impl Intermediate {
    pub fn to_spawn(self) -> Spawn {
        Spawn {
            ore: self.ore,
            location: Location::from(self.cave, self.layer),
            spawn_rarity: self.spawn_rarity,
        }
    }
}

impl PostgresJsonHolder for Intermediate {
    fn table_name() -> String {
        "game_data.spawns".to_string()
    }

    fn children() -> Vec<TableMapping> {
        vec![
            TableMapping {
                member_name: "ore".to_string(),
                gen_func: Ore::generate_sql,
                where_stmt: format!("WHERE {}.ore_name = {}.ore_name", Ore::table_name(), Self::table_name())
            },
            TableMapping {
                member_name: "cave".to_string(),
                gen_func: Cave::generate_sql,
                where_stmt: format!("WHERE {cave}.cave_name = {spawn}.cave_name AND {cave}.world_name = {spawn}.world_name", cave=Cave::table_name(), spawn=Self::table_name())
            },
            TableMapping {
                member_name: "layer".to_string(),
                gen_func: Layer::generate_sql,
                where_stmt: format!("WHERE {layer}.layer_name = {spawn}.layer_name AND {layer}.world_name = {spawn}.world_name", layer=Layer::table_name(), spawn=Self::table_name())
            }
        ]
    }
}

impl Spawn {
    pub async fn from_ore_loc(pool: &Pool<Postgres>, ore_name: &str, loc_name: &str, world_name: &str) -> Result<Spawn, sqlx::Error> {
        let mut args = PgArguments::default();
        args.add(ore_name).unwrap();
        args.add(loc_name).unwrap();
        args.add(world_name).unwrap();
        let intermediate = get_item(pool, &format!("WHERE {table}.ore_name = $1 AND {table}.world_name = $3 AND ({table}.cave_name = $2 OR {table}.layer_name = $2)", table=Intermediate::table_name()), args).await?;
        Ok(intermediate.to_spawn())
    }

    pub async fn from_loc(pool: &Pool<Postgres>, loc_name: &str, world_name: &str) -> Result<Vec<Spawn>, sqlx::Error> {
        let mut args = PgArguments::default();
        args.add(loc_name).unwrap();
        args.add(world_name).unwrap();
        let intermediate = get_items(pool, &format!("WHERE {table}.world_name = $2 AND ({table}.cave_name = $1 OR {table}.layer_name = $1)", table=Intermediate::table_name()), args).await?;
        Ok(intermediate.into_iter().map(|item| { item.to_spawn() }).collect())
    }

    pub async fn from_ore(pool: &Pool<Postgres>, ore_name: &str) -> Result<Vec<Spawn>, sqlx::Error> {
        let mut args = PgArguments::default();
        args.add(ore_name).unwrap();
        let intermediate = get_items(pool, &format!("WHERE {table}.ore_name = $1", table=Intermediate::table_name()), args).await?;
        Ok(intermediate.into_iter().map(|item| { item.to_spawn() }).collect())
    }

    pub fn adjusted_rarity(&self) -> i64 {
        match &self.location {
            Location::Layer(_) => {
                self.spawn_rarity
            },
            Location::Cave(cave) => {
                (cave.cave_rarity as f64 * 1.88 * self.spawn_rarity as f64) as i64
            }
        }
    }
}

impl_json!(Intermediate);