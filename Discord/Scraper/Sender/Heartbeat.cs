using System.Text.Json.Nodes;

namespace GooberTracker.Discord.Scraper.Sender;

public class Heartbeat(CancellationTokenSource cts) : Utils.JsonSender(cts)
{

    public override async Task<bool> ShouldHandle(JsonNode e) =>
        e is JsonObject obj &&
        obj.ContainsKey("d") &&
        obj["d"] is JsonObject d &&
        d.ContainsKey("heartbeat_interval");

    public override async Task HandleEvent(JsonNode e, GooberScraper scraper)
    {
        if (Cts.IsCancellationRequested) return;
        var interval = e["d"]!["heartbeat_interval"]!.GetValue<int>();
        scraper.WriteQueue.Push(new JsonObject
        {
            ["op"] = 2,
            ["d"] = new JsonObject
            {
                ["token"] = Environment.GetEnvironmentVariable("SCRAPER_TOKEN"),
                ["properties"] = new JsonObject
                {
                    ["$os"] = "windows",
                    ["$browser"] = "chrome",
                    ["$device"] = "pc"
                }
            }
        });
        while (!Cts.IsCancellationRequested)
        {
            await Task.Delay((int)(interval * .75));
            scraper.WriteQueue.Push(new JsonObject
            {
                ["op"] = 1,
                ["d"] = null
            });
        }
    }
    
}