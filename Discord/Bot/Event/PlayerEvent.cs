using Discord;
using Discord.Net;
using Discord.WebSocket;
using GooberTracker.Core.Types.Channel;
using GooberTracker.Core.Types.Goober;
using GooberTracker.Core.Types.Multiplier;
using GooberTracker.Core.Types.Ping;
using GooberTracker.Core.Types.Player;
using GooberTracker.Core.Types.PlayerName;
using GooberTracker.Core.Types.PlayerPing;
using GooberTracker.Core.Types.Spawner;
using GooberTracker.Core.Types.Track;
using GooberTracker.Discord.Scraper;
using SmartFormat;
using ChannelType = GooberTracker.Core.Types.Channel.ChannelType;

namespace GooberTracker.Discord.Bot.Event;

public class PlayerEvent(GooberBot bot, Track track) : EventTracker.Event(bot, track)
{
    protected override Task<List<Channel>> Channels => GetChannels();
    protected virtual Task<string> Title => Task.FromResult("GOOBER");

    private async Task<Goober?> GetGoober()
    {
        var playerName = await PlayerNameManager.Instance.Get(track.PlayerStr);
        if (playerName == null) return null;
        var player = await playerName.Player;
        if (player == null) return null;
        return await GooberManager.Instance.Get(player);
    }
    
    private async Task<List<Channel>> GetChannels()
    {
        var goober = await GetGoober();
        if (goober == null) return [];

        List<Channel> o = [];
        var toCheck = (await ChannelManager.Instance.GetAll(ChannelType.Player)).ToList();
        if (this is ServerGlobalEvent)
        {
            toCheck.AddRange(await ChannelManager.Instance.GetAll(ChannelType.ServerGlobal));
        }
        foreach (var channel in toCheck)
        {
            try
            {
                var guildChannel = await bot.GetChannelAsync((ulong)channel.ChannelId);
                if (guildChannel is not ITextChannel textChannel) continue;
                var guild = await ((IDiscordClient)bot).GetGuildAsync(textChannel.GuildId);
                if (await guild.GetUserAsync(goober.DiscordId) != null)
                {
                    o.Add(channel);
                }
            }
            catch (HttpException e)
            {
                Console.WriteLine($"[GlobalEvent] Error: Couldn't get channel {channel.ChannelId} | {e}");
            }
        }

        return o;
    }

    public static async Task<bool> ShouldHandle(Track track)
    {
        var playerName = await PlayerNameManager.Instance.Get(track.PlayerStr);
        return playerName != null;
    }

    private async Task<string> GetPlayerPing(Channel channel)
    {
        var goober = await GetGoober();
        if (goober == null) return "";
        var playerPing = await PlayerPingManager.Instance.Get(goober, channel);
        return playerPing is not { Ping: true } ? "" : $" <@{goober.DiscordId}>";
    } 
    
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

        var rarity = await track.Rarity;
        
        return Smart.Format(message, new
        {
            guild = (await Title).Extend(),
            player = track.PlayerStr.Extend(),
            player_ping = (await GetPlayerPing(channel)).Extend(),
            variant = (variantName is { Length: > 0 } ? $"{variantName} " : "").Extend(),
            ore = oreName.Extend(),
            cave = cave.Extend(),
            tier = tierName.Extend(),
            tier_variant = (variantName is { Length: > 0 } ? $" ({variantName})" : "").Extend(),
            ping = pingStr.Extend(),
            base_rarity = rarity?.Base ?? -1,
            adjusted_rarity = rarity?.Adjusted ?? -1,
            blocks = track.Mined,
            loadout = track.EquipmentStr.Extend(),
            _event = eStr.Extend()
        });
    }
}