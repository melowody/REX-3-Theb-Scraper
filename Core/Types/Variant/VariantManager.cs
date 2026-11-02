using System.Text.Json;
using Discord;
using Discord.Interactions;

namespace GooberTracker.Core.Types.Variant;

public class VariantManager : AbstractDirectusManager<Variant>
{
    protected override string TableName => "Variant";
    
    private static readonly Lazy<VariantManager> InstanceImpl = new(() => new VariantManager());
    public static VariantManager Instance => InstanceImpl.Value;
    
    public async Task<Variant?> Get(int id) => await GetImpl(
        x => x.Id == id,
        new {id}
    );

    public async Task<Variant?> Get(string name) => await GetImpl(
        x => x.Name == name,
        new {name}
    );

    public async Task<List<Variant>> GetAll(string name, int limit = 9999) => await GetAllImpl(
        x => name == "" || x.Name.Contains(name, StringComparison.CurrentCultureIgnoreCase),
        name == "" ? null : new { name = new { _contains = name } },
        new { limit }
    );
    
    public class VariantAutocompleteHandler : AutocompleteHandler
    {
        public override async Task<AutocompletionResult> GenerateSuggestionsAsync(IInteractionContext context, IAutocompleteInteraction autocompleteInteraction,
            IParameterInfo parameter, IServiceProvider services)
        {
            var ores = await Instance.GetAll(autocompleteInteraction.Data.Current.Value.ToString() ?? "", 25);
            return AutocompletionResult.FromSuccess(ores.Select(ore => new AutocompleteResult(ore.Name, ore.Id)).Take(25));
        }
    }

}