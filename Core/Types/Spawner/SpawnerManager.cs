using Discord;
using Discord.Interactions;

namespace GooberTracker.Core.Types.Spawner;

public class SpawnerManager : AbstractDirectusManager<Spawner>
{
    protected override string TableName => "Spawner";
    
    private static readonly Lazy<SpawnerManager> InstanceImpl = new(() => new SpawnerManager());
    public static SpawnerManager Instance => InstanceImpl.Value;
    
    public async Task<Spawner?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );
    
    public async Task<Spawner?> Get(string name, World.World? world = null) => await GetImpl(
        x => x.Name == name && (world == null || world.Id == x.WorldId),
        world == null ? new {name} : new {name, world = world.Id}
    );

    private async Task<List<Spawner>> GetAll(string name) => await GetAllImpl(
        x => name == "" || x.Name.Contains(name, StringComparison.CurrentCultureIgnoreCase),
        name == "" ? null : new { name = new { _contains = name }}
    );
    
    public class CaveAutocompleteHandler : AutocompleteHandler
    {
        public override async Task<AutocompletionResult> GenerateSuggestionsAsync(IInteractionContext context, IAutocompleteInteraction autocompleteInteraction,
            IParameterInfo parameter, IServiceProvider services)
        {
            var caves = (await Instance.GetAll(autocompleteInteraction.Data.Current.Value.ToString() ?? "")).Where(x => x.Type == SpawnerType.Cave);
            return AutocompletionResult.FromSuccess(caves.Select(async cave => new AutocompleteResult(await this.GetName(cave), cave.Id)).Select(t => t.Result).Take(25));
        }
    }
}