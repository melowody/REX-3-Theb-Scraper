pub mod senders;

use std::sync::Arc;
use tokio::sync::Mutex;
use poise::async_trait;
use poise::futures_util::{SinkExt, StreamExt};
use serde_json::Value;
use serenity::futures::stream::{SplitSink, SplitStream};
use serenity::http::Http;
use sqlx::{Pool, Postgres};
use tokio::net::TcpStream;
use tokio::sync::mpsc;
use tokio::sync::mpsc::{UnboundedReceiver, UnboundedSender};
use tokio::task::AbortHandle;
use tokio_tungstenite::{MaybeTlsStream, WebSocketStream};
use tokio_tungstenite::tungstenite::{Bytes, Message};
use tokio_util::sync::CancellationToken;

#[async_trait]
pub trait JsonSender: Send + Sync {

    async fn should_handle(&self, event: &Value, pool: Arc<Pool<Postgres>>) -> bool;

    async fn handle_event(&mut self,
                          event: &Value,
                          pool: Arc<Pool<Postgres>>,
                          send_queue: &mut UnboundedSender<Value>,
                          cancel_token: CancellationToken) -> Result<(), String>;

}

pub struct GooberScraper {
    senders: Vec<Box<dyn JsonSender + Send + Sync>>,
    http: Arc<Http>,
    tasks: Vec<AbortHandle>,
    pool: Arc<Pool<Postgres>>
}

impl GooberScraper {
    pub fn new(http: Arc<Http>, pool: Arc<Pool<Postgres>>, senders: Vec<Box<dyn JsonSender + Send + Sync>>) -> Self {
        GooberScraper { senders, http, tasks: vec![], pool }
    }

    pub async fn start_loop(mut self) -> Result<(), String> {
        let cancel_token = CancellationToken::new();
        let _guard = cancel_token.clone().drop_guard();

        let url = "wss://gateway.discord.gg/?v=10&encoding=json";

        let (ws_stream, response) = tokio_tungstenite::connect_async(url)
            .await
            .map_err(|err| format!("Error connecting to websocket: {:?}", err))?;

        let (write, read) = ws_stream.split();

        let (tx, rx) = mpsc::unbounded_channel::<Value>();

        let senders = Arc::new(Mutex::new(self.senders));
        let senders_clone = Arc::clone(&senders);
        let pool_clone = Arc::clone(&self.pool);
        let read_handle = tokio::spawn(async move {
            Self::read_loop(read, senders_clone, pool_clone, tx, cancel_token.clone()).await
        });

        let write_handle = tokio::spawn(async move {
            Self::write_loop(write, rx).await
        });

        self.tasks.push(read_handle.abort_handle());
        self.tasks.push(write_handle.abort_handle());
        let res = tokio::select! {
            res = read_handle => res,
            res = write_handle => res,
        };

        for handle in self.tasks.drain(..) {
            handle.abort();
        }

        res.map_err(|e| e.to_string())?
    }

    async fn read_loop(
        mut read: SplitStream<WebSocketStream<MaybeTlsStream<TcpStream>>>,
        senders: Arc<Mutex<Vec<Box<dyn JsonSender + Send + Sync>>>>,
        pool: Arc<Pool<Postgres>>,
        mut tx: UnboundedSender<Value>,
        cancellation_token: CancellationToken
    ) -> Result<(), String> {
        while let Some(msg_result) = read.next().await {
            let msg = msg_result.map_err(|e| format!("Error reading from websocket: {:?}", e))?;
            if msg.is_close() { break; }

            let text = match msg {
                Message::Text(t) => Bytes::from(t),
                Message::Binary(b) => b,
                _ => continue
            };

            println!("{:?}", text);

            let value_result = serde_json::from_slice::<Value>(&text.iter().as_slice());
            if let Err(e) = value_result {
                return Err(format!("Error deserializing json: {:?}", e));
            }

            let value: Value = value_result.unwrap();

            if let Some(7) = value.get("op").and_then(|v| v.as_u64()) {
                return Err("Received op 7".into());
            }

            for sender in senders.lock().await.iter_mut() {
                if sender.should_handle(&value, Arc::clone(&pool)).await {
                    sender.handle_event(&value, Arc::clone(&pool), &mut tx, cancellation_token.clone()).await.expect("Could not parse event");
                }
            }
        }
        Ok(())
    }

    async fn write_loop(mut write: SplitSink<WebSocketStream<MaybeTlsStream<TcpStream>>, Message>, mut rx: UnboundedReceiver<Value>) -> Result<(), String> {
        while let Some(value) = rx.recv().await {
            let json_str = value.to_string();
            write.send(Message::Text(json_str.into())).await.expect("Could not send message");
        }
        Ok(())
    }
}