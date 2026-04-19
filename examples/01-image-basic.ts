import { Wittgenstein } from "@wittgenstein/core";

async function main() {
  const wittgenstein = await Wittgenstein.bootstrap();
  const outcome = await wittgenstein.run(
    {
      modality: "image",
      prompt: "A black-and-white architectural still life",
    },
    {
      command: "example:image",
      args: [],
      dryRun: true,
    },
  );

  console.log(outcome.manifest);
}

void main();
