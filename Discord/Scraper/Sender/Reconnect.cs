using System.Net.WebSockets;
using System.Text.Json.Nodes;

namespace GooberTracker.Discord.Scraper.Sender;

public class Reconnect(CancellationTokenSource cts) : Utils.JsonSender(cts)
{

    public override async Task<bool> ShouldHandle(JsonNode e) =>
        e is JsonObject obj && obj.ContainsKey("op") && obj["op"]!.GetValue<int>() == 7;

    public override async Task HandleEvent(JsonNode e, GooberScraper scraper)
    {
        await scraper.Cancel();

        await scraper.Socket.CloseAsync(WebSocketCloseStatus.NormalClosure, null, CancellationToken.None);
        await Task.Delay(1000);
        _ = Utils.LogExceptions(scraper.Start());
    }
    
}