namespace GooberTracker.Core.Types.PlayerPing;

public class PlayerPingManager : AbstractDirectusManager<PlayerPing>
{
    public record GetParams(Goober.Goober Goober, Channel.Channel Channel);
    
    protected override string TableName => "Player_Ping";
    
    private static readonly Lazy<PlayerPingManager> InstanceImpl = new(() => new PlayerPingManager());
    public static PlayerPingManager Instance => InstanceImpl.Value;
    
    public async Task<PlayerPing?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );
    
    public async Task<PlayerPing?> Get(Goober.Goober goober, Channel.Channel channel) => await GetImpl(
        x => x.GooberId == goober.Id && x.ChannelId == channel.Id,
        new {goober = goober.Id, channel = channel.Id}
    );

    public async Task<PlayerPing?> Get(GetParams getParams) => await Get(getParams.Goober, getParams.Channel);

    public async Task<PlayerPing?> Add(GetParams getParams, bool ping) => await UpsertImpl(
        Get,
        getParams,
        new { goober = getParams.Goober.Id, channel = getParams.Channel.Id, ping },
        new { goober = getParams.Goober.Id, channel = getParams.Channel.Id, ping }
    );
    
    public async Task<PlayerPing?> Add(Goober.Goober goober, Channel.Channel channel, bool ping) => await Add(new GetParams(goober, channel), ping);
}