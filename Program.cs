using System.Text.Json;
using Discord;
using GooberTracker.Core.Types.Player;
using GooberTracker.Core.Types.Tier;
using GooberTracker.Discord.Bot;
using GooberTracker.Discord.Scraper;

namespace GooberTracker;

public static class Program
{
    private static Task Log(LogMessage msg)
    {
        try
        {
            Console.WriteLine(msg.ToString());
            return Task.CompletedTask;
        }
        catch (Exception exception)
        {
            return Task.FromException(exception);
        }
    }

    public static async Task Main(string[] _)
    { 
        var bot = new GooberBot();
        bot.Log += Log;
        await bot.StartAsync();

        var guild = await bot.Rest.GetGuildAsync(1409296527561592964);
        Console.WriteLine(guild.EveryoneRole.Id);

        await GooberScraper.Instance.Start();
        
        await Task.Delay(-1);
    }
}