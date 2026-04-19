import type { WittgensteinRequest } from "@wittgenstein/schemas";
import type { CodecRegistry } from "./registry.js";

export function routeRequest(request: WittgensteinRequest, registry: CodecRegistry) {
  return registry.getOrThrow(request.modality);
}
