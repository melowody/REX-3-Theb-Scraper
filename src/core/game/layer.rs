use sqlx::Arguments;
use sqlx::{Pool, Postgres};
use sqlx::postgres::PgArguments;
use crate::core::game::ore::Ore;
use crate::core::game::world::World;
use crate::core::{PostgresJsonHolder, TableMapping};
use crate::impl_json;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Layer {
    pub layer_name: String,
    pub world: World,
    pub layer_ore: Ore,
    pub layer_min_depth: i32,
    pub layer_max_depth: i32
}

impl PostgresJsonHolder for Layer {
    fn table_name() -> String {
        "game_data.layers".to_string()
    }

    fn children() -> Vec<TableMapping> {
        vec![
            TableMapping {
                member_name: "world".to_string(),
                gen_func: World::generate_sql,
                where_stmt: format!("WHERE {}.world_name = {}.world_name", Layer::table_name(), World::table_name()),
            },
            TableMapping {
                member_name: "layer_ore".to_string(),
                gen_func: Ore::generate_sql,
                where_stmt: format!("WHERE {}.ore_name = {}.ore_name", Layer::table_name(), Ore::table_name()),
            }
        ]
    }
}

impl Layer {
    pub async fn get_all(pool: &Pool<Postgres>) -> Result<Vec<Layer>, sqlx::Error> {
        get_items(pool, "", PgArguments::default()).await
    }

    pub async fn from_name(pool: &Pool<Postgres>, name: &str) -> Result<Layer, sqlx::Error> {
        let mut args = PgArguments::default();
        args.add(name).unwrap();
        get_item(pool, &format!("WHERE {}.layer_name = $1", Self::table_name()), args).await
    }
}

impl_json!(Layer);