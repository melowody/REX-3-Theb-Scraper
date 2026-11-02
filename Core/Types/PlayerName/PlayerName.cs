using System.Text.Json.Serialization;
using GooberTracker.Core.Types.Player;

namespace GooberTracker.Core.Types.PlayerName;

public record PlayerName(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("player")] int PlayerId,
    [property: JsonPropertyName("name")] string Name
) : IRExObject<int>
{
    [JsonIgnore] public Task<Player.Player?> Player => PlayerManager.Instance.Get(PlayerId);
    
    public int GetKeyTyped() => Id;

    public virtual bool Equals(PlayerName? other) => other?.Id == Id;

    public override string ToString() => Name;

}