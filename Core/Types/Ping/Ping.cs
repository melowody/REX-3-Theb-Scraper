using System.Text.Json.Serialization;
using GooberTracker.Core.Types.Tier;
using GooberTracker.Core.Types.Variant;

namespace GooberTracker.Core.Types.Ping;

public record Ping(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("channel")]
    int InternalChannelId,
    [property: JsonPropertyName("ping")] string PingStr,
    [property: JsonPropertyName("variant")]
    int VariantId,
    [property: JsonPropertyName("tier")] int TierId
) : IRExObject<int>
{
    public int GetKeyTyped() => Id;

    [JsonIgnore] public Task<Variant.Variant?> Variant => VariantManager.Instance.Get(VariantId);
    
    [JsonIgnore] public Task<Tier.Tier?> Tier => TierManager.Instance.Get(TierId);

    public virtual bool Equals(Ping? other) => other?.Id == Id;
}