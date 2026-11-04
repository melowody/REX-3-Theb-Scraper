using Discord;
using Discord.WebSocket;
using GooberTracker.Core.Types.Channel;
using GooberTracker.Core.Types.Ping;
using GooberTracker.Core.Types.Spawner;
using GooberTracker.Core.Types.Track;
using GooberTracker.Core.Types.TrackerFormat;
using GooberTracker.Discord.Bot.Event;

namespace GooberTracker.Discord.Bot;

public class EventTracker(GooberBot bot)
{

    public abstract class Event(GooberBot bot, Track track)
    {
        protected readonly GooberBot Bot = bot;
        protected readonly Track Track = track;
        
        protected abstract Task<List<Channel>> Channels { get; }

        private const string BaseMessage = """
                                           ---------------------------------------------
                                           **[{guild} TRACKER]**
                                           **{player}{player_ping}** has found **{variant}{ore}**
                                           Tier: **{tier}**{tier_variant}{ping}
                                           Base Rarity: 1 in {base_rarity:N0}
                                           Blocks: {blocks:N0}
                                           Loadout: {loadout}
                                           Event: {_event} 
                                           ---------------------------------------------
                                           """;

        private const string AdjustedMessage = """
                                                ---------------------------------------------
                                                **[{guild} TRACKER]**
                                                **{player}{player_ping}** has found **{variant}{ore} ({cave})**
                                                Tier: **{tier}**{tier_variant}{ping}
                                                Base Rarity: 1 in {base_rarity:N0} in {cave}s
                                                Adjusted Rarity: {adjusted_rarity:N0}
                                                Blocks: {blocks:N0}
                                                Loadout: {loadout}
                                                Event: {_event}
                                                ---------------------------------------------
                                                """;

        private async Task<string> GetFormat()
        {
            string ret;
            var message = await TrackerFormatManager.Instance.GetAll(DateTime.Today);
            if ((await Track.Spawner)?.Type == SpawnerType.Cave)
            {
                ret = AdjustedMessage;
                if (message.Count > 0) ret = message[Random.Shared.Next(0, message.Count)].AdjustedFormat;
            }
            else
            {
                ret = BaseMessage;
                if (message.Count > 0) ret = message[Random.Shared.Next(0, message.Count)].DefaultFormat;
            }

            return ret;
        }
        
        public async Task SendMessages()
        {
            foreach (var channel in await Channels)
            {
                var guildChannel = await Bot.GetChannelAsync((ulong)channel.ChannelId);
                if (guildChannel is not ITextChannel textChannel) continue;
                await textChannel.SendMessageAsync(await GetMessage(channel, await GetFormat()));
            }
        }

        protected abstract Task<string> GetMessage(Channel channel, string message);
    }

    public async Task<List<Event>> GetEvents(Track track)
    {
        List<Event> o = [];
        if (await ServerGlobalEvent.ShouldHandle(track))
        {
            o.Add(new ServerGlobalEvent(bot, track));
        }
        else if (await PlayerEvent.ShouldHandle(track))
        {
            o.Add(new PlayerEvent(bot, track));
            // await TrackManager.Instance.Post(track);
        }
        if (await GlobalEvent.ShouldHandle(track)) o.Add(new GlobalEvent(bot, track));
        if (BeginnerEvent.ShouldHandle(track)) o.Add(new BeginnerEvent(bot, track));
        return o;
    }

}