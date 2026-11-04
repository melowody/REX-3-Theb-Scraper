namespace GooberTracker.Core.Types.PlayerName;

public class PlayerNameManager : AbstractDirectusManager<PlayerName>
{
    protected override string TableName => "Player_Name";
    
    private static readonly Lazy<PlayerNameManager> InstanceImpl = new(() => new PlayerNameManager());
    public static PlayerNameManager Instance => InstanceImpl.Value;
    
    public async Task<PlayerName?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );
    
    public async Task<PlayerName?> Get(string name) => await GetImpl(
        x => x.Name == name,
        new {name}
    );
    
    public async Task<List<PlayerName>> GetAll(Player.Player player) => await GetAllImpl(
        x => x.PlayerId == player.Id,
        new {player = player.Id}
    );
    
    public async Task<PlayerName?> Add(int playerId, string name) => await PostImpl(
        new { player = playerId, name }
    );
    
    public async Task<PlayerName?> Add(Player.Player player, string name) => await Add(player.Id, name);

    public async Task Remove(int id) => await DeleteImpl(id);

    public async Task Remove(Player.Player player)
    {
        var names = await GetAll(player);
        foreach (var name in names)
        {
            await Remove(name.Id);
        }
    }
}