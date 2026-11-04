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

[Group("remove", "Remove something from the bot!")]
[CommandContextType(InteractionContextType.BotDm, InteractionContextType.Guild, InteractionContextType.PrivateChannel)]
public class RemoveCommand : InteractionModuleBase<SocketInteractionContext>
{
    
    [SlashCommand("player", "Remove a player from the bot!")]
    [CommandContextType(InteractionContextType.Guild)]
    public async Task Player(IUser? user = null)
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
        
        var currGoob = await GooberManager.Instance.Get(curr.Id);
        if (currGoob == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "Couldn't link discord, please try again");
            return;
        }
        
        var player = await currGoob.Player;
        if (player == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "Player either doesn't exist, or couldn't contact the CMS.");
            return;
        }

        var guild = Context.Guild;
        foreach (var discordChannel in await ((IGuild)guild).GetChannelsAsync())
        {
            var channel = await ChannelManager.Instance.Get((long)discordChannel.Id);
            if (channel is not { Type: ChannelType.Player or ChannelType.ServerGlobal }) continue;
            await PlayerPingManager.Instance.Remove(currGoob, channel);
        }

        await PlayerPingManager.Instance.Remove(currGoob);
        await GooberManager.Instance.Remove(currGoob.Id);
        await PlayerManager.Instance.Remove(player.Id);

        await ModifyOriginalResponseAsync(x => x.Content = "Goodbye...... From Gooberville.....");
    }

    [SlashCommand("channel", "Register a channel!")]
    [CommandContextType(InteractionContextType.Guild)]
    public async Task Channel()
    {
        await DeferAsync(ephemeral: true);
        
        if (Context.Interaction.User is not SocketGuildUser user || !(user.GuildPermissions.ManageChannels || GooberBot.Owners.Contains(user.Id)))
        {
            await ModifyOriginalResponseAsync(x => x.Content = "You must have the `Manage Channels` permission dummy!");
            return;
        }

        var channel = await ChannelManager.Instance.Get((long)Context.Channel.Id);
        if (channel == null) {
            await ModifyOriginalResponseAsync(x => x.Content = "Either channel doesn't exist, or couldn't access CMS.");
            return;
        }

        await PingManager.Instance.Remove(channel);
        await PlayerPingManager.Instance.Remove(channel);
        await ChannelManager.Instance.Remove(channel.Id);

        await ModifyOriginalResponseAsync(x => x.Content = "Channel removed from tracks!");
    }
    
    [SlashCommand("ping", "Register the pings for the channel!")]
    [CommandContextType(InteractionContextType.Guild)]
    public async Task Ping(
        [Summary("variant"), Autocomplete(typeof(VariantManager.VariantAutocompleteHandler))] int variantId,
        [Summary("tier"), Autocomplete(typeof(TierManager.TierAutocompleteHandler))] int tierId
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

        var ping = await PingManager.Instance.Get(channel, variant, tier);
        if (ping == null)
        {
            await ModifyOriginalResponseAsync(x => x.Content = "Couldn't get ping from CMS, if it exists, contact Mel.");
            return;
        }

        await PingManager.Instance.Remove(ping.Id);
        await ModifyOriginalResponseAsync(x => x.Content = "Removed channel from pings");
    }
    
}