use std::error::Error;
use num_format::{Locale, ToFormattedString};
use crate::bot::commands::Context;
use rand::RngExt;
use crate::core::game::spawn::Spawn;

fn get_ore(roll: f64, spawns: Vec<Spawn>) -> String {
    let adjusted = (1_000_000_000. - roll) / 999_999_999.;
    let mut total: f64 = 0.;
    for spawn in spawns {
        if spawn.spawn_rarity == 0 {
            continue;
        }
        total += 1. / spawn.spawn_rarity as f64;
        if total >= adjusted {
            return format!("**{}**", spawn.ore.ore_name);
        }
    }
    "Moon Core".to_string()
}

/// Roll for Epinephrine!
#[poise::command(slash_command, prefix_command)]
pub async fn epinephrine(ctx: Context<'_>) -> Result<(), Box<dyn Error + Send + Sync>> {
    let roll: f64 = {
        let mut rng = rand::rng();
        rng.random_range(1.0..1_000_000_000.)
    };
    let floor_roll = roll.floor() as u32;

    let mut spawns = Spawn::from_loc(&ctx.data().pool, "Moon Core Layer", "Luna Refuge").await?;
    spawns.sort_by(|s1, s2| {s2.spawn_rarity.cmp(&s1.spawn_rarity)});

    let chosen_ore: String = get_ore(roll, spawns);

    match floor_roll {
        999_999_999 => {
            ctx.reply("YOU GOT EPINEPHRINE! @everyone\n(rolled 999,999,999)").await?;
        }
        1 => {
            ctx.reply("YOU GOT...as far away from Epinephrine as possible! @everyone\n(rolled 1)").await?;
        }
        _ => {
            ctx.reply(format!("You got {}!\n(got {} but needed 999,999,999)", chosen_ore, floor_roll.to_formatted_string(&Locale::en))).await?;
        }
    }

    Ok(())
}