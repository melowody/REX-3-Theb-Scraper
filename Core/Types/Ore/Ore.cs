using System.Text.Json.Serialization;
using GooberTracker.Core.Types.Tier;

namespace GooberTracker.Core.Types.Ore;

public record Ore(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("tier")] int TierId,
    [property: JsonPropertyName("alt_name")] string[] AltNames
) : IRExObject<int>
{
    [JsonIgnore]
    public Task<Tier.Tier?> Tier => TierManager.Instance.Get(TierId);
    
    public int GetKeyTyped() => Id;

    public virtual bool Equals(Ore? other) => other?.Id == Id;

    public override string ToString() => Name;
}