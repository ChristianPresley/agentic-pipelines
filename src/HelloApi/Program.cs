using HelloApi;

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.ConfigureKestrel(o => o.AddServerHeader = false);
builder.Services.AddSingleton<GreetingService>();
builder.Services.AddProblemDetails();
builder.Services.AddOpenApi();
builder.Services.AddHealthChecks();

var app = builder.Build();

app.UseExceptionHandler();
app.UseStatusCodePages();

app.MapOpenApi("/v3/api-docs");

app.MapGet("/api/hello", (string? name, GreetingService service) =>
        name is { Length: > 200 }
            ? Results.Problem(statusCode: StatusCodes.Status400BadRequest, detail: "Invalid request parameter")
            : Results.Ok(new Greeting(service.Greet(name))))
    .WithTags("hello")
    .WithSummary("Say hello");

app.MapHealthChecks("/actuator/health");
app.MapHealthChecks("/actuator/health/readiness");
app.MapHealthChecks("/actuator/health/liveness");

await app.RunAsync();

/// <summary>Entry point marker for integration tests.</summary>
#pragma warning disable CA1050 // WebApplicationFactory requires the top-level Program type
public partial class Program;
#pragma warning restore CA1050
