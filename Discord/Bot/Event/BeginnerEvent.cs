using Discord;
using Discord.Net;
using GooberTracker.Core.Types.Channel;
using GooberTracker.Core.Types.Ping;
using GooberTracker.Core.Types.Spawner;
using GooberTracker.Core.Types.Track;
using GooberTracker.Discord.Scraper;
using SmartFormat;
using ChannelType = GooberTracker.Core.Types.Channel.ChannelType;

namespace GooberTracker.Discord.Bot.Event;

public class BeginnerEvent(GooberBot bot, Track track) : EventTracker.Event(bot, track)
{
    protected override Task<List<Channel>> Channels => GetChannels();
    protected virtual Task<string> Title => Task.FromResult(":beginner:");

    private async Task<List<Channel>> GetChannels()
    {
        var channels = await ChannelManager.Instance.GetAll(ChannelType.Beginner);
        List<Channel> o = [];
        foreach (var channel in channels)
        {
            try
            {
                var guildChannel = await Bot.GetChannelAsync((ulong)channel.ChannelId);
                if (guildChannel is not ITextChannel) continue;
                o.Add(channel);
            }
            catch (HttpException e)
            {
                Console.WriteLine($"[GlobalEvent] Error: Couldn't get channel {channel.ChannelId} | {e}");
            }
        }
        return o;
    }

    public static bool ShouldHandle(Track track) => track.Mined < 100_000;

    protected override async Task<string> GetMessage(Channel channel, string message)
    {
        var discordChannel = await Bot.GetChannelAsync((ulong)channel.ChannelId) as ITextChannel;
        
        var variant = await Track.Variant;
        var variantName = variant?.Name == "Normal" ? "" : variant?.Name;
        
        var ore = await Track.Ore;
        var oreName = ore?.Name ?? "Invalid Ore";
        if (discordChannel != null && ore != null)
        {
            var modified = HardCoded.GetModifiedTrackName(discordChannel.GuildId, ore, variant);
            if (modified != null) oreName = modified;
        }

        var tier = ore == null ? null : await ore.Tier;
        var tierName = tier?.Name ?? "Invalid Tier";

        var spawner = await Track.Spawner;
        var cave = "Invalid Cave";
        if (spawner?.Type == SpawnerType.Cave)
        {
            cave = spawner.Name;
        }

        var ping = variant != null && tier != null ? await PingManager.Instance.Get(channel, variant, tier) : null;
        var pingStr = ping?.PingStr ?? "";
        if (pingStr != "" && !pingStr.StartsWith(' ')) pingStr = $" {pingStr}";

        var e = await Track.Event;
        var eOre = e == null ? null : await e.Ore;
        var eStr = eOre?.Name ?? "None";

        var rarity = await Track.Rarity;
        
        return Smart.Format(message, new
        {
            guild = (await Title).Extend(),
            player = Track.PlayerStr.Extend(),
            player_ping = "".Extend(),
            variant = (variantName is { Length: > 0 } ? $"{variantName} " : "").Extend(),
            ore = oreName.Extend(),
            cave = cave.Extend(),
            tier = tierName.Extend(),
            tier_variant = (variantName is { Length: > 0 } ? $" ({variantName})" : "").Extend(),
            ping = pingStr.Extend(),
            base_rarity = rarity?.Base ?? -1,
            adjusted_rarity = rarity?.Adjusted ?? -1,
            blocks = Track.Mined,
            loadout = Track.EquipmentStr.Extend(),
            _event = eStr.Extend()
        });
    }
}