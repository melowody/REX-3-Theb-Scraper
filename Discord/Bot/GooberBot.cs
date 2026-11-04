using Discord;
using Discord.Interactions;
using Discord.WebSocket;
using GooberTracker.Discord.Bot.Command;
using GooberTracker.Discord.Scraper;

namespace GooberTracker.Discord.Bot;

public class GooberBot : DiscordSocketClient
{

    private readonly InteractionService _service;
    private readonly IServiceProvider? _provider;
    private readonly EventTracker _tracker;

    private readonly List<Type> _modules =
    [
        typeof(EpinephrineCommand),
        typeof(IndexCommand),
        typeof(AdjustedCommand),
        typeof(CaveCommand),
        typeof(RegisterCommand),
        typeof(RemoveCommand)
    ];
    
    private bool _commandsRegistered;

    public static readonly List<ulong> Owners =
    [
        190804082032640000,
        252243543555309586,
        227916041567731722,
        797942648932794398,
        1409298754145747086
    ];
    
    public GooberBot(IServiceProvider? provider = null)
    {
       _provider = provider;
       _service = new InteractionService(this, new InteractionServiceConfig()
       {
           EnableAutocompleteHandlers = true
       });
       _tracker = new EventTracker(this);

       InteractionCreated += InteractionHandler;
       AutocompleteExecuted += InteractionHandler;
       Ready += RegisterCommands;

       _service.Log += message =>
       {
           Console.WriteLine($"[InteractionService] {message}");
           return Task.CompletedTask;
       };
    }

    public override async Task StartAsync()
    {
        foreach (var module in _modules)
        {
            await _service.AddModuleAsync(module, _provider);
        }
        
        _ = Task.Run(() => Utils.LogExceptions(SendEvents(CancellationToken.None)));
        _ = Task.Run(() => Utils.LogExceptions(UploadPlayer(CancellationToken.None)));
        
        await LoginAsync(TokenType.Bot, Environment.GetEnvironmentVariable("BOT_TOKEN"));
        await base.StartAsync();
    }

    private async Task InteractionHandler(SocketInteraction interaction)
    {
        var context = new SocketInteractionContext(this, interaction);
        var result = await _service.ExecuteCommandAsync(context, _provider);
        if (!result.IsSuccess)
        {
            Console.WriteLine($"Result failed: {result.Error} | {result.ErrorReason}");
        }
    }

    private async Task RegisterCommands()
    {
        if (_commandsRegistered) return;

        await _service.RegisterCommandsGloballyAsync();
        _commandsRegistered = true;
    }

    private async Task SendEvents(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            var track = await Scraper.Sender.Scraper.GetTrack();
            if (track == null) continue;
            Console.WriteLine("[Bot] Got track!");
            try
            {
                var messages = await _tracker.GetEvents(track);
                foreach (var message in messages)
                {
                    await message.SendMessages();
                }
            }
            catch (Exception e)
            {
                Console.WriteLine($"ERROR: {e}");
            }
        }
    }

    private static async Task UploadPlayer(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            var data = await RegisterCommand.Ids.Pop();
            var uploaded = false;
            if (data == null) continue;
            try
            {
                uploaded = await RegisterCommand.UploadPlayerName(data);
            }
            catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
            {
                throw;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[UploadPlayer] Upload Failed: {ex}");
            }

            if (uploaded) continue;
            await Task.Delay(10_000, cancellationToken);
            RegisterCommand.Ids.Push(data);
        }
    }
    
}