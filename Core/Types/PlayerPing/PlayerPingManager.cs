namespace GooberTracker.Core.Types.PlayerPing;

public class PlayerPingManager : AbstractDirectusManager<PlayerPing>
{
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

    public async Task<PlayerPing?> Add(Goober.Goober goober, Channel.Channel channel, bool ping)
    {
        var playerPing = await Get(goober, channel);
        if (playerPing != null)
        {
            return await PatchImpl(
                playerPing.Id,
                new { goober = goober.Id, channel = channel.Id, ping }
            );
        }
        return await PostImpl(
            new { goober = goober.Id, channel = channel.Id, ping }
        ); 
    }
}