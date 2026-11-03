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
        await DeferAsync();
        
        var ore = await OreManager.Instance.Get(oreId);
        if (ore == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "You must enter a valid Ore!");
            return;
        }
        
        var variant = await VariantManager.Instance.Get(variantId);
        if (variant == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "You must enter a valid Variant!");
            return;
        }

        var tier = await ore.Tier;
        if (tier == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "Could not find Tier for Ore!");
            return;
        }

        var titleVariant = variant.Name == "Normal" ? "" : $"{variant.Name} ";
        var title = $"# {titleVariant}{ore.Name}";

        List<Spawner> spawners = [];
        var addedGilded = false;
        foreach (var spawn in await SpawnManager.Instance.GetAll(ore))
        {
            var spawner = await spawn.Spawner;
            if (spawner == null) continue;
            if (spawner.Type == SpawnerType.Cave) spawners.Add(spawner);
            if (spawner.Type == SpawnerType.Cave || addedGilded) continue;
            var world = await spawner.World;
            if (world == null) continue;
            var gilded = await SpawnerManager.Instance.Get("Gilded Cave", world);
            if (gilded == null) continue;
            spawners.Add(gilded);
            addedGilded = true;
        }

        List<string> entries = [];
        foreach (var spawner in spawners)
        {
            var rarity = await new Track(-1, "", variant.Id, ore.Id, spawner.Id, null, "0", "", "").Rarity;
            entries.Add(Smart.Format(AdjustedFormat, new
            {
                cave = spawner.Name.Extend(),
                cave_rarity = spawner.CaveRarity ?? -1,
                base_rarity = rarity?.Base ?? -1.0,
                adjusted_rarity = rarity?.Adjusted ?? -1.0
            }));
        }

        await ModifyOriginalResponseAsync(x => x.Content = $"{title}\n{string.Join('\n', entries)}");
    }
    
}