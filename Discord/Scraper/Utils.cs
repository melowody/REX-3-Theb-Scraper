using System.Collections.Concurrent;
using System.Net;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading.Channels;
using Discord;
using Discord.Interactions;

namespace GooberTracker.Discord.Scraper;

public static class Utils
{
    public static async Task<string?> ReceiveAsync(this ClientWebSocket ws, CancellationToken cancellationToken)
    {
        var bytes = new byte[1024];
        using var stream = new MemoryStream();

        WebSocketReceiveResult res;

        do
        {
            res = await ws.ReceiveAsync(bytes, cancellationToken);
            
            if (res.MessageType == WebSocketMessageType.Close)
            {
                Console.WriteLine($"[ReceiveAsync] Close received: {res.CloseStatus} | {res.CloseStatusDescription}");

                if (ws.State == WebSocketState.CloseReceived)
                {
                    await ws.CloseOutputAsync(
                        WebSocketCloseStatus.NormalClosure,
                        "Blehhh",
                        CancellationToken.None
                    );
                }

                return null;
            }

            if (res.MessageType != WebSocketMessageType.Text) continue;
            
            stream.Write(bytes, 0, res.Count);
        } while (!res.EndOfMessage);
        
        return Encoding.UTF8.GetString(stream.ToArray());
    }

    public class AsyncStack<T>(CancellationTokenSource cts) where T : class
    {
        private readonly Stack<T> _stack = new();
        private readonly Lock _lock = new();
        private readonly SemaphoreSlim _semaphore = new(0);

        public void Push(T item)
        {
            lock (_lock)
            {
                _stack.Push(item);
            }
            
            _semaphore.Release();
        }

        public async Task<T?> Pop()
        {
            await _semaphore.WaitAsync(cts.Token);

            lock (_lock)
            {
                return _stack.Pop();
            }
        }
    }
    
    public abstract class JsonSender(CancellationTokenSource cts)
    {
        protected readonly CancellationTokenSource Cts = cts;
        
        public abstract Task<bool> ShouldHandle(JsonNode e);
        
        public abstract Task HandleEvent(JsonNode e, GooberScraper scraper);
    }

    private static readonly DateTime DiscordEpoch = new (2015, 01, 01, 0, 0, 0, DateTimeKind.Utc);
    
    public static DateTime FromDiscordSnowflake(this long num)
    {
        var millis = num >> 22;
        return DiscordEpoch.AddMilliseconds(millis);
    }

    public class ExtendedFormat<T>(T obj) : IFormattable where T : class
    {
        private readonly T _obj = obj;

        private static string Modify(string toFormat, string format)
        {
            return format switch
            {
                "lower" => toFormat.ToLower(),
                "upper" => toFormat.ToUpper(),
                _ => toFormat
            };
        }
        
        public string ToString(string? format, IFormatProvider? formatProvider)
        {
            var toFormat = _obj.ToString();
            if (string.IsNullOrEmpty(format)) return toFormat ?? "";
            return Modify(toFormat ?? "", format);
        }
    }

    public static ExtendedFormat<string> Extend(this string str) => new(str);

    public static async Task LogExceptions(Task awaitable)
    {
        try
        {
            await awaitable;
        }
        catch (Exception e)
        {
            Console.WriteLine($"Failed to run task: {e}");
        }
    }
    
    public record RobloxData(long Id, string Name);
    
    private static readonly HttpClient Client = new();

    private static long _lastCalled = 0L;

    public static async Task<RobloxData?> GetRobloxId(string name)
    {
        var response = await Client.PostAsync("https://users.roblox.com/v1/usernames/users", new StringContent($"{{\r\n  \"usernames\": [\r\n    \"{name}\"\r\n  ],\r\n  \"excludeBannedUsers\": false\r\n}}", null, "application/json"));

        var output = await response.Content.ReadAsStringAsync();
        
        Console.WriteLine($"[GetRobloxId] {output} | {response.StatusCode}");

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            Console.WriteLine($"[GetRobloxId] Poor status code!");
            return null;
        }

        if (JsonNode.Parse(output)?["data"] is not JsonArray data)
        {
            return null;
        }
        
        var id = data[0]?["id"]?.GetValue<long>();
        if (id == null)
        {
            Console.WriteLine($"[GetRobloxId] Couldn't get ID from: {data}");
            return null;
        }
        
        var username = data[0]?["name"]?.GetValue<string>();
        if (username != null) return new RobloxData(id.Value, username);
        Console.WriteLine($"[GetRobloxId] Couldn't get username from: {data}");
        return null;

    }

    public static async Task<List<string>?> GetRobloxNames(long id, string? cursor = null)
    {
        var curr = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        if (curr - _lastCalled < 60_000)
        {
            return null;
        }
        _lastCalled = curr;

        var cursorStr = cursor == null ? "" : "&cursor=" + cursor;
        var response =
            await Client.GetAsync($"https://users.roblox.com/v1/users/{id}/username-history?limit=100&sortOrder=Asc{cursorStr}");

        var responseStr = await response.Content.ReadAsStringAsync();
        
        Console.WriteLine($"[GetRobloxNames] {responseStr} | {response.StatusCode}");
        
        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            Console.WriteLine($"[GetRobloxNames] {e}");
            return null;
        }
        
        var data = JsonNode.Parse(responseStr);
        return
        [
            .. from entry in data?["data"] as JsonArray ?? []
            let name = entry?["name"]?.GetValue<string>()
            where name != null
            select name
        ];
    }
    
    public class PingAutocompleteHandler : AutocompleteHandler
    {
        public override Task<AutocompletionResult> GenerateSuggestionsAsync(IInteractionContext context, IAutocompleteInteraction autocompleteInteraction,
            IParameterInfo parameter, IServiceProvider services)
        {
            var curr = autocompleteInteraction.Data.Current.Value.ToString() ?? "";
            var roles = context.Guild.Roles.Where(x => x.IsMentionable && x.Name.Contains(curr, StringComparison.CurrentCultureIgnoreCase)).Select(x => $"<@&{x.Id}>").ToList();
            if (context.Guild.EveryoneRole.IsMentionable && "@everyone".Contains(curr, StringComparison.CurrentCultureIgnoreCase))
            {
                roles.Add("@everyone");
            }

            return Task.FromResult(AutocompletionResult.FromSuccess(roles.Select(role => new AutocompleteResult(role, role)).Take(25)));
        }
    }
    
}