using Discord;
using Discord.Net;
using GooberTracker.Core.Types.Channel;
using GooberTracker.Core.Types.Multiplier;
using GooberTracker.Core.Types.Ping;
using GooberTracker.Core.Types.Spawner;
using GooberTracker.Core.Types.Track;
using GooberTracker.Core.Types.Variant;
using GooberTracker.Discord.Scraper;
using SmartFormat;
using ChannelType = GooberTracker.Core.Types.Channel.ChannelType;

namespace GooberTracker.Discord.Bot.Event;

public class BeginnerEvent(GooberBot bot, Track track) : EventTracker.Event(bot, track)
{
    protected override Task<List<Channel>> Channels => GetChannels();
    
    private async Task<List<Channel>> GetChannels()
    {
        var channels = await ChannelManager.Instance.GetAll(ChannelType.Beginner);
        List<Channel> o = [];
        foreach (var channel in channels)
        {
            try
            {
                var guildChannel = await bot.GetChannelAsync((ulong)channel.ChannelId);
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
        var ore = await track.Ore;
        var oreName = ore?.Name ?? "Invalid Ore";

        var tier = ore == null ? null : await ore.Tier;
        var tierName = tier?.Name ?? "Invalid Tier";
        
        var variant = await track.Variant;
        var variantName = variant?.Name == "Normal" ? "" : variant?.Name;

        var spawner = await track.Spawner;
        var cave = "Invalid Cave";
        if (spawner?.Type == SpawnerType.Cave)
        {
            cave = spawner.Name;
        }

        var ping = variant != null && tier != null ? await PingManager.Instance.Get(channel, variant, tier) : null;
        var pingStr = ping?.PingStr ?? "";

        var spawn = await track.Spawn;

        var e = await track.Event;
        var eOre = e == null ? null : await e.Ore;
        var eStr = eOre?.Name ?? "None";
        
        Multiplier? multiplier = null;
        if (variant != null && tier != null) multiplier = await MultiplierManager.Instance.Get(variant, tier);
        
        return Smart.Format(message, new
        {
            guild = ":beginner:".Extend(),
            player = track.PlayerStr.Extend(),
            player_ping = "".Extend(),
            variant = (variantName is { Length: > 0 } ? $"{variantName} " : "").Extend(),
            ore = oreName.Extend(),
            cave = cave.Extend(),
            tier = tierName.Extend(),
            tier_variant = (variantName is { Length: > 0 } ? $" ({variantName})" : "").Extend(),
            ping = pingStr.Extend(),
            base_rarity = (spawn?.Rarity ?? -1) * (multiplier?.Multi ?? 1),
            adjusted_rarity = await track.Rarity ?? -1,
            blocks = track.Mined,
            loadout = track.EquipmentStr.Extend(),
            _event = eStr.Extend()
        });
    }
}