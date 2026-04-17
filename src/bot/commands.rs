use poise::async_trait;
use serenity::all::CreateEmbed;
use sqlx::{Pool, Postgres};

pub mod epinephrine;
pub mod index;

pub struct GooberData {
    pub pool: Pool<Postgres>
}

type Error = Box<dyn std::error::Error + Send + Sync>;
type Context<'a> = poise::Context<'a, GooberData, Error>;

#[async_trait]
pub trait Paginator<T> {

    async fn make_page(&mut self, item: &T) -> Result<CreateEmbed, Error>;

    fn set_button_properties(&mut self);

    async fn start_loop(&mut self) -> Result<(), Error>;

}