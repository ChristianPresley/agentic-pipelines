using System.Text;

namespace HelloApi;

/// <summary>Builds greeting messages from user supplied names.</summary>
public sealed class GreetingService
{
    /// <summary>Name used when the caller supplies none.</summary>
    public const string DefaultName = "World";

    /// <summary>Maximum number of characters kept from a supplied name.</summary>
    public const int MaxNameLength = 50;

    public string Greet(string? name) => $"Hello, {Sanitize(name)}!";

    public string Shout(string? name) => Greet(name).ToUpperInvariant();

    /// <summary>Reduces a name to letters, digits, spaces and a few safe punctuation characters.</summary>
    public static string Sanitize(string? name)
    {
        if (name is null)
        {
            return DefaultName;
        }

        var sb = new StringBuilder();
        for (var i = 0; i < name.Length && sb.Length < MaxNameLength; i++)
        {
            var c = name[i];
            if (char.IsLetterOrDigit(c) || c is ' ' or '-' or '_' or '.')
            {
                sb.Append(c);
            }
        }

        var cleaned = sb.ToString().Trim();
        return cleaned.Length == 0 ? DefaultName : cleaned;
    }
}
