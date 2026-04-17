use std::sync::Arc;
use crate::bot::GooberBot;
use crate::db::get_pool;
use crate::scraper::GooberScraper;
use crate::scraper::senders::heartbeat::Heartbeat;

pub mod core;
pub mod db;
pub mod bot;
pub mod scraper;

#[tokio::main]
async fn main() {
    dotenvy::dotenv().ok();
    tracing_subscriber::fmt::init();

    let pool = get_pool().await;
    let pool_arc = Arc::new(pool.clone());

    let client = GooberBot::start(pool).await.expect("Error starting client!");

    loop {
        let scraper = GooberScraper::new(client.http.clone(), Arc::clone(&pool_arc), vec![
            Box::new(Heartbeat {})
        ]);

        scraper.start_loop().await.expect("Error starting scraper!");
    }

}
