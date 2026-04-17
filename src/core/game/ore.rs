use sqlx::Arguments;
use sqlx::{Pool, Postgres};
use sqlx::postgres::PgArguments;
use crate::core::game::tier::Tier;
use crate::core::{PostgresJsonHolder, TableMapping};
use crate::core::game::spawn::Spawn;
use crate::impl_json;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Ore {
    pub ore_name: String,
    pub tier: Tier,
    pub ore_alt_name: Option<String>
}

impl PostgresJsonHolder for Ore {
    fn table_name() -> String {
        "game_data.ores".to_string()
    }

    fn children() -> Vec<TableMapping> {
        vec![
            TableMapping {
                member_name: "tier".to_string(),
                gen_func: Tier::generate_sql,
                where_stmt: format!("WHERE {}.tier_name = {}.tier_name", Ore::table_name(), Tier::table_name()),
            }
        ]
    }
}

impl Ore {
    pub async fn get_all(pool: &Pool<Postgres>) -> Result<Vec<Ore>, sqlx::Error> {
        get_items(pool, "", PgArguments::default()).await
    }

    pub async fn from_name(pool: &Pool<Postgres>, name: &str) -> Result<Ore, sqlx::Error> {
        let mut args = PgArguments::default();
        args.add(name).unwrap();
        get_item(pool, &format!("WHERE ({table}.ore_name = $1 OR {table}.ore_alt_name = $1)", table=Self::table_name()), args).await
    }

    pub async fn spawns(&self, pool: &Pool<Postgres>) -> Result<Vec<Spawn>, sqlx::Error> {
        Spawn::from_ore(pool, &self.ore_name).await
    }
}

impl_json!(Ore);