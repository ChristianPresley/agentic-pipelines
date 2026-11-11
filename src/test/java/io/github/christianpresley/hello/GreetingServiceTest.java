package io.github.christianpresley.hello;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class GreetingServiceTest {

  private final GreetingService service = new GreetingService();

  @Test
  void greetsDefaultWhenNull() {
    assertThat(service.greet(null)).isEqualTo("Hello, World!");
  }

  @Test
  void greetsDefaultWhenBlank() {
    assertThat(service.greet("   ")).isEqualTo("Hello, World!");
  }

  @Test
  void greetsByName() {
    assertThat(service.greet("Ada")).isEqualTo("Hello, Ada!");
  }

  @Test
  void stripsUnsafeCharacters() {
    assertThat(service.greet("<script>alert(1)</script>")).isEqualTo("Hello, scriptalert1script!");
  }

  @Test
  void truncatesLongNames() {
    final String result = GreetingService.sanitize("a".repeat(500));
    assertThat(result).hasSize(GreetingService.MAX_NAME_LENGTH);
  }

  @Test
  void shoutsInUpperCase() {
    assertThat(service.shout("ada")).isEqualTo("HELLO, ADA!");
  }
}
