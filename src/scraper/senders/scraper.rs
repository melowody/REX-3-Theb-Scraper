use std::sync::Arc;
use poise::async_trait;
use regex::Regex;
use serde_json::Value;
use sqlx::{Pool, Postgres};
use tokio::sync::mpsc::UnboundedSender;
use tokio_util::sync::CancellationToken;
use crate::core::game::cave::Cave;
use crate::core::game::ore::Ore;
use crate::core::game::variant::Variant;
use crate::core::game::world::World;
use crate::core::player::player::Player;
use crate::core::player::tracker::Tracker;
use crate::scraper::JsonSender;

struct TrackScraper {}

#[async_trait]
impl JsonSender for TrackScraper {

    async fn should_handle(&self, event: &Value, pool: Arc<Pool<Postgres>>) -> bool {
        if event.get("t").and_then(|v| v.as_str()) != Some("MESSAGE_CREATE") {
            return false;
        }

        let Some(id) = event["d"]["author"]["id"].as_i64() else { return false };

        Tracker::get_all(&pool)
            .await
            .expect("Coult not get trackers")
            .iter()
            .any(|t| t.tracker_id == id)
    }

    async fn handle_event(&mut self, event: &Value, pool: Arc<Pool<Postgres>>, send_queue: &mut UnboundedSender<Value>, cancel_token: CancellationToken) -> Result<(), String> {
        let title_re = Regex::new(r"^\*\*(.+?)\*\* has found\s?(?:an? (spectral|ionized)\s?)?\*\*\s?(.+?)\*\*(?: \(\*(.+?)\*\))?$").unwrap();
        let Some(title) = event["title"].as_str() else { return Err("Could not find title".to_string()) };
        let mut results = vec![];
        for (_, [path, lineno, line]) in title_re.captures(title).map(|c| c.extract()) {
            results.push((path, lineno.parse::<u64>().unwrap(), line));
        }

        let player_name = results.get(1).and_then(|i| Some(i.2));
        let player = if player_name.is_none() { return Err("Player doesn't exist in title!".to_string()) } else { Player::from_name(&pool, player_name.unwrap()).await.unwrap() };

        let variant_text = results.get(2).and_then(|i| Some(i.2));
        let variant = if variant_text.is_none() { return Err("Variant doesn't exist in the title!".to_string()) } else { Variant::from_name(&pool, variant_text.unwrap()).await.expect("Could not find variant") };

        let ore_text = results.get(3).and_then(|i| Some(i.2));
        let ore = if ore_text.is_none() { return Err("Ore doesn't exist in the title!".to_string()) } else { Ore::from_name(&pool, ore_text.unwrap()).await.expect("Could not find ore") };

        let Some(world_text) = event["description"].as_str() else { return Err("Could not find world".to_string()) };
        let world = World::from_name(&pool, world_text).await.expect("Could not find world");

        let cave_text = results.get(4).and_then(|i| Some(i.2));
        let cave = if cave_text.is_none() { None } else { Some(Cave::from_name(&pool, cave_text.unwrap()).await.expect("Could not find cave")) };

        Ok(())
    }

}