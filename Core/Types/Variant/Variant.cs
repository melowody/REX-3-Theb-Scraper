using System.Text.Json.Serialization;

namespace GooberTracker.Core.Types.Variant;

public record Variant(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("name")] string Name
) : IRExObject<int>
{
    public int GetKeyTyped() => Id;

    public virtual bool Equals(Variant? other) => Id == other?.Id;

    public override string ToString() => Name;
}