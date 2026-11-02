using System.Net.WebSockets;
using System.Text.Json;
using System.Text.Json.Nodes;
using GooberTracker.Discord.Scraper.Sender;

namespace GooberTracker.Discord.Scraper;

public class GooberScraper
{

    public ClientWebSocket Socket = new();
    private static CancellationTokenSource _cts = new();
    
    private Utils.AsyncStack<JsonNode> _readQueue = new(_cts);
    public Utils.AsyncStack<JsonNode> WriteQueue = new(_cts);

    private readonly List<Utils.JsonSender> _senders = [
        new Heartbeat(_cts),
        new Reconnect(_cts),
        new Sender.Scraper(_cts)
    ];
    
    private static readonly Lazy<GooberScraper> InstanceImpl = new(() => new GooberScraper());
    public static GooberScraper Instance => InstanceImpl.Value;
    
    public async Task Start()
    {
        _cts = new CancellationTokenSource();
        Socket = new ClientWebSocket();
        await Socket.ConnectAsync(new Uri("wss://gateway.discord.gg/?v=10&encoding=json"), _cts.Token);
        _readQueue = new Utils.AsyncStack<JsonNode>(_cts);
        WriteQueue = new Utils.AsyncStack<JsonNode>(_cts);

        _ = Task.Run(async () =>
        {
            while (!_cts.IsCancellationRequested)
            {
                await Utils.LogExceptions(ReadLoop());
            }
        });
        _ = Task.Run(async () =>
        {
            while (!_cts.IsCancellationRequested)
            {
                await Utils.LogExceptions(ProcessLoop());
            }
        });
        _ = Task.Run(async () =>
        {
            while (!_cts.IsCancellationRequested)
            {
                await Utils.LogExceptions(WriteLoop());
            }
        });
    }

    public async Task Cancel()
    {
        await _cts.CancelAsync();
    }
    
    private async Task ReadLoop()
    {
        var message = await Socket.ReceiveAsync(_cts.Token);
        Console.WriteLine($"[Read] {message}");
        var e = JsonNode.Parse(message);
        if (e == null) return;
        _readQueue.Push(e);
    }

    private async Task ProcessLoop()
    {
        var message = _readQueue.Pop();
        if (message is not JsonObject) return;
        Console.WriteLine($"[Process] Processing: {message.ToString()[..Math.Min(message.ToString().Length, 500)]}");
        foreach (var sender in _senders)
        {
            Console.WriteLine($"[Process] Attempting Sender {sender.GetType().Name}");
            if (!await sender.ShouldHandle(message)) continue;
            Console.WriteLine("[Process] Sending...");
            _ = Utils.LogExceptions(sender.HandleEvent(message, this));
        }
    }

    private async Task WriteLoop()
    {
        var e = WriteQueue.Pop();
        if (e == null) return;
        Console.WriteLine($"[Write] {e}");
        try
        {
            await Socket.SendAsync(JsonSerializer.SerializeToUtf8Bytes(e), WebSocketMessageType.Text, true,
                _cts.Token);
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("[Write] Cancelled");
        }
    }
}