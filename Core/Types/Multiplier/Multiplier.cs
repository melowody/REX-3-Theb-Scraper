using System.Text.Json.Serialization;
using GooberTracker.Core.Types.Tier;
using GooberTracker.Core.Types.Variant;

namespace GooberTracker.Core.Types.Multiplier;

public record Multiplier(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("tier")] int TierId,
    [property: JsonPropertyName("variant")]
    int VariantId,
    [property: JsonPropertyName("multiplier")]
    int Multi
) : IRExObject<int>
{
    public int GetKeyTyped() => Id;

    [JsonIgnore]
    public Task<Tier.Tier?> Tier => TierManager.Instance.Get(TierId);
    [JsonIgnore]
    public Task<Variant.Variant?> Variant => VariantManager.Instance.Get(VariantId);

    public virtual bool Equals(Multiplier? other) => other?.Id == Id;

    public override string ToString() => $"{TierId}:{VariantId}";
}