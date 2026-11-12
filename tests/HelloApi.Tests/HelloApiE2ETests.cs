namespace HelloApi.Tests;

/// <summary>
/// End-to-end checks against a running deployment (for example the container image). Skipped
/// unless E2E_BASE_URL is set, so regular test runs ignore it.
/// </summary>
public class HelloApiE2ETests
{
    private static readonly string? BaseUrl = Environment.GetEnvironmentVariable("E2E_BASE_URL")?.TrimEnd('/');
    private static readonly HttpClient Client = new() { Timeout = TimeSpan.FromSeconds(10) };

    private static async Task<HttpResponseMessage> GetAsync(string path) =>
        await Client.GetAsync(new Uri($"{BaseUrl}{path}"), CancellationToken.None);

    [Fact]
    public async Task GreetsTheWorldByDefault()
    {
        if (BaseUrl is null) { return; }
        using var response = await GetAsync("/api/hello");
        Assert.Equal(System.Net.HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("application/json", response.Content.Headers.ContentType?.ToString());
        Assert.Contains("Hello, World!", await response.Content.ReadAsStringAsync(CancellationToken.None));
    }

    [Fact]
    public async Task GreetsANamedUser()
    {
        if (BaseUrl is null) { return; }
        using var response = await GetAsync("/api/hello?name=E2E");
        Assert.Contains("Hello, E2E!", await response.Content.ReadAsStringAsync(CancellationToken.None));
    }

    [Fact]
    public async Task RejectsOversizedNames()
    {
        if (BaseUrl is null) { return; }
        using var response = await GetAsync($"/api/hello?name={new string('a', 201)}");
        Assert.Equal(System.Net.HttpStatusCode.BadRequest, response.StatusCode);
    }

    [Theory]
    [InlineData("/actuator/health/liveness")]
    [InlineData("/actuator/health/readiness")]
    [InlineData("/v3/api-docs")]
    public async Task ExposesOperationalEndpoints(string path)
    {
        if (BaseUrl is null) { return; }
        using var response = await GetAsync(path);
        Assert.Equal(System.Net.HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task DoesNotLeakServerDetailsOnUnknownRoutes()
    {
        if (BaseUrl is null) { return; }
        using var response = await GetAsync("/does-not-exist");
        Assert.Equal(System.Net.HttpStatusCode.NotFound, response.StatusCode);
        Assert.False(response.Headers.Contains("Server"));
        Assert.DoesNotContain("Exception", await response.Content.ReadAsStringAsync(CancellationToken.None));
    }
}
