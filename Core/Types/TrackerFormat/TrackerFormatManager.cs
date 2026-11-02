namespace GooberTracker.Core.Types.TrackerFormat;

public class TrackerFormatManager : AbstractDirectusManager<TrackerFormat>
{
    protected override string TableName => "Tracker_Format";
    
    private static readonly Lazy<TrackerFormatManager> InstanceImpl = new(() => new TrackerFormatManager());
    public static TrackerFormatManager Instance => InstanceImpl.Value;
    
    public async Task<TrackerFormat?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );

    public async Task<List<TrackerFormat>> GetAll(int month, int day) => await GetAllImpl(
        x => x.Month == month && x.Day == day,
        new { month, day }
    );

    public async Task<List<TrackerFormat>> GetAll(DateTime date) => await GetAll(date.Month, date.Day);
}