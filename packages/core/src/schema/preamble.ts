export function injectSchemaPreamble(prompt: string, schemaPreamble: string): string {
  return [
    "You are Wittgenstein.",
    "Return valid JSON only.",
    schemaPreamble.trim(),
    `User prompt:\n${prompt.trim()}`,
  ].join("\n\n");
}
