using GooberTracker.Core.Types.Track;

namespace GooberTracker.Discord.Bot.Event;

public class ServerGlobalEvent(GooberBot bot, Track track) : PlayerEvent(bot, track)
{
    protected override Task<string> Title => Task.FromResult("SERVER GLOBAL");
    
    public new static async Task<bool> ShouldHandle(Track track)
    {
        return await PlayerEvent.ShouldHandle(track) && await GlobalEvent.ShouldHandle(track);
    }
}