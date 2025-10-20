do
$$
    begin
        create type tracker_type as enum ('global', 'player', 'beginner');
    exception
        when duplicate_object then null;
    end
$$;

do
$$
    begin
        create type equip_type as enum ('pickaxe', 'lhand', 'rhand', 'manual', 'artifact');
    exception
        when duplicate_object then null;
    end;
$$;

create table if not exists worlds
(
    world_id   text not null
        primary key,
    world_name text not null
        unique,
    world_desc text not null
);

create table if not exists tiers
(
    tier_id    text                  not null
        primary key,
    tier_name  text                  not null
        unique,
    tier_num   integer               not null
        unique,
    min_rarity bigint                not null,
    max_rarity bigint                not null,
    color      text default ''::text not null
);

create table if not exists ores
(
    ore_id   text not null
        primary key,
    ore_name text not null
        unique,
    tier_id  text not null
        references tiers,
    alt_name text
);

create table if not exists caves
(
    cave_id     text    not null
        primary key,
    ore_id      text    not null
        references ores,
    cave_name   text    not null
        unique,
    world_id    text    not null
        references worlds,
    cave_rarity integer not null
);

create table if not exists layers
(
    layer_id   text    not null
        primary key,
    ore_id     text    not null
        references ores,
    layer_name text    not null
        unique,
    world_id   text    not null
        references worlds,
    min_depth  integer not null,
    max_depth  integer not null
);

create table if not exists spawns
(
    ore_id   text   not null
        references ores,
    layer_id text
        references layers,
    cave_id  text
        references caves,
    rarity   bigint not null,
    constraint ore_spawn
        unique (ore_id, layer_id, cave_id)
);

create table if not exists guilds
(
    guild_id   bigint not null
        primary key,
    guild_name text   not null
);

create table if not exists channels
(
    channel_id   bigint       not null
        primary key,
    channel_type tracker_type not null,
    ping_role    bigint
);

create table if not exists players
(
    user_id     bigint not null
        primary key,
    player_name text   not null
        unique,
    guild_id    bigint
        references guilds,
    max_epi     integer,
    min_epi     integer
);

create table if not exists trackers
(
    tracker_id bigint not null
        primary key
);

create table if not exists equipment
(
    equip_id   text       not null
        primary key,
    equip_name text       not null,
    equip_desc text,
    equip_tier integer    not null,
    equip_type equip_type not null,
    world_id   text
        references worlds
);

create table if not exists abilities
(
    ability_id          text    not null
        primary key,
    equip_id            text    not null
        references equipment,
    ability_name        text    not null,
    ability_desc        text    not null,
    ability_rate        integer not null,
    ability_luck        text,
    ability_lifespan    text,
    ability_area        text,
    ability_amount      text,
    ability_pinned_luck text
);

create table if not exists events
(
    ore_id         text    not null
        primary key
        references ores,
    world_id       text    not null
        references worlds,
    event_text     text    not null,
    event_desc     text    not null,
    ore_rarity     integer not null,
    event_duration integer not null,
    event_chance   integer not null
);

create table if not exists variants
(
    variant_id   text    not null
        primary key,
    variant_name text    not null,
    variant_num  integer not null
        unique
);

create table if not exists recipes
(
    equip_id   text    not null
        references equipment,
    ore_id     text    not null
        references ores,
    count      numeric not null,
    variant_id text
        references variants,
    constraint recipe_step
        unique (equip_id, ore_id)
);

create table if not exists multipliers
(
    variant_id     text    not null
        references variants,
    tier_id        text    not null
        references tiers,
    multiplier_num integer not null,
    constraint multiplier
        unique (variant_id, tier_id)
);

create table if not exists tracks
(
    player_name  text   not null,
    ore_id       text   not null
        references ores,
    variant_id   text
        references variants,
    cave_id      text
        references caves,
    world_id     text   not null
        references worlds,
    blocks_mined bigint not null,
    event_id     text
        references events,
    equip_ids    text[],
    constraint track_key
        unique (player_name, blocks_mined)
);

