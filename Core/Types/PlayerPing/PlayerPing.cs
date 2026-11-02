using System.Text.Json.Serialization;
using GooberTracker.Core.Types.Channel;
using GooberTracker.Core.Types.Goober;

namespace GooberTracker.Core.Types.PlayerPing;

public record PlayerPing(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("channel")]
    int ChannelId,
    [property: JsonPropertyName("goober")] int GooberId,
    [property: JsonPropertyName("ping")] bool Ping
) : IRExObject<int>
{
    public int GetKeyTyped() => Id;

    public virtual bool Equals(PlayerPing? other) => other?.Id == Id;

    [JsonIgnore] public Task<Channel.Channel?> Channel => ChannelManager.Instance.Get(ChannelId);
    
    [JsonIgnore] public Task<Goober.Goober?> Goober => GooberManager.Instance.Get(GooberId);
}