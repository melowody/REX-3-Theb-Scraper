using Discord;
using Discord.Interactions;
using GooberTracker.Core.Types.Ore;
using GooberTracker.Core.Types.Spawn;
using GooberTracker.Core.Types.Spawner;

namespace GooberTracker.Discord.Bot.Command;

public class EpinephrineCommand : InteractionModuleBase<SocketInteractionContext>
{

    private static Spawn? GetOre(double roll, List<Spawn> spawns)
    {
        var adjusted = (1_000_000_000.0 - roll) / 999_999_999.0;
        var total = 0.0;
        foreach (var spawn in spawns.Where(spawn => spawn.Rarity > 0.0001))
        {
            total += 1.0 / spawn.Rarity;
            Console.WriteLine($"New total: {total}");
            if (total > adjusted)
            {
                return spawn;
            }
        }
        return spawns.FirstOrDefault(x => x.Rarity < 0.0001);
    }
    
    [SlashCommand("epinephrine", "Roll for Epinephrine!")]
    [CommandContextType(InteractionContextType.BotDm, InteractionContextType.Guild, InteractionContextType.PrivateChannel)]
    public async Task Epinephrine()
    {
        await DeferAsync();
        
        var roll = Random.Shared.NextDouble() * (1_000_000_000.0 - 1.0) + 1.0;

        var spawner = await SpawnerManager.Instance.Get("Moon Core Layer");
        Ore? ore = null;
        if (spawner != null)
        {
            var spawns = await SpawnManager.Instance.GetAll(spawner);
            if (spawns.Count > 0)
            {
                spawns.Sort((x, y) => x.Rarity < y.Rarity ? -1 : 1);
                
                var spawn = GetOre(roll, spawns);
                if (spawn != null) ore = await spawn.Ore;
            }
        }
        
        var floorRoll = (int)Math.Floor(roll);
        
        switch (floorRoll)
        {
            case 999_999_999:
                await ModifyOriginalResponseAsync(x =>
                {
                    x.Content = "**YOU GOT EPINEPHRINE!** @everyone\n(rolled 999,999,999)";
                    x.AllowedMentions = AllowedMentions.All;
                });
                break;
            case 1:
                await ModifyOriginalResponseAsync(x =>
                {
                    x.Content = "**YOU GOT...**as far away from Epinephrine as possible! @everyone\n(rolled 1)";
                    x.AllowedMentions = AllowedMentions.All;
                });
                break;
            default:
                if (ore == null)
                {
                    await ModifyOriginalResponseAsync(x => x.Content = $"You didn't get Epinephrine :c\n(got {floorRoll:N0} but needed 999,999,999)");
                }
                else
                {
                    await ModifyOriginalResponseAsync(x => x.Content = $"You got **{ore.Name}**!\n(got {floorRoll:N0} but needed 999,999,999)");
                }
                
                break;
        }
    }
}