using System.Text.Json.Serialization;
using GooberTracker.Core.Types.Ore;
using GooberTracker.Core.Types.World;

namespace GooberTracker.Core.Types.Spawner;

public enum SpawnerType
{
    Layer,
    Cave
}

public record Spawner(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("type")] SpawnerType Type,
    [property: JsonPropertyName("world")] int WorldId,
    [property: JsonPropertyName("block")] int BlockId,
    [property: JsonPropertyName("min_depth")]
    int? MinDepth,
    [property: JsonPropertyName("max_depth")]
    int? MaxDepth,
    [property: JsonPropertyName("cave_rarity")]
    int? CaveRarity
) : IRExObject<int>
{
    [JsonIgnore]
    public Task<World.World?> World => WorldManager.Instance.Get(WorldId);
    [JsonIgnore]
    public Task<Ore.Ore?> Block => OreManager.Instance.Get(BlockId);
    
    public int GetKeyTyped() => Id;

    public virtual bool Equals(Spawner? other) => other?.Id == Id;

    public override string ToString() => Name;
}