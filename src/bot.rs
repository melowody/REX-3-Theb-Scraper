use std::sync::Arc;
use poise::{Framework, FrameworkOptions};
use serenity::all::GatewayIntents;
use serenity::{Client, Error};
use serenity::http::Http;
use sqlx::{Pool, Postgres};
use crate::bot::commands::epinephrine::epinephrine;
use crate::bot::commands::GooberData;
use crate::bot::commands::index::index;

pub mod commands;

pub struct GooberBot {
    pub http: Arc<Http>
}

impl GooberBot {
    pub async fn start(pool: Pool<Postgres>) -> Result<GooberBot, Error> {
        let token = std::env::var("BOT_TOKEN").unwrap();
        let intents = GatewayIntents::non_privileged()
            | GatewayIntents::MESSAGE_CONTENT;

        let framework = Framework::builder()
            .options(FrameworkOptions {
                commands: vec![
                    epinephrine(),
                    index()
                ],
                ..Default::default()
            })
            .setup(|ctx, _ready, framework| {
                Box::pin(async move {
                    poise::builtins::register_globally(ctx, &framework.options().commands).await?;
                    Ok(GooberData { pool })
                })
            })
            .build();

        let mut client = Client::builder(&token, intents)
            .framework(framework)
            .await
            .expect("Err creating client");

        let http = client.http.clone();

        tokio::spawn(async move {
            if let Err(why) = client.start().await {
                println!("Could not start client: {:?}", why);
            }
        });

        Ok(GooberBot {
            http
        })
    }
}