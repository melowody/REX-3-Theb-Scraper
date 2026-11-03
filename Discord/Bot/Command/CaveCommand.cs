using Discord;
using Discord.Interactions;
using GooberTracker.Core.Types.Spawn;
using GooberTracker.Core.Types.Spawner;
using GooberTracker.Discord.Scraper;
using SmartFormat;

namespace GooberTracker.Discord.Bot.Command;

public class CaveCommand : InteractionModuleBase<SocketInteractionContext>
{

    private const string CaveFormat = """
                                      # {cave}
                                      ## Rarity: 1 in {cave_rarity:N0}
                                      **Ores:**
                                      {ores}
                                      """;
    
    [SlashCommand("cave", "Get the  information about a REx Cave")]
    [CommandContextType(InteractionContextType.BotDm, InteractionContextType.Guild,
        InteractionContextType.PrivateChannel)]
    public async Task Cave([Summary("cave"), Autocomplete(typeof(SpawnerManager.CaveAutocompleteHandler))] int caveId)
    {
        await DeferAsync();
        
        var cave = await SpawnerManager.Instance.Get(caveId);
        if (cave == null)
        {
            Console.WriteLine("You must enter a valid Cave!");
            return;
        }

        var spawns = await SpawnManager.Instance.GetAll(cave);
        List<string> spawnList = [];
        foreach (var spawn in spawns)
        {
            var ore = await spawn.Ore;
            if (ore == null)
            {
                await ModifyOriginalResponseAsync(x => x.Content = $"Could not find ore: {spawn.OreId}");
                continue;
            }
            spawnList.Add($"{ore.Name}: 1 in {spawn.Rarity:N0}");
        }
        
        await ModifyOriginalResponseAsync(x => x.Content = Smart.Format(CaveFormat, new
        {
            cave = cave.Name.Extend(),
            cave_rarity = cave.CaveRarity ?? -1,
            ores = string.Join("\n", spawnList).Extend()
        }));
    }
    
}