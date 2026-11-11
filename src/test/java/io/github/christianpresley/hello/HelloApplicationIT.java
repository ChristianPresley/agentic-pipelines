package io.github.christianpresley.hello;

import static org.assertj.core.api.Assertions.assertThat;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.SpringBootTest.WebEnvironment;
import org.springframework.boot.test.web.server.LocalServerPort;

@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class HelloApplicationIT {

  @LocalServerPort private int port;

  private String get(final String path) throws Exception {
    final HttpRequest request =
        HttpRequest.newBuilder(URI.create("http://localhost:" + port + path)).GET().build();
    return HttpClient.newHttpClient()
        .send(request, HttpResponse.BodyHandlers.ofString())
        .body();
  }

  @Test
  void helloEndpointResponds() throws Exception {
    assertThat(get("/api/hello?name=IT")).contains("Hello, IT!");
  }

  @Test
  void healthEndpointIsUp() throws Exception {
    assertThat(get("/actuator/health")).contains("UP");
  }

  @Test
  void onlyHealthIsExposedWithoutDetails() throws Exception {
    assertThat(get("/actuator")).doesNotContain("/actuator/info").doesNotContain("/actuator/env");
    assertThat(get("/actuator/health")).doesNotContain("components").doesNotContain("diskSpace");
  }

  @Test
  void openApiSpecIsPublished() throws Exception {
    assertThat(get("/v3/api-docs")).contains("/api/hello");
  }
}
