use sqlx::Arguments;
use sqlx::{Pool, Postgres};
use sqlx::postgres::PgArguments;
use crate::core::{PostgresJsonHolder, TableMapping};
use crate::impl_json;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct World {
    pub world_name: String,
    pub world_desc: String,
    pub world_alt_names: Vec<String>
}

impl PostgresJsonHolder for World {
    fn table_name() -> String {
        "game_data.worlds".to_string()
    }

    fn children() -> Vec<TableMapping> {
        vec![]
    }
}

impl World {
    pub async fn get_all(pool: &Pool<Postgres>) -> Result<Vec<World>, sqlx::Error> {
        get_items(pool, "", PgArguments::default()).await
    }

    pub async fn from_name(pool: &Pool<Postgres>, name: &str) -> Result<World, sqlx::Error> {
        let mut args = PgArguments::default();
        args.add(name).unwrap();
        get_item(pool, &format!("WHERE ({table}.world_name = $1 OR $1=ANY({table}.world_alt_names)", table=Self::table_name()), args).await
    }
}

impl_json!(World);