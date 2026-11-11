package io.github.christianpresley.hello;

import jakarta.validation.ConstraintViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/** Maps validation failures to client errors without leaking internals. */
@RestControllerAdvice
public class ApiExceptionHandler {

  /**
   * Converts constraint violations to a 400 response.
   *
   * @param ex the violation
   * @return a problem detail with a generic message
   */
  @ExceptionHandler(ConstraintViolationException.class)
  public ProblemDetail badRequest(final ConstraintViolationException ex) {
    return ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Invalid request parameter");
  }
}
