namespace GooberTracker.Core.Types.Goober;

public class GooberManager : AbstractDirectusManager<Goober>
{
    protected override string TableName => "Goober";
    
    private static readonly Lazy<GooberManager> InstanceImpl = new(() => new GooberManager());
    public static GooberManager Instance => InstanceImpl.Value;
    
    public async Task<Goober?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );
    
    public async Task<Goober?> Get(ulong discordId) => await GetImpl(
        x => x.DiscordId == discordId,
        new { discord_id = discordId.ToString() }
    );

    public async Task<Goober?> Get(Player.Player player) => await GetImpl(
        x => x.PlayerId == player.Id,
        new { player_id = player.Id }
    );

    public async Task<Goober?> Add(ulong discordId, Player.Player player) => await UpsertImpl(
        Get,
        discordId,
        new { discord_id = discordId.ToString(), player_id = player.Id },
        new { discord_id = discordId.ToString(), player_id = player.Id }
    );

    public async Task Remove(int id) => await DeleteImpl(id);
}