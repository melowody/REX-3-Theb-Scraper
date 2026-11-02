using System.Text.Json.Serialization;
using GooberTracker.Core.Types.Player;

namespace GooberTracker.Core.Types.Goober;

public record Goober(
   [property: JsonPropertyName("id")] int Id,
   [property: JsonPropertyName("discord_id")]
   string DiscordIdStr,
   [property: JsonPropertyName("player_id")]
   int PlayerId
) : IRExObject<int>
{
   public int GetKeyTyped() => Id;

   public virtual bool Equals(Goober? other) => other?.Id == Id;

   [JsonIgnore] public ulong DiscordId => ulong.Parse(DiscordIdStr);

   [JsonIgnore] public Task<Player.Player?> Player => PlayerManager.Instance.Get(PlayerId);
}