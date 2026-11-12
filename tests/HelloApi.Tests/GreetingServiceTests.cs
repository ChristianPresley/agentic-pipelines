using HelloApi;

namespace HelloApi.Tests;

public class GreetingServiceTests
{
    private readonly GreetingService _service = new();

    [Theory]
    [InlineData(null, "Hello, World!")]
    [InlineData("   ", "Hello, World!")]
    [InlineData("Ada", "Hello, Ada!")]
    [InlineData("<script>alert(1)</script>", "Hello, scriptalert1script!")]
    public void GreetsByName(string? name, string expected) =>
        Assert.Equal(expected, _service.Greet(name));

    [Fact]
    public void TruncatesLongNames() =>
        Assert.Equal(GreetingService.MaxNameLength, GreetingService.Sanitize(new string('a', 500)).Length);

    [Fact]
    public void ShoutsInUpperCase() =>
        Assert.Equal("HELLO, ADA!", _service.Shout("ada"));

    [Theory]
    [InlineData("")]
    [InlineData("\u0000\u202e")]
    [InlineData("\r\n; DROP TABLE")]
    public void NeverReturnsUnsafeOutput(string input)
    {
        var result = GreetingService.Sanitize(input);
        Assert.NotEmpty(result);
        Assert.True(result.Length <= GreetingService.MaxNameLength);
        Assert.All(result, c => Assert.True(char.IsLetterOrDigit(c) || c is ' ' or '-' or '_' or '.'));
    }
}
