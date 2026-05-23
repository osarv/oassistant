import sys
from pathlib import Path
from ollama import Client

client = Client()
model = Client().list().models[0]["model"]
config = Path.cwd() / "cfg"

history = []
if (config.exists()):
    for line in config.read_text().splitlines():
        if line.startswith("model="):
            model = line.split("=", 1)[1].strip()
            break

while True:
    try:
        history.append({"role": "user", "content": input(">> ")})
        stream = client.chat(
            model=model,
            messages=history,
            stream=True,
        )

        history.append({"role": "assistant", "content": ""})
        for chunk in stream:
            print(chunk.message.content, end="", flush=True)
            history[-1]["content"] += chunk.message.content
        print()

    except KeyboardInterrupt:
        print("\n[Interrupted by user]", end="")
        sys.exit()

