use sqlx::Arguments;
use sqlx::{Pool, Postgres};
use sqlx::postgres::PgArguments;
use crate::core::game::ore::Ore;
use crate::core::game::world::World;
use crate::core::{PostgresJsonHolder, TableMapping};
use crate::impl_json;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Cave {
    pub cave_name: String,
    pub world: World,
    pub cave_ore: Ore,
    pub cave_rarity: i64
}

impl PostgresJsonHolder for Cave {
    fn table_name() -> String {
        "game_data.caves".to_string()
    }

    fn children() -> Vec<TableMapping> {
        vec![
            TableMapping {
                member_name: "world".to_string(),
                gen_func: World::generate_sql,
                where_stmt: format!("WHERE {}.world_name = {}.world_name", Cave::table_name(), World::table_name()),
            },
            TableMapping {
                member_name: "cave_ore".to_string(),
                gen_func: Ore::generate_sql,
                where_stmt: format!("WHERE {}.ore_name = {}.ore_name", Cave::table_name(), Ore::table_name()),
            }
        ]
    }
}

impl Cave {
    pub async fn get_all(pool: &Pool<Postgres>) -> Result<Vec<Cave>, sqlx::Error> {
        get_items(pool, "", PgArguments::default()).await
    }

    pub async fn from_name(pool: &Pool<Postgres>, name: &str) -> Result<Cave, sqlx::Error> {
        let mut args = PgArguments::default();
        args.add(name).unwrap();
        get_item(pool, &format!("WHERE {}.cave_name = $1", Self::table_name()), args).await
    }
}

impl_json!(Cave);