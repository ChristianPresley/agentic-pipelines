package io.github.christianpresley.hello;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Size;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** REST endpoints that return greetings. */
@RestController
@RequestMapping("/api")
@Validated
@Tag(name = "hello")
public class HelloController {

  private final GreetingService service;

  /**
   * Creates the controller.
   *
   * @param service the greeting service
   */
  public HelloController(final GreetingService service) {
    this.service = service;
  }

  /**
   * Returns a greeting.
   *
   * @param name optional name to greet
   * @return the greeting
   */
  @GetMapping("/hello")
  @Operation(summary = "Say hello")
  public Greeting hello(
      @RequestParam(name = "name", required = false) @Size(max = 200) final String name) {
    return new Greeting(service.greet(name));
  }
}
