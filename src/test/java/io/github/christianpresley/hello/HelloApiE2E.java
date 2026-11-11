package io.github.christianpresley.hello;

import static org.assertj.core.api.Assertions.assertThat;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;

/**
 * End-to-end checks against a running deployment (for example the container image). Enabled only
 * when {@code E2E_BASE_URL} is set, so regular builds skip it.
 */
@EnabledIfEnvironmentVariable(named = "E2E_BASE_URL", matches = "https?://.+")
class HelloApiE2E {

  private static String baseUrl;
  private static final HttpClient CLIENT =
      HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();

  @BeforeAll
  static void readBaseUrl() {
    baseUrl = System.getenv("E2E_BASE_URL").replaceAll("/+$", "");
  }

  private static HttpResponse<String> get(final String path) throws Exception {
    final HttpRequest request =
        HttpRequest.newBuilder(URI.create(baseUrl + path))
            .timeout(Duration.ofSeconds(10))
            .GET()
            .build();
    return CLIENT.send(request, HttpResponse.BodyHandlers.ofString());
  }

  @Test
  void greetsTheWorldByDefault() throws Exception {
    final HttpResponse<String> response = get("/api/hello");
    assertThat(response.statusCode()).isEqualTo(200);
    assertThat(response.headers().firstValue("Content-Type")).hasValueSatisfying(
        type -> assertThat(type).contains("application/json"));
    assertThat(response.body()).contains("Hello, World!");
  }

  @Test
  void greetsANamedUser() throws Exception {
    final HttpResponse<String> response = get("/api/hello?name=E2E");
    assertThat(response.statusCode()).isEqualTo(200);
    assertThat(response.body()).contains("Hello, E2E!");
  }

  @Test
  void rejectsOversizedNames() throws Exception {
    final HttpResponse<String> response = get("/api/hello?name=" + "a".repeat(201));
    assertThat(response.statusCode()).isEqualTo(400);
  }

  @Test
  void exposesLivenessAndReadiness() throws Exception {
    assertThat(get("/actuator/health/liveness").statusCode()).isEqualTo(200);
    assertThat(get("/actuator/health/readiness").statusCode()).isEqualTo(200);
  }

  @Test
  void publishesTheOpenApiContract() throws Exception {
    final HttpResponse<String> response = get("/v3/api-docs");
    assertThat(response.statusCode()).isEqualTo(200);
    assertThat(response.body()).contains("/api/hello");
  }

  @Test
  void doesNotLeakServerDetailsOnUnknownRoutes() throws Exception {
    final HttpResponse<String> response = get("/does-not-exist");
    assertThat(response.statusCode()).isEqualTo(404);
    assertThat(response.headers().firstValue("Server")).isEmpty();
    assertThat(response.body()).doesNotContain("Exception");
  }
}
