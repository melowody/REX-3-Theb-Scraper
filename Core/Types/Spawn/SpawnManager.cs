namespace GooberTracker.Core.Types.Spawn;

public class SpawnManager : AbstractDirectusManager<Spawn>
{
    protected override string TableName => "Spawn";
    
    private static readonly Lazy<SpawnManager> InstanceImpl = new(() => new SpawnManager());
    public static SpawnManager Instance => InstanceImpl.Value;
    
    public async Task<Spawn?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );
    
    public async Task<Spawn?> Get(Ore.Ore ore, Spawner.Spawner spawner) => await GetImpl(
        x => x.OreId == ore.Id && x.SpawnerId == spawner.Id,
        new {ore = ore.Id, spawner = spawner.Id}
    );

    public async Task<List<Spawn>> GetAll(Ore.Ore ore) => await GetAllImpl(
        x => x.OreId == ore.Id,
        new {ore = ore.Id}
    );
    
    public async Task<List<Spawn>> GetAll(Spawner.Spawner spawner) => await GetAllImpl(
        x => x.SpawnerId == spawner.Id,
        new {spawner = spawner.Id}
    );

}