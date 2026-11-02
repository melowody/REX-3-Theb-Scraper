using System.Text.Json.Serialization;
using GooberTracker.Core.Types.Variant;

namespace GooberTracker.Core.Types.Tier;

public record Tier(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("min_rarity")]
    string MinRarity,
    [property: JsonPropertyName("max_rarity")]
    string MaxRarity,
    [property: JsonPropertyName("color")] string Color,
    [property: JsonPropertyName("global_requirement")] int[] GlobalRequiredIds
) : IRExObject<int>
{
    public int GetKeyTyped() => Id;

    private async Task<List<Variant.Variant?>> GetGlobalRequirements()
    {
        List<Variant.Variant?> o = [];
        foreach (var id in GlobalRequiredIds)
        {
            o.Add(await VariantManager.Instance.Get(id));
        }

        return o;
    }

    [JsonIgnore]
    public Task<List<Variant.Variant?>> GlobalRequirements => GetGlobalRequirements();

    public virtual bool Equals(Tier? other) => other?.Id == Id;

    public override string ToString() => Name;
}