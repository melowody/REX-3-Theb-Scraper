using System.Text.Json.Serialization;

namespace GooberTracker.Core.Types.TrackerFormat;

public record TrackerFormat(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("month")] int Month,
    [property: JsonPropertyName("day")] int Day,
    [property: JsonPropertyName("format_string")]
    string DefaultFormat,
    [property: JsonPropertyName("adjusted_format")]
    string AdjustedFormat
) : IRExObject<int>
{
    public int GetKeyTyped() => Id;

    public virtual bool Equals(TrackerFormat? other) => other?.Id == Id;

    public override string ToString() => DefaultFormat;
}