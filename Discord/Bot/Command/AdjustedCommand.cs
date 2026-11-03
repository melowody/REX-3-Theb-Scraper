using Discord;
using Discord.Interactions;
using GooberTracker.Core.Types.Multiplier;
using GooberTracker.Core.Types.Ore;
using GooberTracker.Core.Types.Spawn;
using GooberTracker.Core.Types.Spawner;
using GooberTracker.Core.Types.Track;
using GooberTracker.Core.Types.Variant;
using GooberTracker.Discord.Scraper;
using SmartFormat;

namespace GooberTracker.Discord.Bot.Command;

public class AdjustedCommand : InteractionModuleBase<SocketInteractionContext>
{
    
    private const string AdjustedFormat = """
                                     ## {cave} (1 in {cave_rarity:N0})
                                     **Base Rarity**: 1 in {base_rarity:N0}
                                     **Adjusted Rarity**: 1 in {adjusted_rarity:N0}
                                     """;

    [SlashCommand("adjusted", "Get the adjusted information about a REx Ore")]
    [CommandContextType(InteractionContextType.BotDm, InteractionContextType.Guild,
        InteractionContextType.PrivateChannel)]
    public async Task Adjusted(
        [Summary("ore"), Autocomplete(typeof(OreManager.OreAutocompleteHandler))] int oreId,
        [Summary("variant"), Autocomplete(typeof(VariantManager.VariantAutocompleteHandler))] int variantId = 3
    )
    {
        var ore = await OreManager.Instance.Get(oreId);
        if (ore == null)
        {
            await RespondAsync("You must enter a valid Ore!", ephemeral: true);
            return;
        }
        
        var variant = await VariantManager.Instance.Get(variantId);
        if (variant == null)
        {
            await RespondAsync("You must enter a valid Variant!", ephemeral: true);
            return;
        }

        var tier = await ore.Tier;
        if (tier == null)
        {
            await RespondAsync("Could not find Tier for Ore!", ephemeral: true);
            return;
        }

        var multi = await MultiplierManager.Instance.Get(variant, tier);
        var multiplier = multi?.Multi ?? 1;

        var titleVariant = variant.Name == "Normal" ? "" : $"{variant.Name} ";
        var title = $"# {titleVariant}{ore.Name}";

        var spawns = await SpawnManager.Instance.GetAll(ore);
        foreach (var spawn in spawns)
        {
            var spawner = await spawn.Spawner;
            if (spawner == null || spawner.Type == SpawnerType.Cave) continue;
            var world = await spawner.World;
            if (world == null) continue;
            var gilded = await SpawnerManager.Instance.Get("Gilded Cave", world);
            if (gilded == null) continue;
            spawns.Add(new Spawn(-1, ore.Id, gilded.Id, $"{2.5 * spawn.Rarity}"));
            break;
        }

        List<string> entries = [];
        foreach (var spawn in spawns)
        {
            var spawner = await spawn.Spawner;
            if (spawner == null) continue;
            if (spawner.Type == SpawnerType.Layer) continue;
            var rarity = await new Track(-1, "", variant.Id, ore.Id, spawner.Id, null, "0", "", "").Rarity;
            entries.Add(Smart.Format(AdjustedFormat, new
            {
                cave = spawner.Name.Extend(),
                cave_rarity = spawner.CaveRarity ?? -1,
                base_rarity = rarity?.Base ?? -1.0,
                adjusted_rarity = rarity?.Adjusted ?? -1.0
            }));
        }

        await RespondAsync($"{title}\n{string.Join('\n', entries)}");
    }
    
}