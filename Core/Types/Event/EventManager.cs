namespace GooberTracker.Core.Types.Event;

public class EventManager : AbstractDirectusManager<Event>
{
    protected override string TableName => "Event";
    
    private static readonly Lazy<EventManager> InstanceImpl = new(() => new EventManager());
    public static EventManager Instance => InstanceImpl.Value;
    
    public async Task<Event?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );
    
    public async Task<Event?> Get(Ore.Ore ore) => await GetImpl(
        x => x.OreId == ore.Id,
        new {ore = ore.Id}
    );
}