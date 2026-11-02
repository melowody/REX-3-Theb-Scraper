using System.Net.WebSockets;
using System.Text.Json.Nodes;

namespace GooberTracker.Discord.Scraper.Sender;

public class Reconnect(CancellationTokenSource cts) : Utils.JsonSender(cts)
{

    public override Task<bool> ShouldHandle(JsonNode e) =>
        Task.FromResult(e is JsonObject obj && obj.ContainsKey("op") && obj["op"]!.GetValue<int>() == 7);

    public override Task HandleEvent(JsonNode e, GooberScraper scraper)
    {
       scraper.Restart();
       return Task.CompletedTask;
    }
    
}