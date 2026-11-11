package io.github.christianpresley.hello;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Entry point for the Hello World REST API. */
@SpringBootApplication
public class HelloApplication {

  /**
   * Starts the application.
   *
   * @param args command line arguments
   */
  public static void main(final String[] args) {
    SpringApplication.run(HelloApplication.class, args);
  }
}
