using System.Text.Json.Serialization;

namespace GooberTracker.Core.Types.Channel;

public enum ChannelType
{
    Beginner,
    Player,
    Global
}

public record Channel(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("channel_id")] string ChannelIdStr,
    [property: JsonPropertyName("type")] string TypeStr
) : IRExObject<int>
{
    public int GetKeyTyped() => Id;
    
    [JsonIgnore]
    public long ChannelId => long.Parse(ChannelIdStr);
    
    [JsonIgnore]
    public ChannelType Type => TypeStr switch
    {
        "beginner" => ChannelType.Beginner,
        "global" => ChannelType.Global,
        _ => ChannelType.Player
    };

    public virtual bool Equals(Channel? other) => other?.Id == Id;

    public override string ToString() => $"{ChannelIdStr}: {TypeStr}";
}