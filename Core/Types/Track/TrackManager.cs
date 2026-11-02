namespace GooberTracker.Core.Types.Track;

public class TrackManager : AbstractDirectusManager<Track>
{
    protected override string TableName => "Track";
    
    private static readonly Lazy<TrackManager> InstanceImpl = new(() => new TrackManager());
    public static TrackManager Instance => InstanceImpl.Value;
    
    public async Task<Track?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );

    public async Task<Track?> Post(Track track) => await PostImpl(
        new
        {
            variant = track.VariantId, ore = track.OreId, spawner = track.SpawnerId, @event = track.EventId,
            mined = track.MinedStr, player = track.PlayerStr, time = track.TimeStr
        }
    );
}