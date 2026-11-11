package io.github.christianpresley.hello;

/**
 * Response payload for the greeting endpoint.
 *
 * @param message the greeting text
 */
public record Greeting(String message) {}
