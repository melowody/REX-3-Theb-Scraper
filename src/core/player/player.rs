use sqlx::Arguments;
use sqlx::{Error, Pool, Postgres};
use sqlx::postgres::PgArguments;
use crate::core::{PostgresJsonHolder, TableMapping};
use crate::core::game::variant::Variant;
use crate::impl_json;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Player {
    pub player_name: String,
    pub player_id: i64
}

impl PostgresJsonHolder for Player {
    fn table_name() -> String {
        "player_data.player_names".to_string()
    }

    fn children() -> Vec<TableMapping> {
        vec![]
    }
}

impl Player {

    pub async fn from_name(pool: &Pool<Postgres>, name: &str) -> Result<Player, Error> {
        let mut binds = PgArguments::default();
        binds.add(name).unwrap();
        get_item(&pool, &format!("WHERE {}.player_name = $1", Variant::table_name()), binds).await
    }

}

impl_json!(Player);