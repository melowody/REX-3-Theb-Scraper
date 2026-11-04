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
    public static readonly Utils.AsyncStack<Utils.RobloxData> Ids = new(CancellationToken.None);

    public static async Task UploadPlayerName(Utils.RobloxData data)
    {
        var player = await PlayerManager.Instance.Get(data.Id);
        if (player == null)
        {
            return;
        }
        
        var robloxNames = await Utils.GetRobloxNames(data.Id);
        if (robloxNames == null)
        {
            return;
        }

        var currNames = await PlayerNameManager.Instance.GetAll(player);
        if (robloxNames.All(x => x != data.Name)) robloxNames.Add(data.Name);
        robloxNames = [.. robloxNames.Where(x => currNames.All(y => y.Name != x))];
        
        foreach (var robloxName in robloxNames)
        {
            await PlayerNameManager.Instance.AddPlayer(player.Id, robloxName);
        }
    }
    
    [SlashCommand("player", "Register to the bot!")]
    [CommandContextType(InteractionContextType.BotDm, InteractionContextType.Guild,
        InteractionContextType.PrivateChannel)]
    public async Task Player(string name, bool ping, IUser? user = null)
    {
        await DeferAsync(ephemeral: true);
        
        var curr = Context.Interaction.User;
        if (user != null)
        {
            if (!GooberBot.Owners.Contains(Context.Interaction.User.Id))
            {
                await ModifyOriginalResponseAsync(x => x.Content = "You must be an owner of the bot to do this!");
                return;
            }
            curr = user as SocketUser;
        }

        if (curr == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "Couldn't find the correct user, please contact Mel");
            return;
        }
        
        var robloxId = await Utils.GetRobloxData(name);
        if (robloxId == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "Couldn't get user ID, try again in a minute");
            return;
        }
        
        var player = await PlayerManager.Instance.Get(robloxId.Id) ?? await PlayerManager.Instance.Add(robloxId.Id);
        if (player == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "Couldn't access CMS, please contact Mel pweaaseeeee :3");
            return;
        }
        
        Ids.Push(robloxId);

        var currGoob = await GooberManager.Instance.Add(curr.Id, player);

        var guild = Context.Guild;
        foreach (var discordChannel in await ((IGuild)guild).GetChannelsAsync())
        {
            var channel = await ChannelManager.Instance.Get((long)discordChannel.Id);
            if (channel is not { Type: ChannelType.Player } || currGoob == null) continue;
            await PlayerPingManager.Instance.Add(currGoob, channel, ping);
        }

        await ModifyOriginalResponseAsync(x => x.Content = "Welcome...... To Gooberville.....");
    }

    [SlashCommand("channel", "Register a channel!")]
    [CommandContextType(InteractionContextType.Guild)]
    public async Task Channel(ChannelType type)
    {
        await DeferAsync(ephemeral: true);
        
        if (Context.Interaction.User is not SocketGuildUser user || !(user.GuildPermissions.ManageChannels || GooberBot.Owners.Contains(user.Id)))
        {
            await ModifyOriginalResponseAsync(x => x.Content = "You must have the `Manage Channels` permission dummy!");
            return;
        }

        if (await ChannelManager.Instance.Add(Context.Channel.Id, type) == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "Couldn't access directus, please message Mel");
            return;
        }
        await ModifyOriginalResponseAsync(x => x.Content = $"Channel subscribed to {type} tracks!");
    }
    
    [SlashCommand("ping", "Register the pings for the channel!")]
    [CommandContextType(InteractionContextType.Guild)]
    public async Task Ping(
        [Summary("variant"), Autocomplete(typeof(VariantManager.VariantAutocompleteHandler))] int variantId,
        [Summary("tier"), Autocomplete(typeof(TierManager.TierAutocompleteHandler))] int tierId,
        [Summary("ping"), Autocomplete(typeof(Utils.PingAutocompleteHandler))] string pingStr
    )
    {
        await DeferAsync(ephemeral: true);
        
        if (Context.Interaction.User is not SocketGuildUser user || !(user.GuildPermissions.ManageChannels || GooberBot.Owners.Contains(user.Id)))
        {
            await ModifyOriginalResponseAsync(x => x.Content = "You must have the `Manage Channels` permission dummy!");
            return;
        }

        var channel = await ChannelManager.Instance.Get((long)Context.Channel.Id);
        if (channel == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "This channel isn't attached to the bot!");
            return;
        }

        var variant = await VariantManager.Instance.Get(variantId);
        if (variant == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "You silly, you gotta enter a valid variant!");
            return;
        }
        
        var tier = await TierManager.Instance.Get(tierId);
        if (tier == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "You silly, you gotta enter a valid tier!");
            return;
        }

        await PingManager.Instance.Add(channel, variant, tier, pingStr);
        await ModifyOriginalResponseAsync(x => x.Content = "Signed up channel for pings");
    }
    
}