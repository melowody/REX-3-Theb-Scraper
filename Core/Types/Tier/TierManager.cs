using System.Text.Json;
using System.Text.Json.Nodes;
using Discord;
using Discord.Interactions;

namespace GooberTracker.Core.Types.Tier;

public class TierManager : AbstractDirectusManager<Tier>
{
    protected override string TableName => "Tier";
    
    private static readonly Lazy<TierManager> InstanceImpl = new(() => new TierManager());
    public static TierManager Instance => InstanceImpl.Value;
    
    
    private static JsonNode FixNode(string x)
    {
        var node = JsonNode.Parse(x)!;
        var data = node["data"]! as JsonArray;
        foreach (var ore in data!)
        {
            var names = ore!["global_requirement"] as JsonArray;
            var arr = new JsonArray();
            foreach (var item in names!)
            {
                arr.Add(item!["item"]!.GetValue<int>());
            }
            ore["global_requirement"] = arr;
        }
        return node;
    }
    
    public async Task<Tier?> Get(int id) => await GetImpl(
        x => x.Id == id,
        FixNode,
        new {id},
        new {fields = "*,global_requirement.item:Tier_Variant.Variant_id"}
    );
    
    public async Task<Tier?> Get(string name) => await GetImpl(
        x => x.Name == name,
        FixNode,
        new {name},
        new {fields = "*,global_requirement.item:Tier_Variant.Variant_id"}
    );

    public async Task<List<Tier>> GetAll(string name, int limit = 9999) => await GetAllImpl(
        x => name == "" || x.Name.Contains(name, StringComparison.CurrentCultureIgnoreCase),
        FixNode,
        name == "" ? null : new { name = new { _contains = name } },
        new { fields = "*,global_requirement.item:Tier_Variant.Variant_id", limit }
    );
    
    public class TierAutocompleteHandler : AutocompleteHandler
    {
        public override async Task<AutocompletionResult> GenerateSuggestionsAsync(IInteractionContext context, IAutocompleteInteraction autocompleteInteraction,
            IParameterInfo parameter, IServiceProvider services)
        {
            var ores = await Instance.GetAll(autocompleteInteraction.Data.Current.Value.ToString() ?? "", 25);
            Console.WriteLine($"[TierAutocompleteHandler] {JsonSerializer.Serialize(ores)}");
            return AutocompletionResult.FromSuccess(ores.Select(ore => new AutocompleteResult(ore.Name, ore.Id)).Take(25));
        }
    }
}