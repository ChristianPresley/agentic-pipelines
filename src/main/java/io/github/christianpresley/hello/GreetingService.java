package io.github.christianpresley.hello;

import java.util.Locale;
import org.springframework.stereotype.Service;

/** Builds greeting messages from user supplied names. */
@Service
public class GreetingService {

  /** Name used when the caller supplies none. */
  public static final String DEFAULT_NAME = "World";

  /** Maximum number of characters kept from a supplied name. */
  public static final int MAX_NAME_LENGTH = 50;

  /**
   * Builds a greeting for the given name.
   *
   * @param name the requested name, may be {@code null} or blank
   * @return a greeting message, never {@code null}
   */
  public String greet(final String name) {
    return "Hello, " + sanitize(name) + "!";
  }

  /**
   * Returns the upper-case form of a greeting using the root locale.
   *
   * @param name the requested name
   * @return the shouted greeting
   */
  public String shout(final String name) {
    return greet(name).toUpperCase(Locale.ROOT);
  }

  /**
   * Reduces a name to letters, digits, spaces and a few safe punctuation characters.
   *
   * @param name raw name, may be {@code null}
   * @return a safe, bounded name
   */
  static String sanitize(final String name) {
    if (name == null) {
      return DEFAULT_NAME;
    }
    final StringBuilder out = new StringBuilder();
    for (int i = 0; i < name.length() && out.length() < MAX_NAME_LENGTH; i++) {
      final char c = name.charAt(i);
      if (Character.isLetterOrDigit(c) || c == ' ' || c == '-' || c == '_' || c == '.') {
        out.append(c);
      }
    }
    final String cleaned = out.toString().strip();
    return cleaned.isEmpty() ? DEFAULT_NAME : cleaned;
  }
}
