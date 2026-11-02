using System.Text.Json;
using System.Text.Json.Nodes;
using System.Web;

namespace GooberTracker.Core.Types.World;

public class WorldManager : AbstractDirectusManager<World>
{
    protected override string TableName => "World";

    private static readonly Lazy<WorldManager> InstanceImpl = new(() => new WorldManager());
    public static WorldManager Instance => InstanceImpl.Value;

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

    public async Task<World?> Get(int id) => await GetImpl(
        x => x.Id == id,
        FixNode,
        new {id},
        new {fields = "*,alt_name.item:Alt_Names.name"}
    );

    public async Task<World?> Get(string name) => await GetImpl(
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
        new {fields = "*,alt_name.item:Alt_Names.name"}
    );

}