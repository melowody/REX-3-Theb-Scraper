using GooberTracker.Core.Types.Ore;
using GooberTracker.Core.Types.Spawn;
using GooberTracker.Core.Types.Spawner;
using GooberTracker.Core.Types.Track;
using GooberTracker.Core.Types.Variant;

namespace GooberTracker;

public static class HardCoded
{
    public const double CaveConstant = 1.88;
    public static readonly Task<Variant?> DefaultVariant = VariantManager.Instance.Get("Normal");
    private const ulong GoobervilleId = 1098291233945813044;

    public static async Task<string> GetName(this SpawnerManager.CaveAutocompleteHandler _, Spawner spawner)
    {
        if (spawner.Name != "Gilded Cave") return spawner.Name;
        var world = await spawner.World;
        return world == null ? spawner.Name : $"{spawner.Name} ({world.Name})";
    }
    
    public static async Task<Spawn?> GetSpecialRarity(this Track track)
    {
        Console.WriteLine("[Track/Special] Checking Special Rarity");
        var spawn = await track.Spawner;
        if (spawn == null) return null;

        var ore = await track.Ore;
        if (ore == null) return null;

        if (spawn.Name == "Gilded Cave")
        {
            Console.WriteLine("[Track/Special] Checking Gilded Cave");
            var oreSpawns = await SpawnManager.Instance.GetAll(ore);
            Spawn? layerSpawn = null;
            foreach (var oreSpawn in oreSpawns)
            {
                Console.WriteLine($"[Track/Special] Checking Spawner: {oreSpawn.SpawnerId}");
                var oreSpawner = await oreSpawn.Spawner;
                if (oreSpawner is not { Type: SpawnerType.Layer }) continue;
                break;
            }

            var divisor = 1.0;
            if (track.EquipmentStr.Contains("100 Leaf Clover"))
            {
                divisor = 1.0 / 57.0;
            }

            if (track.EquipmentStr.Contains("Ambrosia Salad") || track.EquipmentStr.Contains("57 Leaf Clover"))
            {
                divisor = 1.0 / 100.0;
            }

            if (layerSpawn == null)
            {
                Console.WriteLine($"[Track/Special] Couldn't find layer spawn for ore: {ore.Name}");
                return null;
            }
            Console.WriteLine($"[Track/Special] Out: {layerSpawn.Rarity * 2.5 * divisor}");
            return new Spawn(-1, ore.Id, spawn.Id, $"{layerSpawn.Rarity * 2.5 * divisor}");
        }
        
        var ev = await track.Event;
        if (ev == null) return null;

        var evOre = await ev.Ore;
        if (evOre == null) return null;

        if (evOre.Name != "Nebulova") return null;
        {
            var starry = await SpawnerManager.Instance.Get("Starry Cave");
            if (starry == null) return null;

            var oreSpawn = await SpawnManager.Instance.Get(ore, starry);
            return oreSpawn == null ? null : new Spawn(-1, ore.Id, spawn.Id, $"{oreSpawn.Rarity * 3.0}");
        }

    }

    public static string? GetModifiedTrackName(ulong server, Ore ore, Variant? variant = null)
    {
        var variantPrefix = variant != null ? variant.Name == "Normal" ? "" : $"{variant.Name}" : "";
        if (server != GoobervilleId) return null;
        switch (ore.Name)
        {
            case "Inclemetite":
            {
                var chance = Random.Shared.Next(0, 10);
                return chance == 0 ? $"{variantPrefix} 𝔞 𝔪𝔞𝔤𝔦𝔠 𝔴𝔞𝔫𝔡" : $"{variantPrefix} The Magic Medal";
            }
            case "Acceleratium":
            {
                return variant?.Name == "Ionized" ? "Sea Urchin Crystal" : null;
            }
        }

        return null;
    }
}