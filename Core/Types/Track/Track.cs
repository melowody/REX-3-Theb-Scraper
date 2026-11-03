using System.Text.Json;
using System.Text.Json.Serialization;
using GooberTracker.Core.Types.Event;
using GooberTracker.Core.Types.Multiplier;
using GooberTracker.Core.Types.Ore;
using GooberTracker.Core.Types.Spawn;
using GooberTracker.Core.Types.Spawner;
using GooberTracker.Core.Types.Variant;

namespace GooberTracker.Core.Types.Track;


public record Track(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("player")] string PlayerStr,
    [property: JsonPropertyName("variant")]
    int VariantId,
    [property: JsonPropertyName("ore")] int OreId,
    [property: JsonPropertyName("spawner")]
    int SpawnerId,
    [property: JsonPropertyName("event")] int? EventId,
    [property: JsonPropertyName("mined")] string MinedStr,
    [property: JsonPropertyName("equipment")] string EquipmentStr,
    [property: JsonPropertyName("time")] string TimeStr
) : IRExObject<int>
{
    public record TrackRarity(double Base, double Adjusted);
    
    [JsonIgnore] public long Mined => long.Parse(MinedStr);
    
    [JsonIgnore] public DateTime Time => DateTime.Parse(TimeStr);

    [JsonIgnore] public Task<Variant.Variant?> Variant => VariantManager.Instance.Get(VariantId);

    [JsonIgnore] public Task<Ore.Ore?> Ore => OreManager.Instance.Get(OreId);
    
    [JsonIgnore] public Task<Spawner.Spawner?> Spawner => SpawnerManager.Instance.Get(SpawnerId);
    
    [JsonIgnore] public Task<Event.Event?> Event => EventId == null ? Task.FromResult<Event.Event?>(null) : EventManager.Instance.Get(EventId.Value);
        
    private async Task<Spawn.Spawn?> GetSpawn()
    {
        var ore = await Ore;
        if (ore == null) return null;
        var spawner = await Spawner;
        if (spawner == null) return null;
        return await SpawnManager.Instance.Get(ore, spawner);
    }

    [JsonIgnore] public Task<Spawn.Spawn?> Spawn => GetSpawn();

    private async Task<Multiplier.Multiplier?> GetMultiplier()
    {
        var ore = await Ore;
        if (ore == null) return null;
        var variant = await Variant;
        if (variant == null) return null;
        var tier = await ore.Tier;
        if (tier == null) return null;
        return await MultiplierManager.Instance.Get(variant, tier);
    }
    
    [JsonIgnore] public Task<Multiplier.Multiplier?> Multiplier => GetMultiplier();

    private async Task<Spawn.Spawn?> GetSpecialRarity()
    {
        var spawn = await Spawner;
        if (spawn == null) return null;

        var ore = await Ore;
        if (ore == null) return null;

        if (spawn.Name == "Gilded Cave")
        {
            var oreSpawns = await SpawnManager.Instance.GetAll(ore);
            Spawn.Spawn? layerSpawn = null;
            foreach (var oreSpawn in oreSpawns)
            {
                var oreSpawner = await oreSpawn.Spawner;
                if (oreSpawner?.Type is not SpawnerType.Layer) continue;
                break;
            }

            var divisor = 1.0;
            if (EquipmentStr.Contains("100 Leaf Clover"))
            {
                divisor = 1.0 / 57.0;
            }

            if (EquipmentStr.Contains("Ambrosia Salad") || EquipmentStr.Contains("57 Leaf Clover"))
            {
                divisor = 1.0 / 100.0;
            }
            return layerSpawn == null ? null : new Spawn.Spawn(-1, ore.Id, spawn.Id, $"{layerSpawn.Rarity * 2.5 * divisor}");
        }
        
        var ev = await Event;
        if (ev == null) return null;

        var evOre = await ev.Ore;
        if (evOre == null) return null;

        if (evOre.Name != "Nebulova") return null;
        {
            var starry = await SpawnerManager.Instance.Get("Starry Cave");
            if (starry == null) return null;

            var oreSpawn = await SpawnManager.Instance.Get(ore, starry);
            return oreSpawn == null ? null : new Spawn.Spawn(-1, ore.Id, spawn.Id, $"{oreSpawn.Rarity * 3.0}");
        }

    }
    
    private async Task<TrackRarity?> GetRarity()
    {
        var spawner = await Spawner;
        if (spawner == null)
        {
            Console.WriteLine($"[Track] Could not find spawner: {SpawnerId}");
            return null;
        }

        var spawn = await Spawn ?? await GetSpecialRarity();
        if (spawn == null)
        {
            Console.WriteLine($"[Track] Could not find spawn: {SpawnerId} + {OreId}");
            return null;
        }
        
        Console.WriteLine($"[Track] Spawn: {spawn.Id} | Rarity: {spawn.Rarity}");
        
        var multiplier = (await Multiplier)?.Multi ?? 1;
        
        var rarity = (double)spawn.Rarity * multiplier;
        var adjusted = rarity;
        if (spawner.Type == SpawnerType.Cave)
        {
            adjusted *= 1.88 * spawner.CaveRarity ?? 1.0;
        }

        return new TrackRarity(rarity, adjusted);
    }
    
    [JsonIgnore] public Task<TrackRarity?> Rarity => GetRarity();
    
    public int GetKeyTyped() => Id;

    public virtual bool Equals(Track? other) => other?.Id == Id;

    public override string ToString() =>
        $"{PlayerStr} found {VariantId} {OreId} at {Time} in {SpawnerId} with {MinedStr}";
}