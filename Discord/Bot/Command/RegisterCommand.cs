using System.Text.Json;
using System.Text.Json.Nodes;
using Discord;
using Discord.Interactions;
using Discord.WebSocket;
using GooberTracker.Core.Types.Channel;
using GooberTracker.Core.Types.Goober;
using GooberTracker.Core.Types.Ping;
using GooberTracker.Core.Types.Player;
using GooberTracker.Core.Types.PlayerName;
using GooberTracker.Core.Types.PlayerPing;
using GooberTracker.Core.Types.Tier;
using GooberTracker.Core.Types.Variant;
using GooberTracker.Discord.Scraper;
using ChannelType = GooberTracker.Core.Types.Channel.ChannelType;

namespace GooberTracker.Discord.Bot.Command;

[Group("register", "Register something to the bot!")]
[CommandContextType(InteractionContextType.BotDm, InteractionContextType.Guild, InteractionContextType.PrivateChannel)]
public class RegisterCommand : InteractionModuleBase<SocketInteractionContext>
{
    [SlashCommand("player", "Register to the bot!")]
    [CommandContextType(InteractionContextType.BotDm, InteractionContextType.Guild,
        InteractionContextType.PrivateChannel)]
    public async Task Player(string name, bool ping, IUser? user = null)
    {
        var curr = Context.Interaction.User;
        if (user != null)
        {
            if (!GooberBot.Owners.Contains(Context.Interaction.User.Id))
            {
                await RespondAsync("You must be an owner of the bot to do this!", ephemeral: true);
                return;
            }
            curr = user as SocketUser;
        }

        if (curr == null)
        {
            await RespondAsync("Couldn't find the correct user, please contact Mel", ephemeral: true);
            return;
        }
        
        var robloxId = await Utils.GetRobloxId(name);
        if (robloxId == null)
        {
            await RespondAsync("Couldn't get user ID, try again in a minute", ephemeral: true);
            return;
        }
        
        var player = await PlayerManager.Instance.FromRoblox(robloxId.Id) ?? await PlayerManager.Instance.Add(robloxId.Id);
        if (player == null)
        {
            await RespondAsync("Couldn't access CMS, please contact Mel pweaaseeeee :3", ephemeral: true);
            return;
        }

        var robloxNames = await Utils.GetRobloxNames(robloxId.Id);
        if (robloxNames == null)
        {
            await RespondAsync("Couldn't get names, try again in a minute", ephemeral: true);
            return;
        }

        var currNames = await PlayerNameManager.Instance.GetAll(player);
        if (robloxNames.All(x => x != robloxId.Name)) robloxNames.Add(robloxId.Name);
        robloxNames = [.. robloxNames.Where(x => currNames.All(y => y.Name != x))];

        foreach (var robloxName in robloxNames)
        {
            await PlayerNameManager.Instance.AddPlayer(player.Id, robloxName);
        }

        var currGoob = await GooberManager.Instance.Get(curr.Id);
        if (currGoob != null)
        {
            await GooberManager.Instance.Patch(currGoob.Id, curr.Id, player);
        }
        else
        {
            currGoob = await GooberManager.Instance.Add(curr.Id, player);
        }

        if (currGoob != null)
        {
            var channel = await ChannelManager.Instance.Get((long)Context.Channel.Id);
            if (channel != null)
            {
                var playerPing = await PlayerPingManager.Instance.Get(currGoob, channel);
                if (playerPing == null)
                {
                    await PlayerPingManager.Instance.Add(currGoob, channel, ping);
                }
                else
                {
                    await PlayerPingManager.Instance.Patch(playerPing.Id, currGoob, channel, ping);
                }
            }
        }

        await RespondAsync("Welcome...... To Gooberville.....", ephemeral: true);
    }

    [SlashCommand("channel", "Register a channel!")]
    [CommandContextType(InteractionContextType.Guild)]
    public async Task Channel(ChannelType type)
    {
        if (Context.Interaction.User is not SocketGuildUser user || !user.GuildPermissions.ManageChannels)
        {
            await RespondAsync("You must have the `Manage Channels` permission dummy!", ephemeral: true);
            return;
        }

        if (await ChannelManager.Instance.AddChannel(Context.Channel.Id, type) == null)
        {
            await RespondAsync("Couldn't access directus, please message Mel", ephemeral: true);
            return;
        }
        await RespondAsync($"Channel subscribed to {type} tracks!", ephemeral: true);
    }
    
    [SlashCommand("ping", "Register the pings for the channel!")]
    [CommandContextType(InteractionContextType.Guild)]
    public async Task Ping(
        [Summary("variant"), Autocomplete(typeof(VariantManager.VariantAutocompleteHandler))] int variantId,
        [Summary("tier"), Autocomplete(typeof(TierManager.TierAutocompleteHandler))] int tierId,
        string pingStr
    )
    {
        if (Context.Interaction.User is not SocketGuildUser user || !user.GuildPermissions.ManageChannels)
        {
            await RespondAsync("You must have the `Manage Channels` permission dummy!", ephemeral: true);
            return;
        }

        var channel = await ChannelManager.Instance.Get((long)Context.Channel.Id);
        if (channel == null)
        {
            await RespondAsync("This channel isn't attached to the bot!", ephemeral: true);
            return;
        }

        var variant = await VariantManager.Instance.Get(variantId);
        if (variant == null)
        {
            await RespondAsync("You silly, you gotta enter a valid variant!", ephemeral: true);
            return;
        }
        
        var tier = await TierManager.Instance.Get(tierId);
        if (tier == null)
        {
            await RespondAsync("You silly, you gotta enter a valid tier!", ephemeral: true);
            return;
        }

        await PingManager.Instance.AddPing(channel, variant, tier, pingStr);
        await RespondAsync("Signed up channel for pings", ephemeral: true);
    }
    
}