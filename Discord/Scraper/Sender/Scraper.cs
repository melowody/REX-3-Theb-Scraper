using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using GooberTracker.Core.Types.Event;
using GooberTracker.Core.Types.Ore;
using GooberTracker.Core.Types.Spawn;
using GooberTracker.Core.Types.Spawner;
using GooberTracker.Core.Types.Track;
using GooberTracker.Core.Types.Tracker;
using GooberTracker.Core.Types.Variant;
using GooberTracker.Core.Types.World;

namespace GooberTracker.Discord.Scraper.Sender;

public partial class Scraper(CancellationTokenSource cts) : Utils.JsonSender(cts)
{
    private static readonly Utils.AsyncStack<Track>? TrackStack = new(CancellationToken.None);

    public static Task<Track?> GetTrack() => TrackStack?.Pop() ?? Task.FromResult<Track?>(null);

    private async Task<Track?> ParseTrack(JsonObject e)
    {
        Console.WriteLine($"[Scraper] Parsing: {e}");

        var titleRegex = TitleRegex().Match(e["title"]?.GetValue<string>() ?? "");
        if (!titleRegex.Success) return null;
        
        var playerName = titleRegex.Groups[1].Value;
        var variantText = titleRegex.Groups[2].Value;
        var oreText = titleRegex.Groups[3].Value;
        var caveText = titleRegex.Groups[4].Value;
        
        Console.WriteLine($"[Scraper] Player: {playerName} | Variant: {variantText} | Ore: {oreText} | Cave: {caveText}");
        
        var worldText = e["description"]?.GetValue<string>() ?? "None";
        
        Console.WriteLine("[Scraper] Getting Time");
        
        var timeStr = e["id"]?.GetValue<string>();
        if (timeStr == null) return null;
        var time = long.Parse(timeStr).FromDiscordSnowflake();
        
        Console.WriteLine("[Scraper] Getting Variant");
        
        var variant = await HardCoded.DefaultVariant;
        Cts.Token.ThrowIfCancellationRequested();
        if (variantText.Length > 0)
        {
            variant = await VariantManager.Instance.Get(
                new CultureInfo("en-US", false).TextInfo.ToTitleCase(variantText));
            Cts.Token.ThrowIfCancellationRequested();
        }
        if (variant == null) return null;

        Console.WriteLine("[Scraper] Getting Ore");
        
        var ore = await OreManager.Instance.Get(oreText);
        Cts.Token.ThrowIfCancellationRequested();
        if (ore == null) return null;
        
        Console.WriteLine("[Scraper] Getting World");
        
        var world = await WorldManager.Instance.Get(worldText);
        Cts.Token.ThrowIfCancellationRequested();
        if (world == null) return null;

        Console.WriteLine("[Scraper] Getting Spawner");
        
        Spawner? spawner;
        if (caveText.Length > 0)
        {
            spawner = await SpawnerManager.Instance.Get(caveText);
            Cts.Token.ThrowIfCancellationRequested();
        }
        else
        {
            var spawns = new List<Spawn>();

            Console.WriteLine(ore.Name);
            var spawnList = await SpawnManager.Instance.GetAll(ore);
            Cts.Token.ThrowIfCancellationRequested();
            foreach (var spawn in spawnList)
            {
                var inSpawner = await spawn.Spawner;
                Cts.Token.ThrowIfCancellationRequested();
                if (inSpawner == null || inSpawner.Type == SpawnerType.Cave)
                {
                    Console.WriteLine("[Scraper] Found either null or cave");
                    continue;
                }
                var inWorld = await inSpawner.World;
                Cts.Token.ThrowIfCancellationRequested();
                if (inWorld == world) spawns.Add(spawn);
            }
            
            if (spawns.Count == 0)
            {
                Console.WriteLine("[Scraper] Could not find a valid spawn");
                return null;
            }
            spawner = await spawns.First().Spawner;
        }

        Cts.Token.ThrowIfCancellationRequested();
        if (spawner == null) return null;

        Console.WriteLine("[Scraper] Getting Event/Blocks Mined");
        
        var blocksMined = -1L;
        int? eventId = null;
        var equipment = "";

        try
        {
            Console.WriteLine($"[Scraper] Working with: ${e}");
            var fields = (JsonArray?)e["fields"] ?? [];
            Console.WriteLine($"[Scraper] Fields: {fields}");
            foreach (var field in (JsonArray?)e["fields"] ?? [])
            {

                switch (field?["name"]?.GetValue<string>())
                {
                    case "Blocks Mined":
                    {
                        Console.WriteLine(
                            $"[Scraper] Blocks Mined: {(field["value"]?.GetValue<string>() ?? "-1").Replace(",", "")}");
                        blocksMined = long.Parse((field["value"]?.GetValue<string>() ?? "-1").Replace(",", ""));
                        break;
                    }
                    case "Event":
                    {
                        var ev = field["value"]?.GetValue<string>();
                        if (ev is null or "None") continue;
                        var eventOre = await OreManager.Instance.Get(ev);
                        Cts.Token.ThrowIfCancellationRequested();
                        if (eventOre == null) continue;
                        var eventImpl = await EventManager.Instance.Get(eventOre);
                        Cts.Token.ThrowIfCancellationRequested();
                        eventId = eventImpl?.Id;
                        break;
                    }
                    case "Loadout":
                    {
                        equipment = field["value"]?.GetValue<string>() ?? "Unknown Equipment";
                        break;
                    }
                }
            }
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"ERROR: {ex}");
        }
        
        var track = new Track(0, playerName, variant.Id, ore.Id, spawner.Id, eventId, blocksMined.ToString(), equipment, time.ToLongDateString());
        Console.WriteLine($"[Scraper] Scraped: {JsonSerializer.Serialize(track)}");
        return track;
    }

    public override async Task<bool> ShouldHandle(JsonNode e)
    {
        if (Cts.IsCancellationRequested) return false;
        if (e is not JsonObject obj || !obj.ContainsKey("t")) return false;
        var t = obj["t"]?.GetValue<string?>();
        if (t is not "MESSAGE_CREATE") return false;
        if (!obj.ContainsKey("d")) return false;
        if (obj["d"]! is not JsonObject d || !d.ContainsKey("author")) return false;
        if (d["author"]! is not JsonObject author || !author.ContainsKey("id")) return false;
        Console.WriteLine($"[Scraper] Author: {author} | String: {author["id"]!.GetValue<string>()} | Long: {long.Parse(author["id"]!.GetValue<string>())}");
        var ret = await TrackerManager.Instance.Get(long.Parse(author["id"]!.GetValue<string>())) != null;
        Cts.Token.ThrowIfCancellationRequested();
        return ret;
    }
        

    public override async Task HandleEvent(JsonNode e, GooberScraper scraper)
    {
        foreach (var embed in (e["d"]!["embeds"]! as JsonArray)!)
        {
            if (Cts.IsCancellationRequested) return;
            var track = await ParseTrack((embed as JsonObject)!);
            Cts.Token.ThrowIfCancellationRequested();
            if (track == null || TrackStack == null) continue;
            Console.WriteLine("[Scraper] Pushing track");
            TrackStack.Push(track);
        }
    }

    [GeneratedRegex(@"^\*\*(.+?)\*\* has found\s?(?:an? (spectral|ionized)\s?)?\*\*\s?(.+?)\*\*(?: \(\*(.+?)\*\))?$")]
    private static partial Regex TitleRegex();
}