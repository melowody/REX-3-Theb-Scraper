namespace GooberTracker.Core.Types.Ping;

public class PingManager : AbstractDirectusManager<Ping>
{
    protected override string TableName => "Ping";
    
    private static readonly Lazy<PingManager> InstanceImpl = new(() => new PingManager());
    public static PingManager Instance => InstanceImpl.Value;
    
    public async Task<Ping?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );
    
    public async Task<Ping?> Get(Channel.Channel channel, Variant.Variant variant, Tier.Tier tier) => await GetImpl(
        x => x.InternalChannelId == channel.Id && x.VariantId == variant.Id && x.TierId == tier.Id,
        new {channel = channel.Id, variant = variant.Id, tier = tier.Id}
    );

    public async Task<Ping?> Add(Channel.Channel channel, Variant.Variant variant, Tier.Tier tier, string pingStr)
    {
        var ping = await Get(channel, variant, tier);
        if (ping != null)
        {
            return await PatchImpl(
                ping.Id,
                new { channel = channel.Id, variant = variant.Id, tier = tier.Id, ping = pingStr }
            );
        }
        return await PostImpl(
            new { channel = channel.Id, variant = variant.Id, tier = tier.Id, ping = pingStr }
        );
    }
        
}