using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Web;
using Microsoft.Extensions.Caching.Memory;

namespace GooberTracker.Core;

/// <summary>
/// Interface <c>IRExObject</c> is the base for any object used in <c>AbstractManager</c>
/// </summary>
public interface IRExObject
{
    /// <summary>
    /// Gets the primary key used in the database for this object
    /// </summary>
    /// <returns>The primary key</returns>
    object? GetKey();
}

/// <summary>
/// Interface <c>IRExObject</c> is the base for any object used in <c>AbstractManager</c>
/// </summary>
public interface IRExObject<out T> : IRExObject
{
    new T GetKeyTyped();

    object? IRExObject.GetKey() => GetKeyTyped();
}

/// <summary>
/// Class <c>AbstractManager</c> is a base manager class for storing and retrieving objects<br />
/// It takes a generic type <c>T</c> to type check the inserted objects against
/// </summary>
public class AbstractManager<T> where T : IRExObject
{
    private List<T> Objects { get; } = [];

    /// <summary>
    /// Gets an item by its ID
    /// </summary>
    /// <param name="key">The ID to get the item by</param>
    /// <returns>The item, null if it does not exist</returns>
    public T? GetBy(object? key) => Objects.FirstOrDefault(x => Equals(x.GetKey(), key));

    /// <summary>
    /// Gets a shallow copy of the <c>AbstractManager</c>'s object list
    /// </summary>
    /// <returns>A shallow copy of the objects</returns>
    public List<T> GetAll() => [..Objects];

    /// <summary>
    /// Checks whether any object exists in the <c>AbstractManager</c>'s object list that satisfies the predicate function
    /// </summary>
    /// <param name="predicate">The function to check each object against</param>
    /// <returns>Whether the object exists in the <c>AbstractManager</c>'s object list</returns>
    public bool exists(Predicate<T>? predicate = null)
    {
        predicate ??= _ => true;
        return Objects.Any(x => predicate(x));
    }

    /// <summary>
    /// Adds an object to the <c>AbstractManager</c>'s object list if it doesn't exist<br />
    /// <br />
    /// Checking uses the <c>Equals</c> function in the <c>T</c> class
    /// </summary>
    /// <param name="obj">The object to add</param>
    public void Add(T obj)
    {
        if (!exists(o => o.Equals(obj)))
        {
            Objects.Add(obj);
        }
    }
    
    /// <summary>
    /// Gets a list of all objects in the <c>AbstractManager</c>'s object list that satisfy the predicate
    /// </summary>
    /// <param name="predicate">The function to check each object against</param>
    /// <returns>A list of all the objects that satisfy the predicate</returns>
    public List<T> Get(Predicate<T>? predicate = null) => Objects.FindAll(predicate ?? (_ => true));
    
    /// <summary>
    /// Deletes all objects in the <c>AbstractManager</c>'s object list that satisfy the predicate
    /// </summary>
    /// <param name="predicate">The function to check each object against</param>
    public void Delete(Predicate<T>? predicate = null) => Objects.RemoveAll(predicate ?? (_ => true));

    /// <summary>
    /// Gets a list of all objects in the <c>AbstractManager</c>'s object list that satisfy the predicate, 
    /// or creates an object if none exist
    /// </summary>
    /// <param name="factory">The function used to create a new object</param>
    /// <param name="predicate">The function to check each object against</param>
    /// <returns>A list of all objects that satisfy the predicate</returns>
    public List<T> Ensure(Func<T> factory, Predicate<T>? predicate = null)
    {
        var items = Get(predicate);
        if (items.Count > 0) return items;

        var o = factory();
        Add(o);
        return [o];
    }

    /// <summary>
    /// Adds an object to the <c>AbstractManager</c>'s object list, replacing the old object if it exists<br />
    /// <br />
    /// This uses the <c>Equals</c> function to check if the object exists
    /// </summary>
    /// <param name="obj">The object to add</param>
    public void Upsert(T obj)
    {
        Delete(x => x.Equals(obj));
        Add(obj);
    }
    
}

public record DirectusMetaObject(
    [property: JsonPropertyName("filter_count")]
    int FilterCount
);

public record DirectusGetResponse<T>(
    [property: JsonPropertyName("meta")]
    DirectusMetaObject? Meta,
    [property: JsonPropertyName("data")]
    List<T> Data
) where T : IRExObject;

public record DirectusPostResponse<T>(
    [property: JsonPropertyName("meta")]
    DirectusMetaObject? Meta,
    [property: JsonPropertyName("data")]
    T Data
) where T : IRExObject;

public abstract class AbstractDirectusManager<T> : AbstractManager<T> where T : class, IRExObject
{
    private record CacheResult(List<T> Value);

    private static readonly JsonSerializerOptions Options = new()
    {
        PropertyNameCaseInsensitive = true,
        Converters = { new JsonStringEnumConverter() }
    };

    private static HttpClient Client
    {
        get {
            if (field != null) return field;
            field = new HttpClient();
            field.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", Environment.GetEnvironmentVariable("DIRECTUS_KEY"));

            return field;
        }
    }

    protected abstract string TableName { get; }

    private string Url => $"https://directus.meluhdy.dev/items/{TableName}";

    private readonly MemoryCache _cache = new(new MemoryCacheOptions());

    private async Task<DirectusGetResponse<T>?> MakeRequest(
        Func<string, JsonNode> modifier,
        object? parameters = null,
        object? extraParameters = null
    )
    {
        var url = new Uri(Url);
        
        var builder = new UriBuilder(url);
        var query = HttpUtility.ParseQueryString(builder.Query);
        
        if (parameters != null) query["filter"] = JsonSerializer.Serialize(parameters);
        if (extraParameters != null)
        {
            foreach (var property in JsonSerializer.SerializeToElement(extraParameters).EnumerateObject()
                         .Where(property =>
                             property.Value.ValueKind is not (JsonValueKind.Null or JsonValueKind.Undefined)))
            {
                query[property.Name] = property.Value.ToString();
            }
        }

        builder.Query = query.ToString();
        url = builder.Uri;
        
        Console.WriteLine($"[{GetType().Name}] Get: {url}");

        var response = await Client.GetAsync(url);

        Console.WriteLine($"[{GetType().Name}] {response.StatusCode}");

        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();

        Console.WriteLine($"[{GetType().Name}] {json}");

        return JsonSerializer.Deserialize<DirectusGetResponse<T>>(modifier(json), Options);
    }

    private async Task<DirectusPostResponse<T>?> MakePost(
        Func<string, JsonNode> modifier,
        object data
    )
    {
        var url = new Uri(Url);
        
        Console.WriteLine($"[{GetType().Name}] Post: {url}");
        
        var content = JsonContent.Create(data);

        var response = await Client.PostAsync(url, content);
        
        Console.WriteLine($"[{GetType().Name}] {response.StatusCode}");

        response.EnsureSuccessStatusCode();
        
        var json = await response.Content.ReadAsStringAsync();

        Console.WriteLine($"[{GetType().Name}] {json}");

        return JsonSerializer.Deserialize<DirectusPostResponse<T>>(modifier(json), Options);
    }
    
    private async Task<DirectusPostResponse<T>?> MakePatch<TU>(
        Func<string, JsonNode> modifier,
        TU id,
        object data
    )
    {
        var url = new Uri($"{Url}/{id}");
        
        Console.WriteLine($"[{GetType().Name}] Patch: {url}");
        
        var content = JsonContent.Create(data);

        var response = await Client.PatchAsync(url, content);
        
        Console.WriteLine($"[{GetType().Name}] {response.StatusCode}");

        response.EnsureSuccessStatusCode();
        
        var json = await response.Content.ReadAsStringAsync();

        Console.WriteLine($"[{GetType().Name}] {json}");

        return JsonSerializer.Deserialize<DirectusPostResponse<T>>(modifier(json), Options);
    }
    
    private async Task MakeDelete<TU>(
        TU id
    )
    {
        var url = new Uri($"{Url}/{id}");
        
        Console.WriteLine($"[{GetType().Name}] Delete: {url}");

        var response = await Client.DeleteAsync(url);
        
        Console.WriteLine($"[{GetType().Name}] {response.StatusCode}");

        response.EnsureSuccessStatusCode();
    }

    protected async Task<List<T>> GetAllImpl(Predicate<T> predicate, Func<string, JsonNode> modifier, object? parameters = null, object? extraParameters = null)
    {
        var cacheString =
            $"[{GetType().Name}] Getting: {TableName}/{typeof(T).Name}/{JsonSerializer.Serialize(parameters, Options)}/{JsonSerializer.Serialize(extraParameters, Options)}";
        Console.WriteLine(cacheString);
        
        var result = await _cache.GetOrCreateAsync(
            cacheString,
            async x =>
            {
                x.AbsoluteExpirationRelativeToNow = TimeSpan.FromHours(5);

                var response = (await MakeRequest(modifier, parameters, extraParameters) ?? new DirectusGetResponse<T>(null, [])).Data;
                if (response.Count == 0) return new CacheResult([]);
        
                response.ForEach(Add);
                return new CacheResult(Get(predicate));
            }
        );

        return result?.Value ?? [];
    }

    protected async Task<List<T>> GetAllImpl(Predicate<T> predicate, object? parameters = null, object? extraParameters = null) =>
        await GetAllImpl(predicate, x => JsonNode.Parse(x)!, parameters, extraParameters);

    protected async Task<T?> GetImpl(Predicate<T> predicate, Func<string, JsonNode> modifier, object? parameters = null,
        object? extraParameters = null) =>
        (await GetAllImpl(predicate, modifier, parameters, extraParameters)).FirstOrDefault();

    protected async Task<T?> GetImpl(Predicate<T> predicate, object? parameters = null, object? extraParameters = null) =>
        await GetImpl(predicate, x => JsonNode.Parse(x)!, parameters, extraParameters);

    protected async Task<T?> PostImpl(object parameters) => (await MakePost(x => JsonNode.Parse(x)!, parameters))?.Data;
    
    protected async Task<T?> PatchImpl<TU>(Func<string, JsonNode> modifier, TU id, object data) => (await MakePatch(modifier, id, data))?.Data;
    
    protected async Task<T?> PatchImpl<TU>(TU id, object data) => await PatchImpl(x => JsonNode.Parse(x)!, id, data);

    protected async Task DeleteImpl<TU>(TU id) => await MakeDelete(id);

}