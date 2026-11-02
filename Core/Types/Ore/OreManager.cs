using System.Text.Json;
using System.Text.Json.Nodes;
using Discord;
using Discord.Interactions;

namespace GooberTracker.Core.Types.Ore;

public class OreManager : AbstractDirectusManager<Ore>
{
    protected override string TableName => "Ore";
    
    private static readonly Lazy<OreManager> InstanceImpl = new(() => new OreManager());
    public static OreManager Instance => InstanceImpl.Value;
    
    private static JsonNode FixNode(string x)
    {
        var node = JsonNode.Parse(x)!;
        var data = node["data"]! as JsonArray;
        foreach (var ore in data!)
        {
            var names = ore!["alt_name"] as JsonArray;
            var arr = new JsonArray();
            foreach (var item in names!)
            {
                arr.Add(item!["item"]!["name"]!.GetValue<string>());
            }
            ore["alt_name"] = arr;
        }
        return node;
    }
    
    public async Task<Ore?> Get(int id) => await GetImpl(
        x => x.Id == id,
        FixNode,
        new {id},
        new {fields = "*,alt_name.item:Alt_Names.name"}
    );
    
    public async Task<List<Ore>> GetAll(string name, int limit = 9999) => await GetAllImpl(
        x => name == "" || x.Name.Contains(name, StringComparison.CurrentCultureIgnoreCase) || x.AltNames.Any(y => y.Contains(name, StringComparison.CurrentCultureIgnoreCase)),
        FixNode,
        name == "" ? null : new Dictionary<string, object>
        {
            ["_or"] = new object[]
            {
                new { name = new { _contains = name } },
                new Dictionary<string, object>
                {
                    ["alt_name"] = new Dictionary<string, object>
                    {
                        ["item:Alt_Names"] = new { name = new { _contains = name } }
                    }
                }
            }
        },
        new { fields = "*,alt_name.item:Alt_Names.name", limit }
    );
    
    public async Task<Ore?> Get(string name) => await GetImpl(
        x => x.Name == name || x.AltNames.Contains(name),
        FixNode,
        new Dictionary<string, object>
        {
            ["_or"] = new object[]
            {
                new { name },
                new Dictionary<string, object>
                {
                    ["alt_name"] = new Dictionary<string, object>
                    {
                        ["item:Alt_Names"] = new { name }
                    }
                }
            }
        },
        new { fields = "*,alt_name.item:Alt_Names.name" }
    );
    
    public class OreAutocompleteHandler : AutocompleteHandler
    {
        public override async Task<AutocompletionResult> GenerateSuggestionsAsync(IInteractionContext context, IAutocompleteInteraction autocompleteInteraction,
            IParameterInfo parameter, IServiceProvider services)
        {
            var ores = await Instance.GetAll(autocompleteInteraction.Data.Current.Value.ToString() ?? "", 25);
            return AutocompletionResult.FromSuccess(ores.Select(ore => new AutocompleteResult(ore.Name, ore.Id)).Take(25));
        }
    }
    
}