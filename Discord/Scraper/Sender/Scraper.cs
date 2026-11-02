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

public partial class Scraper : Utils.JsonSender
{
    private static Utils.AsyncStack<Track>? _trackStack;

    public static Track? GetTrack() => _trackStack?.Pop();

    public Scraper(CancellationTokenSource cts) : base(cts)
    {
        _trackStack = new Utils.AsyncStack<Track>(cts);
    }

    private static async Task<Track?> ParseTrack(JsonObject e)
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
        
        var variant = await VariantManager.Instance.Get("Normal");
        if (variantText.Length > 0)
            variant = await VariantManager.Instance.Get(new CultureInfo("en-US", false).TextInfo.ToTitleCase(variantText));
        if (variant == null) return null;

        Console.WriteLine("[Scraper] Getting Ore");
        
        var ore = await OreManager.Instance.Get(oreText);
        if (ore == null) return null;
        
        Console.WriteLine("[Scraper] Getting World");
        
        var world = await WorldManager.Instance.Get(worldText);
        if (world == null) return null;

        Console.WriteLine("[Scraper] Getting Spawner");
        
        Spawner? spawner;
        if (caveText.Length > 0)
        {
            spawner = await SpawnerManager.Instance.Get(caveText);
        }
        else
        {
            var spawns = new List<Spawn>();

            Console.WriteLine(ore.Name);
            foreach (var spawn in await SpawnManager.Instance.GetAll(ore))
            {
                Console.WriteLine("[Scraper] Blehhhh");
                var inSpawner = await spawn.Spawner;
                if (inSpawner == null || inSpawner.Type == SpawnerType.Cave)
                {
                    Console.WriteLine("[Scraper] Found either null or cave");
                    continue;
                }
                var inWorld = await inSpawner.World;
                if (inWorld == world) spawns.Add(spawn);
            }
            
            if (spawns.Count == 0)
            {
                Console.WriteLine("[Scraper] Could not find a valid spawn");
                return null;
            }
            spawner = await spawns.First().Spawner;
        }
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
                        Console.WriteLine($"[Scraper] Blocks Mined: {(field["value"]?.GetValue<string>() ?? "-1").Replace(",", "")}");
                        blocksMined = long.Parse((field["value"]?.GetValue<string>() ?? "-1").Replace(",", ""));
                        break;
                    }
                    case "Event":
                    {
                        var ev = field["value"]?.GetValue<string>();
                        if (ev is null or "None") continue;
                        var eventOre = await OreManager.Instance.Get(ev);
                        if (eventOre == null) continue;
                        var eventImpl = await EventManager.Instance.Get(eventOre);
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
        return await TrackerManager.Instance.Get(long.Parse(author["id"]!.GetValue<string>())) != null;
    }
        

    public override async Task HandleEvent(JsonNode e, GooberScraper scraper)
    {
        foreach (var embed in (e["d"]!["embeds"]! as JsonArray)!)
        {
            if (Cts.IsCancellationRequested) return;
            var track = await ParseTrack((embed as JsonObject)!);
            if (track == null || _trackStack == null) continue;
            Console.WriteLine("[Scraper] Pushing track");
            _trackStack.Push(track);
        }
    }

    [GeneratedRegex(@"^\*\*(.+?)\*\* has found\s?(?:an? (spectral|ionized)\s?)?\*\*\s?(.+?)\*\*(?: \(\*(.+?)\*\))?$")]
    private static partial Regex TitleRegex();
}