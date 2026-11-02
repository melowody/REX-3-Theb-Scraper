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

    private async Task<double?> GetRarity()
    {
        var spawner = await Spawner;
        if (spawner == null)
        {
            Console.WriteLine($"[Track] Could not find spawner: {SpawnerId}");
            return null;
        }
        
        var spawn = await Spawn;
        switch (spawn)
        {
            case null when spawner.Name != "Gilded Cave":
                Console.WriteLine($"[Track] Could not find spawn: {SpawnerId} + {OreId}");
                return null;
            case null:
            {
                Console.WriteLine("[Track] Gilded Cave!");
                var ore = await Ore;
                if (ore == null)
                {
                    Console.WriteLine($"[Track] Could not find Ore: {OreId}");
                    return null;
                }
                Spawn.Spawn? layerSpawn = null;
                foreach (var s in await SpawnManager.Instance.GetAll(ore))
                {
                    var sp = await s.Spawner;
                    if (sp == null || sp.Type == SpawnerType.Cave) continue;
                    layerSpawn = s;
                    break;
                }
                if (layerSpawn == null)
                {
                    Console.WriteLine($"[Track] Could not find layer spawn for: {OreId}");
                    return null;
                }
                spawn = new Spawn.Spawn(-1, OreId, spawner.Id, $"{layerSpawn.Rarity * 2.5}");
                break;
            }
        }
        Console.WriteLine($"[Track] Spawn: {spawn.Id}, Rarity: {spawn.Rarity}");

        var multiplier = (await Multiplier)?.Multi ?? 1;

        var rarity = (double)spawn.Rarity * multiplier;
        if (spawner.Type == SpawnerType.Cave)
        {
            rarity *= 1.88 * spawner.CaveRarity ?? 1.0;
        }

        return rarity;
    }
    
    [JsonIgnore] public Task<double?> Rarity => GetRarity();
    
    public int GetKeyTyped() => Id;

    public virtual bool Equals(Track? other) => other?.Id == Id;

    public override string ToString() =>
        $"{PlayerStr} found {VariantId} {OreId} at {Time} in {SpawnerId} with {MinedStr}";
}