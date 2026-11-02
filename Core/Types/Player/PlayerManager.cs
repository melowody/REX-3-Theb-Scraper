using System.Text.Json;
using System.Text.Json.Nodes;

namespace GooberTracker.Core.Types.Player;

public class PlayerManager : AbstractDirectusManager<Player>
{
    protected override string TableName => "Player";
    
    private static readonly Lazy<PlayerManager> InstanceImpl = new(() => new PlayerManager());
    public static PlayerManager Instance => InstanceImpl.Value;
    
    public async Task<Player?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );
    
    public async Task<Player?> FromRoblox(long id) => await GetImpl(
        x => x.RobloxId == id,
        new {roblox_id = id.ToString()}
    );

    public async Task<Player?> Add(long robloxId) => await PostImpl(
        new { roblox_id = robloxId.ToString() }
    );
}