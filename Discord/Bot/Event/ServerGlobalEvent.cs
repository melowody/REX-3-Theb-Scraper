using GooberTracker.Core.Types.Track;

namespace GooberTracker.Discord.Bot.Event;

public class ServerGlobalEvent(GooberBot bot, Track track) : PlayerEvent(bot, track)
{
    protected override Task<string> Title => Task.FromResult("Server Global");
    
    public static async Task<bool> ShouldHandle(Track track)
    {
        if (!await PlayerEvent.ShouldHandle(track)) return false;
        return await GlobalEvent.ShouldHandle(track);
    }
}