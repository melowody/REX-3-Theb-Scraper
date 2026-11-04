namespace GooberTracker.Core.Types.Channel;

public class ChannelManager : AbstractDirectusManager<Channel>
{
    protected override string TableName => "Channel";
    
    private static readonly Lazy<ChannelManager> InstanceImpl = new(() => new ChannelManager());
    public static ChannelManager Instance => InstanceImpl.Value;
    
    public async Task<Channel?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id = id.ToString()}
    );
    
    public async Task<Channel?> Get(long discordId) => await GetImpl(
        x => x.ChannelId == discordId,
        new {channel_id = discordId.ToString()}
    );

    public async Task<List<Channel>> GetAll(ChannelType type) => await GetAllImpl(
        x => x.Type == type,
        new
        {
            type = type switch
            {
                ChannelType.Beginner => "beginner",
                ChannelType.Global => "global",
                ChannelType.ServerGlobal => "server_global",
                _ => "player"
            }
        }
    );

    public async Task<Channel?> Add(long channelId, ChannelType type) => await UpsertImpl(
        Get,
        channelId,
        new
        {
            channel_id = channelId.ToString(), type = type switch
            {
                ChannelType.Beginner => "beginner",
                ChannelType.Global => "global",
                ChannelType.ServerGlobal => "server_global",
                _ => "player"
            }
        },
        new
        {
            channel_id = channelId.ToString(), type = type switch
            {
                ChannelType.Beginner => "beginner",
                ChannelType.Global => "global",
                ChannelType.ServerGlobal => "server_global",
                _ => "player"
            }
        }
    );
    
    public async Task Remove(int id) => await DeleteImpl(id);
}