using System.Text.Json.Serialization;

namespace GooberTracker.Core.Types.World;

public record World(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("description")] string Description,
    [property: JsonPropertyName("alt_name")] List<string> AltNames
) : IRExObject<int>
{
    public int GetKeyTyped() => Id;

    public virtual bool Equals(World? other) => Id == other?.Id;

    public override string ToString() => Name;
}