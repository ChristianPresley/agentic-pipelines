package io.github.christianpresley.hello;

import static org.assertj.core.api.Assertions.assertThat;

import net.jqwik.api.ForAll;
import net.jqwik.api.Property;

class GreetingServicePropertyTest {

  private final GreetingService service = new GreetingService();

  @Property
  void greetingNeverNullAndAlwaysWellFormed(@ForAll final String name) {
    final String greeting = service.greet(name);
    assertThat(greeting).startsWith("Hello, ").endsWith("!");
  }

  @Property
  void sanitizedNameIsBoundedAndSafe(@ForAll final String name) {
    final String clean = GreetingService.sanitize(name);
    assertThat(clean).isNotBlank().hasSizeLessThanOrEqualTo(GreetingService.MAX_NAME_LENGTH);
    assertThat(clean).doesNotContainPattern("[<>\"'&/\\\\;]");
  }
}
