using System.Text.Json.Serialization;

namespace GooberTracker.Core.Types.Tracker;

public record Tracker(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("tracker_id")] string TrackerIdStr
) : IRExObject<int>
{
    public int GetKeyTyped() => Id;
    
    [JsonIgnore]
    public long TrackerId => long.Parse(TrackerIdStr);

    public virtual bool Equals(Tracker? other) => other?.Id == Id;

    public override string ToString() => TrackerIdStr;
}