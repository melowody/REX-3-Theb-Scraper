using Discord;
using Discord.Interactions;
using GooberTracker.Core.Types.Event;
using GooberTracker.Core.Types.Multiplier;
using GooberTracker.Core.Types.Ore;
using GooberTracker.Core.Types.Spawn;
using GooberTracker.Core.Types.Spawner;
using GooberTracker.Core.Types.Variant;
using GooberTracker.Discord.Scraper;
using SmartFormat;

namespace GooberTracker.Discord.Bot.Command;

[Group("index", "Get information about an item in REx")]
[CommandContextType(InteractionContextType.BotDm, InteractionContextType.Guild, InteractionContextType.PrivateChannel)]
public class IndexCommand : InteractionModuleBase<SocketInteractionContext>
{

    private const string OreFormat = """
                                     ## {ore} ({tier})
                                     {variants}

                                     Location: **{locations}**
                                     {_event}
                                     """;

    private struct VariantComparer(string name, long rarity)
    {
        public readonly string Name = name;
        public readonly long Rarity = rarity;
    }
    
    [SlashCommand("ore", "Get information about a REx Ore")]
    [CommandContextType(InteractionContextType.BotDm, InteractionContextType.Guild, InteractionContextType.PrivateChannel)]
    public async Task Ore([Summary("ore"), Autocomplete(typeof(OreManager.OreAutocompleteHandler))] int oreId)
    {
        await DeferAsync();
        
        var ore = await OreManager.Instance.Get(oreId);
        if (ore == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "You must enter a valid Ore!");
            return;
        }

        var tier = await ore.Tier;
        if (tier == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "Could not get Tier for Ore!");
            return;
        }

        var variants = await VariantManager.Instance.GetAll("");

        var spawns = await SpawnManager.Instance.GetAll(ore);
        List<Spawner> spawners = [];
        Spawn? chosen = null;
        var done = false;
        foreach (var spawn in spawns)
        {
            var spawner = await spawn.Spawner;
            if (spawner == null) continue;
            spawners.Add(spawner);
            if (done) continue;
            chosen = spawn;
            if (spawner.Type == SpawnerType.Layer) done = true;
        }

        List<VariantComparer> variantObjs = [];
        if (chosen != null)
        {
            foreach (var variant in variants)
            {
                var multi = await MultiplierManager.Instance.Get(variant, tier);
                if (multi == null) continue;
                variantObjs.Add(new VariantComparer( variant.Name, multi.Multi * chosen.Rarity ));
            }
        }
        variantObjs.Sort((x, y) => x.Rarity.CompareTo(y.Rarity));

        var oreEvent = await EventManager.Instance.Get(ore);
        var eventStr = oreEvent == null
            ? "This Ore does not have an Event."
            : $"Event Rarity: 1 in {oreEvent.Rarity:N0}";

        await ModifyOriginalResponseAsync(x => x.Content = Smart.Format(OreFormat, new
        {
            ore = ore.Name.Extend(),
            tier = tier.Name.Extend(),
            variants = string.Join('\n', variantObjs.Select(x => $"**{x.Name}**: 1 in {x.Rarity:N0}")).Extend(),
            locations = string.Join(", ", spawners.Select(x => x.Name)).Extend(),
            _event = eventStr
        }));

    }
    
}