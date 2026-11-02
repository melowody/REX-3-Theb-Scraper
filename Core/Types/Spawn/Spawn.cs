using System.Text.Json.Serialization;
using GooberTracker.Core.Types.Ore;
using GooberTracker.Core.Types.Spawner;

namespace GooberTracker.Core.Types.Spawn;

public record Spawn(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("ore")] int OreId,
    [property: JsonPropertyName("spawner")] int SpawnerId,
    [property: JsonPropertyName("rarity")] string RarityStr
) : IRExObject<int>
{
    [JsonIgnore]
    public Task<Ore.Ore?> Ore => OreManager.Instance.Get(OreId);
    
    [JsonIgnore]
    public Task<Spawner.Spawner?> Spawner => SpawnerManager.Instance.Get(SpawnerId);
    
    [JsonIgnore]
    public long Rarity => long.Parse(RarityStr);
    
    public int GetKeyTyped() => Id;

    public virtual bool Equals(Spawn? other) => other?.Id == Id;

    public override string ToString() => $"{OreId}:{SpawnerId}";
}