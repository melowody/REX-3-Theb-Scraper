use poise::serenity_prelude::CreateButton;
use std::collections::HashMap;
use std::time::Duration;
use num_format::{Locale, ToFormattedString};
use poise::{async_trait, CreateReply};
use serenity::all::{Color, ComponentInteractionCollector, CreateActionRow, CreateEmbed, CreateInteractionResponse, CreateInteractionResponseMessage};
use crate::bot::commands::{Context, Error, Paginator};
use crate::core::game::cave::Cave;
use crate::core::game::layer::Layer;
use crate::core::game::Location;
use crate::core::game::multiplier::Multiplier;
use crate::core::game::ore::Ore;
use crate::core::game::spawn::Spawn;
use crate::core::game::variant::Variant;

/// Get information about an item in the Index!
#[poise::command(slash_command, prefix_command, subcommand_required, subcommands("index_ore"))]
pub async fn index(_ctx: Context<'_>) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    Ok(())
}

struct OrePaginator<'a> {
    ctx: Context<'a>,
    multipliers: Vec<Multiplier>,
    spawns: Vec<Spawn>,
    embeds: HashMap<String, CreateEmbed>,
    buttons: Vec<CreateButton>
}

impl <'a> OrePaginator<'a> {

    async fn make_layer_page(&mut self, spawn: &Spawn, layer: &Layer) -> Result<CreateEmbed, Error> {
        let ore = &spawn.ore;

        let ctx_id = self.ctx.id();
        let button_id = format!("{}_layer", ctx_id);
        let mut embed = CreateEmbed::default()
            .color(Color::new(ore.tier.tier_color as u32))
            .title(format!("{} ({})", ore.ore_name, ore.tier.tier_name));

        if self.embeds.contains_key(&button_id) {
            return Ok(self.embeds.get(&button_id).unwrap().clone());
        }

        self.buttons.push(CreateButton::new(&button_id).label("Layer"));
        embed = embed
            .description(&layer.layer_name)
            .field("Base Rarity", spawn.spawn_rarity.to_formatted_string(&Locale::en), true);
        embed = self.apply_multipliers(spawn, &embed);

        let mut layers: Vec<&str> = vec![];
        for spawn in self.spawns.as_slice() {
            if let Location::Layer(layer) = &spawn.location {
                layers.push(&layer.layer_name);
            }
        }
        embed = embed.field("Layers", layers.join(", "), true);
        self.embeds.insert(button_id.clone(), embed.clone());

        Ok(embed)
    }

    async fn make_cave_page(&mut self, spawn: &Spawn, cave: &Cave) -> Result<CreateEmbed, Error> {
        let ore = &spawn.ore;

        let ctx_id = self.ctx.id();
        let button_id = format!("{}_{}", ctx_id, &cave.cave_name);
        let mut embed = CreateEmbed::default()
            .color(Color::new(ore.tier.tier_color as u32))
            .title(format!("{} ({})", ore.ore_name, ore.tier.tier_name));

        if self.embeds.contains_key(&button_id) {
            return Ok(self.embeds.get(&button_id).unwrap().clone());
        }

        self.buttons.push(CreateButton::new(&button_id).label(&cave.cave_name));
        embed = embed
            .description(&cave.cave_name)
            .field("Base Rarity", spawn.spawn_rarity.to_formatted_string(&Locale::en), true);

        embed = self.apply_multipliers(spawn, &embed);
        let rarity = spawn.adjusted_rarity();
        embed = embed.field("Adjusted Rarity", rarity.to_formatted_string(&Locale::en), true);
        for multiplier in self.multipliers.as_slice() {
            embed = embed.field(format!("Adjusted {} Rarity", multiplier.variant.variant_name), (rarity * multiplier.multiplier).to_formatted_string(&Locale::en), true);
        }

        self.embeds.insert(button_id.clone(), embed.clone());

        Ok(embed)
    }

    fn apply_multipliers(&mut self, spawn: &Spawn, embed: &CreateEmbed) -> CreateEmbed {
        let mut out = embed.clone();
        for multiplier in self.multipliers.as_slice() {
            out = out.field(format!("{} Rarity", multiplier.variant.variant_name), (multiplier.multiplier * spawn.spawn_rarity).to_formatted_string(&Locale::en), true);
        }
        out
    }

}

#[async_trait]
impl <'a> Paginator<Spawn> for OrePaginator<'a> {

    async fn make_page(&mut self, item: &Spawn) -> Result<CreateEmbed, Error> {
        match &item.location {
            Location::Layer(layer) => self.make_layer_page(item, layer).await,
            Location::Cave(cave) => self.make_cave_page(item, cave).await,
        }
    }

    fn set_button_properties(&mut self) {
        return;
    }

    async fn start_loop(&mut self) -> Result<(), Error> {

        for spawn in self.spawns.clone() {
            let _ = self.make_page(&spawn).await?;
        }

        let ctx_id = self.ctx.id();
        let display_embed = if self.embeds.contains_key(&format!("{}_layer", ctx_id)) {
            self.embeds.get(&format!("{}_layer", ctx_id)).unwrap()
        } else {
            self.embeds.get(self.embeds.keys().next().unwrap()).unwrap()
        };

        self.ctx.send(CreateReply::default().embed(display_embed.clone()).components(vec![CreateActionRow::Buttons(self.buttons.clone())])).await?;

        while let Some(press) = ComponentInteractionCollector::new(self.ctx)
            .filter(move |press| press.data.custom_id.starts_with(&ctx_id.to_string()))
            .timeout(Duration::from_secs(3600 * 24))
            .await
        {
            let button_id = press.data.custom_id.clone();

            if !self.embeds.contains_key(&button_id) {
                continue;
            }

            press.create_response(
                self.ctx.serenity_context(),
                CreateInteractionResponse::UpdateMessage(
                    CreateInteractionResponseMessage::new()
                        .embed(self.embeds.get(&button_id).unwrap().clone())
                )
            ).await?;
        }

        Ok(())
    }

}

/// Get information about an Ore!
#[poise::command(slash_command, prefix_command, rename="ore")]
pub async fn index_ore(ctx: Context<'_>, ore_name: String) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {

    let pool = &ctx.data().pool;
    let ore = Ore::from_name(pool, &ore_name).await?;
    let spawns = ore.spawns(pool).await?;
    let variants = Variant::get_all(&pool).await?;
    let mut multipliers: Vec<Multiplier> = vec![];

    for variant in variants.as_slice() {
        let multi = Multiplier::from_tier_variant(&pool, &ore.tier.tier_name, &variant.variant_name).await?;
        multipliers.push(multi);
    }

    OrePaginator {
        ctx,
        multipliers,
        spawns,
        embeds: HashMap::new(),
        buttons: vec![],
    }.start_loop().await?;

    Ok(())
}