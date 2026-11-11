package io.github.christianpresley.hello;

import static org.assertj.core.api.Assertions.assertThat;

import com.code_intelligence.jazzer.junit.FuzzTest;

/**
 * Coverage-guided fuzz target. Runs as a regression test over the stored corpus by default; set
 * {@code JAZZER_FUZZ=1} to fuzz.
 */
class GreetingServiceFuzzTest {

  private final GreetingService service = new GreetingService();

  @FuzzTest(maxDuration = "30s")
  void greetNeverThrowsAndStaysSafe(final byte[] data) {
    final String greeting = service.greet(new String(data, java.nio.charset.StandardCharsets.UTF_8));
    assertThat(greeting).startsWith("Hello, ").endsWith("!");
    assertThat(greeting).doesNotContain("<", ">", "\"");
  }
}
