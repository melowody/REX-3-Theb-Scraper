using System.Text.Json.Serialization;
using GooberTracker.Core.Types.Ore;
using GooberTracker.Core.Types.World;

namespace GooberTracker.Core.Types.Event;

public record Event(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("ore")] int OreId,
    [property: JsonPropertyName("world")] int WorldId,
    [property: JsonPropertyName("rarity")] string RarityStr,
    [property: JsonPropertyName("text")] string Text,
    [property: JsonPropertyName("duration")] int Duration,
    [property: JsonPropertyName("chance")] int Chance
) : IRExObject<int>
{
    
    [JsonIgnore]
    public Task<Ore.Ore?> Ore => OreManager.Instance.Get(OreId);
    [JsonIgnore]
    public Task<World.World?> World => WorldManager.Instance.Get(WorldId);
    [JsonIgnore]
    public long Rarity => long.Parse(RarityStr);
    
    public int GetKeyTyped() => Id;
}