import { Wittgenstein } from "@wittgenstein/core";

async function main() {
  const wittgenstein = await Wittgenstein.bootstrap();
  const outcome = await wittgenstein.run(
    {
      modality: "audio",
      prompt: "A calm voice introducing the project",
      route: "speech",
    },
    {
      command: "example:audio",
      args: [],
      dryRun: true,
    },
  );

  console.log(outcome.manifest);
}

void main();
