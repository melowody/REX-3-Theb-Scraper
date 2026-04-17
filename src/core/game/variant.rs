use sqlx::Arguments;
use sqlx::{Pool, Postgres};
use sqlx::postgres::PgArguments;
use struct_iterable::Iterable;
use crate::core::{PostgresJsonHolder, TableMapping};
use crate::impl_json;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Iterable)]
pub struct Variant {
    pub variant_name: String
}

impl PostgresJsonHolder for Variant {
    fn table_name() -> String {
        "game_data.variants".to_string()
    }

    fn children() -> Vec<TableMapping> {
        vec![]
    }
}

impl Variant {
    pub async fn get_all(pool: &Pool<Postgres>) -> Result<Vec<Variant>, sqlx::Error> {
        get_items(&pool, "", PgArguments::default()).await
    }

    pub async fn from_name(pool: &Pool<Postgres>, name: &str) -> Result<Variant, sqlx::Error> {
        let mut binds = PgArguments::default();
        binds.add(name).unwrap();
        get_item(&pool, &format!("WHERE {}.variant_name = $1", Variant::table_name()), binds).await
    }
}

impl_json!(Variant);