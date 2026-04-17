use chrono::{DateTime, Utc};
use sqlx::{Error, Pool, Postgres};
use sqlx::postgres::PgArguments;
use crate::core::game::Location;
use crate::core::game::ore::Ore;
use crate::core::game::variant::Variant;
use crate::core::player::player::Player;
use crate::core::{PostgresJsonHolder, TableMapping};
use crate::core::game::cave::Cave;
use crate::core::game::layer::Layer;
use crate::core::game::spawn::Spawn;
use crate::impl_json;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Track {
    player: Player,
    variant: Option<Variant>,
    ore: Ore,
    location: Location,
    blocks_mined: i64,
    find_date: DateTime<Utc>
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct Intermediate {
    player: Player,
    variant: Option<Variant>,
    ore: Ore,
    cave: Option<Cave>,
    layer: Option<Layer>,
    blocks_mined: i64,
    find_date: DateTime<Utc>
}

impl Intermediate {
    pub fn to_track(self) -> Track {
        Track {
            player: self.player,
            variant: self.variant,
            ore: self.ore,
            location: Location::from(self.cave, self.layer),
            blocks_mined: self.blocks_mined,
            find_date: self.find_date
        }
    }
}

impl PostgresJsonHolder for Intermediate {

    fn table_name() -> String {
        "player_data.tracks".to_string()
    }

    fn children() -> Vec<TableMapping> {
        vec![
            TableMapping {
                member_name: "player".to_string(),
                gen_func: Player::generate_sql,
                where_stmt: format!("WHERE {}.player_id = {}.player_id", Intermediate::table_name(), Player::table_name())
            },
            TableMapping {
                member_name: "variant".to_string(),
                gen_func: Variant::generate_sql,
                where_stmt: format!("WHERE {}.variant_name = {}.variant_name", Intermediate::table_name(), Variant::table_name())
            },
            TableMapping {
                member_name: "ore".to_string(),
                gen_func: Ore::generate_sql,
                where_stmt: format!("WHERE {}.ore_name = {}.ore_name", Intermediate::table_name(), Ore::table_name())
            },
            TableMapping {
                member_name: "cave".to_string(),
                gen_func: Cave::generate_sql,
                where_stmt: format!("WHERE {}.cave_name = {}.cave_name", Intermediate::table_name(), Cave::table_name())
            },
            TableMapping {
                member_name: "layer".to_string(),
                gen_func: Layer::generate_sql,
                where_stmt: format!("WHERE {}.layer_name = {}.layer_name", Intermediate::table_name(), Layer::table_name())
            }
        ]
    }

}

impl Track {
    async fn get_spawn(&self, pool: &Pool<Postgres>) -> Result<Spawn, Error> {
        Spawn::from_ore_loc(&pool, &self.ore.ore_name, &self.location.name(), &self.location.world().world_name).await
    }

    async fn get_all(pool: &Pool<Postgres>) -> Result<Vec<Track>, Error> {
        let items = get_items(pool, "", PgArguments::default()).await?;
        Ok(items.into_iter().map(|i| i.to_track()).collect())
    }
}

impl_json!(Intermediate);