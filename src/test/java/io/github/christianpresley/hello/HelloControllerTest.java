package io.github.christianpresley.hello;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(HelloController.class)
@Import({GreetingService.class, ApiExceptionHandler.class})
class HelloControllerTest {

  @Autowired private MockMvc mvc;

  @Test
  void returnsDefaultGreeting() throws Exception {
    mvc.perform(get("/api/hello"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.message").value("Hello, World!"));
  }

  @Test
  void returnsNamedGreeting() throws Exception {
    mvc.perform(get("/api/hello").param("name", "Ada"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.message").value("Hello, Ada!"));
  }

  @Test
  void rejectsOverlongName() throws Exception {
    mvc.perform(get("/api/hello").param("name", "x".repeat(201)))
        .andExpect(status().isBadRequest());
  }
}
