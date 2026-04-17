use sqlx::Arguments;
use sqlx::{Pool, Postgres};
use sqlx::postgres::PgArguments;
use crate::core::{PostgresJsonHolder, TableMapping};
use crate::core::game::tier::Tier;
use crate::core::game::variant::Variant;
use crate::impl_json;

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct Multiplier {
    pub tier: Tier,
    pub variant: Variant,
    pub multiplier: i64
}

impl PostgresJsonHolder for Multiplier {
    fn table_name() -> String {
        "game_data.multipliers".to_string()
    }

    fn children() -> Vec<TableMapping> {
        vec![
            TableMapping {
                member_name: "tier".to_string(),
                gen_func: Tier::generate_sql,
                where_stmt: format!("WHERE {}.tier_name = {}.tier_name", Self::table_name(), Tier::table_name()),
            },
            TableMapping {
                member_name: "variant".to_string(),
                gen_func: Variant::generate_sql,
                where_stmt: format!("WHERE {}.variant_name = {}.variant_name", Self::table_name(), Variant::table_name()),
            }
        ]
    }
}

impl Multiplier {
    pub async fn get_all(pool: &Pool<Postgres>) -> Result<Vec<Multiplier>, sqlx::Error> {
        get_items(pool, "", PgArguments::default()).await
    }

    pub async fn from_tier_variant(pool: &Pool<Postgres>, tier_name: &str, variant_name: &str) -> Result<Multiplier, sqlx::Error> {
        let mut args = PgArguments::default();
        args.add(tier_name).unwrap();
        args.add(variant_name).unwrap();
        get_item(pool, &format!("WHERE {table}.tier_name = $1 AND {table}.variant_name = $2", table=Self::table_name()), args).await
    }
}

impl_json!(Multiplier);