use std::collections::{HashMap, VecDeque};
use std::sync::Arc;
use std::time::Duration;
use serde_json::{json, Error, Value};
use poise::async_trait;
use serde_json::Value::Null;
use serenity::http::Http;
use sqlx::{Pool, Postgres};
use tokio::sync::mpsc::UnboundedSender;
use tokio_util::sync::CancellationToken;
use crate::scraper::JsonSender;

pub struct Heartbeat {}

#[async_trait]
impl JsonSender for Heartbeat {

    async fn should_handle(&self, event: &Value, _: Arc<Pool<Postgres>>) -> bool {
        if let Some(d) = event.as_object() {
            return d.contains_key("heartbeat_interval");
        }
        false
    }

    async fn handle_event(&mut self, event: &Value, _: Arc<Pool<Postgres>>, send_queue: &mut UnboundedSender<Value>, cancellation_token: CancellationToken) -> Result<(), String> {
        let interval = event.as_object().unwrap().get("d").unwrap().as_object().unwrap().get("heartbeat_interval").unwrap().as_i64().unwrap();
        send_queue.send(json!({
            "op": 2,
            "d": {
                "token": std::env::var("SCRAPER_TOKEN").unwrap(),
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": "pc"
                }
            }
        })).expect("Failed to send op 2 message");

        let queue = send_queue.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_millis(interval as u64));
            loop {
                tokio::select! {
                    _ = cancellation_token.cancelled() => {
                        return;
                    }
                    _ = interval.tick() => {
                        loop {
                            if let Err(_) = queue.send(json!({"op": 1, "d": null})) {
                                break;
                            }
                        }
                    }
                }
            }
        });

        Ok(())
    }

}