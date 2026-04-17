use sqlx::{Pool, Postgres};
use sqlx::postgres::PgArguments;
use crate::core::{PostgresJsonHolder, TableMapping};
use crate::impl_json;

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct Tracker {
    pub tracker_id: i64
}

impl PostgresJsonHolder for Tracker {
    fn table_name() -> String {
        "player_data.tracker_ids".to_string()
    }

    fn children() -> Vec<TableMapping> {
        vec![]
    }
}

impl Tracker {
    pub async fn get_all(pool: &Pool<Postgres>) -> Result<Vec<Tracker>, sqlx::Error> {
        get_items(&pool, "", PgArguments::default()).await
    }
}

impl_json!(Tracker);