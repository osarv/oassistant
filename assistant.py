import sys
from pathlib import Path
from ollama import Client

client = Client()
model = None
config = Path.cwd() / "config.txt"

def cfg_find_model(model_name):
    for mdl in Client().list().models:
        if mdl["model"] == model_name:
            return mdl["model"]
    return None

if (config.exists()):
    for line in config.read_text().splitlines():
        if line.startswith("model="):
            model = cfg_find_model(line.split("=", 1)[1].strip())
            if model is None:
                model = Client().list().models[0]["model"]
                print("[config error] model \"" f"{line.split('=', 1)[1].strip()}\" " "not found")
else:
    config.write_text(f"model={model}\n")

print("using model:", model)
history = []
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
        print("\n[exit]", end="")
        sys.exit()
