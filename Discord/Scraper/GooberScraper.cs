using System.Net;
using System.Net.WebSockets;
using System.Text.Json;
using System.Text.Json.Nodes;
using GooberTracker.Discord.Scraper.Sender;

namespace GooberTracker.Discord.Scraper;

public class GooberScraper
{
    private ClientWebSocket _socket = new();
    private CancellationTokenSource _cts = new();
    
    private Utils.AsyncStack<JsonNode> _readQueue;
    public Utils.AsyncStack<JsonNode> WriteQueue;

    private List<Utils.JsonSender> _senders = [];
    
    private static readonly Lazy<GooberScraper> InstanceImpl = new(() => new GooberScraper());
    public static GooberScraper Instance => InstanceImpl.Value;

    private readonly List<Task> _tasks = [];
    private readonly List<Task> _senderTasks = [];
    private readonly Lock _senderLock = new();

    private int _reconnecting;

    public GooberScraper()
    {
        WriteQueue = new Utils.AsyncStack<JsonNode>(_cts.Token);
        _readQueue = new Utils.AsyncStack<JsonNode>(_cts.Token);
    }

    public async Task Start()
    {
        _cts = new CancellationTokenSource();
        _senders =
        [
            new Heartbeat(_cts),
            new Reconnect(_cts),
            new Sender.Scraper(_cts)
        ];
        _socket = new ClientWebSocket();
        await _socket.ConnectAsync(new Uri("wss://gateway.discord.gg/?v=10&encoding=json"), _cts.Token);
        _readQueue = new Utils.AsyncStack<JsonNode>(_cts.Token);
        WriteQueue = new Utils.AsyncStack<JsonNode>(_cts.Token);

        _tasks.Add(Task.Run(async () =>
        {
            while (!_cts.IsCancellationRequested)
            {
                try
                {
                    await ReadLoop();
                }
                catch (OperationCanceledException) when (_cts.IsCancellationRequested)
                {
                    break;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[Read] Reader stopped: {ex}");
                    Restart();
                    break;
                }
            }
        }));
        _tasks.Add(Task.Run(async () =>
        {
            while (!_cts.IsCancellationRequested)
            {
                try
                {
                    await ProcessLoop();
                }
                catch (OperationCanceledException) when (_cts.IsCancellationRequested)
                {
                    break;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[Process] Processor stopped: {ex}");
                    Restart();
                    break;
                }
            }
        }));
        _tasks.Add(Task.Run(async () =>
        {
            while (!_cts.IsCancellationRequested)
            {
                try
                {
                    await WriteLoop();
                }
                catch (OperationCanceledException) when (_cts.IsCancellationRequested)
                {
                    break;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[Write] Writer stopped: {ex}");
                    Restart();
                    break;
                }
            }
        }));
    }

    private async Task Cancel()
    {
        await _cts.CancelAsync();

        try
        {
            await Task.WhenAll(_tasks);
            Task[] tasks;
            lock (_senderLock)
            {
                tasks = [.. _senderTasks];
                _senderTasks.Clear();
            }

            await Task.WhenAll(tasks);
        }
        finally
        {
            _tasks.Clear();
        }
    }

    public void Restart()
    {
        if (Interlocked.CompareExchange(ref _reconnecting, 1, 0) != 0) return;

        _ = Task.Run(async () =>
        {
            try
            {
                await Cancel();
                _socket.Dispose();
                await Task.Delay(1000);
                await Start();
            }
            catch (Exception e)
            {
                Console.WriteLine($"[Restart] Error: {e}");
            }
            finally
            {
                Interlocked.Exchange(ref _reconnecting, 0);
            }
        });
    }
    
    private async Task ReadLoop()
    {
        var message = await _socket.ReceiveAsync(_cts.Token);
        
        _cts.Token.ThrowIfCancellationRequested();

        if (message == null)
        {
            Console.WriteLine("[Read] No Message");
            throw new WebException("Socket connection closed");
        }
        
        Console.WriteLine($"[Read] {message}");
        var e = JsonNode.Parse(message);
        if (e == null) return;
        _readQueue.Push(e);
    }

    private async Task ProcessLoop()
    {
        var message = await _readQueue.Pop();
        _cts.Token.ThrowIfCancellationRequested();
        if (message is not JsonObject) return;
        Console.WriteLine($"[Process] Processing: {message.ToString()[..Math.Min(message.ToString().Length, 500)]}");
        foreach (var sender in _senders)
        {
            _cts.Token.ThrowIfCancellationRequested();
            Console.WriteLine($"[Process] Attempting Sender {sender.GetType().Name}");
            if (!await sender.ShouldHandle(message)) continue;
            _cts.Token.ThrowIfCancellationRequested();
            Console.WriteLine("[Process] Sending...");
            lock (_senderLock)
            {
                if (_cts.IsCancellationRequested) break;
                _senderTasks.RemoveAll(x => x.IsCompleted);
                _senderTasks.Add(Task.Run(() => Utils.LogExceptions(sender.HandleEvent(message, this))));
            }
        }
    }

    private async Task WriteLoop()
    {
        var e = await WriteQueue.Pop();
        
        _cts.Token.ThrowIfCancellationRequested();

        if (_socket.State != WebSocketState.Open)
        {
            Console.WriteLine("[Write] Connection Closed");
            return;
        }
        
        Console.WriteLine($"[Write] {e}");

        try
        {
            await _socket.SendAsync(JsonSerializer.SerializeToUtf8Bytes(e), WebSocketMessageType.Text, true, _cts.Token);
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("[Write] Cancelled");
        }
        catch (WebSocketException ex)
        {
            Console.WriteLine($"[Write] Error: {ex}");
        }
    }
}