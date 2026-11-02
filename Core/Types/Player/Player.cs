using System.Text.Json.Serialization;

namespace GooberTracker.Core.Types.Player;

public record Player(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("roblox_id")]
    string RobloxIdStr
) : IRExObject<int>
{
    
    [JsonIgnore]
    public long RobloxId => long.Parse(RobloxIdStr);
    
    public int GetKeyTyped() => Id;

    public virtual bool Equals(Player? other) => other?.Id == Id;

    public override string ToString() => RobloxIdStr;
}