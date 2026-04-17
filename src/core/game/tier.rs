use sqlx::Arguments;
use sqlx::{Pool, Postgres};
use sqlx::postgres::PgArguments;
use crate::core::{PostgresJsonHolder, TableMapping};
use crate::impl_json;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Tier {
    pub tier_name: String,
    pub tier_min_rarity: i64,
    pub tier_max_rarity: i64,
    pub tier_color: i32
}

impl PostgresJsonHolder for Tier {
    fn table_name() -> String {
        "game_data.tiers".to_string()
    }

    fn children() -> Vec<TableMapping> {
        vec![]
    }
}

impl Tier {
    pub async fn get_all(pool: &Pool<Postgres>) -> Result<Vec<Tier>, sqlx::Error> {
        get_items(pool, "", PgArguments::default()).await
    }

    pub async fn from_name(pool: &Pool<Postgres>, name: &str) -> Result<Tier, sqlx::Error> {
        let mut args = PgArguments::default();
        args.add(name).unwrap();
        get_item(pool, &format!("WHERE {}.tier_name = $1", Self::table_name()), args).await
    }
}

impl_json!(Tier);