export interface WittgensteinErrorOptions {
  cause?: unknown;
  details?: Record<string, unknown>;
}

export class WittgensteinError extends Error {
  public readonly code: string;
  public readonly details: Record<string, unknown> | undefined;

  public constructor(
    code: string,
    message: string,
    options: WittgensteinErrorOptions = {},
  ) {
    super(message, { cause: options.cause });
    this.name = "WittgensteinError";
    this.code = code;
    this.details = options.details;
  }
}

export class NotImplementedError extends WittgensteinError {
  public constructor(scope: string, options: WittgensteinErrorOptions = {}) {
    super("NOT_IMPLEMENTED", `NotImplementedError(${scope})`, options);
    this.name = "NotImplementedError";
  }
}

export class ValidationError extends WittgensteinError {
  public constructor(message: string, options: WittgensteinErrorOptions = {}) {
    super("VALIDATION_ERROR", message, options);
    this.name = "ValidationError";
  }
}

export class BudgetExceededError extends WittgensteinError {
  public constructor(message: string, options: WittgensteinErrorOptions = {}) {
    super("BUDGET_EXCEEDED", message, options);
    this.name = "BudgetExceededError";
  }
}

export interface SerializedError {
  code: string;
  message: string;
  stack: string | undefined;
}

export function serializeError(error: unknown): SerializedError {
  if (error instanceof WittgensteinError) {
    return {
      code: error.code,
      message: error.message,
      stack: error.stack,
    };
  }

  if (
    typeof error === "object" &&
    error !== null &&
    "message" in error &&
    typeof error.message === "string" &&
    "code" in error &&
    typeof error.code === "string"
  ) {
    return {
      code: error.code,
      message: error.message,
      stack:
        "stack" in error && typeof error.stack === "string"
          ? error.stack
          : undefined,
    };
  }

  if (error instanceof Error) {
    return {
      code: "UNEXPECTED_ERROR",
      message: error.message,
      stack: error.stack,
    };
  }

  return {
    code: "UNKNOWN_THROWN_VALUE",
    message: String(error),
    stack: undefined,
  };
}
