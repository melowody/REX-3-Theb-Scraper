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

    public async Task<List<PlayerPing>> GetAll(Goober.Goober goober) => await GetAllImpl(
        x => x.GooberId == goober.Id,
        new { goober = goober.Id }
    );
    
    public async Task<List<PlayerPing>> GetAll(Channel.Channel channel) => await GetAllImpl(
        x => x.ChannelId == channel.Id,
        new { channel = channel.Id }
    );
    
    public async Task<PlayerPing?> Add(GetParams getParams, bool ping) => await UpsertImpl(
        Get,
        getParams,
        new { goober = getParams.Goober.Id, channel = getParams.Channel.Id, ping },
        new { goober = getParams.Goober.Id, channel = getParams.Channel.Id, ping }
    );
    
    public async Task<PlayerPing?> Add(Goober.Goober goober, Channel.Channel channel, bool ping) => await Add(new GetParams(goober, channel), ping);

    public async Task Remove(int id) => await DeleteImpl(id);
    
    public async Task Remove(Goober.Goober goober, Channel.Channel channel) =>
        await DeleteImpl((await Get(goober, channel))?.Id);

    public async Task Remove(Goober.Goober goober)
    {
        foreach (var ping in await GetAll(goober))
        {
            await Remove(ping.Id);
        }
    }
    
    public async Task Remove(Channel.Channel goober)
    {
        foreach (var ping in await GetAll(goober))
        {
            await Remove(ping.Id);
        }
    }
}