using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;

namespace HelloApi.Tests;

public class HelloApiTests(WebApplicationFactory<Program> factory) : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client = factory.CreateClient();

    [Fact]
    public async Task ReturnsDefaultGreeting()
    {
        var body = await _client.GetFromJsonAsync<Greeting>("/api/hello", CancellationToken.None);
        Assert.Equal("Hello, World!", body?.Message);
    }

    [Fact]
    public async Task ReturnsNamedGreeting()
    {
        var body = await _client.GetFromJsonAsync<Greeting>("/api/hello?name=Ada", CancellationToken.None);
        Assert.Equal("Hello, Ada!", body?.Message);
    }

    [Fact]
    public async Task RejectsOverlongName()
    {
        var response = await _client.GetAsync($"/api/hello?name={new string('x', 201)}", CancellationToken.None);
        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    [Theory]
    [InlineData("/health/live")]
    [InlineData("/health/ready")]
    [InlineData("/v3/api-docs")]
    public async Task ExposesOperationalEndpoints(string path)
    {
        var response = await _client.GetAsync(path, CancellationToken.None);
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }
}
