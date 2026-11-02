namespace GooberTracker.Core.Types.Multiplier;

public class MultiplierManager : AbstractDirectusManager<Multiplier>
{
    protected override string TableName => "Multiplier";
    
    private static readonly Lazy<MultiplierManager> InstanceImpl = new(() => new MultiplierManager());
    public static MultiplierManager Instance => InstanceImpl.Value;
    
    public async Task<Multiplier?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );
    
    public async Task<Multiplier?> Get(Variant.Variant variant, Tier.Tier tier) => await GetImpl(
        x => x.VariantId == variant.Id && x.TierId == tier.Id,
        new {variant = variant.Id, tier = tier.Id}
    );
}