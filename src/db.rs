use sqlx::{Pool, Postgres};
use sqlx::postgres::PgPoolOptions;

pub async fn get_pool() -> Pool<Postgres> {
    let db_url = std::env::var("DB_URL").expect("DB_URL is not set");

    PgPoolOptions::new()
        .max_connections(5)
        .connect(&db_url)
        .await.expect("Could not open PgPool!")
}