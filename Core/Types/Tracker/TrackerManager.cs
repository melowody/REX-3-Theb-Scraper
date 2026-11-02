namespace GooberTracker.Core.Types.Tracker;

public class TrackerManager : AbstractDirectusManager<Tracker>
{
    protected override string TableName => "Tracker";
    
    private static readonly Lazy<TrackerManager> InstanceImpl = new(() => new TrackerManager());
    public static TrackerManager Instance => InstanceImpl.Value;
    
    public async Task<Tracker?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id = id.ToString()}
    );
    
    public async Task<Tracker?> Get(long id) => await GetImpl(
        x => x.TrackerId == id,
        new {tracker_id = id.ToString()}
    );
}