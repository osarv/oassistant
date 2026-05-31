import sys
import json
from enum import Enum
from pathlib import Path
from ollama import Client

COLOR_PROMPT = "\033[31m"
COLOR_USER_TEXT = "\033[36m"
COLOR_RESET = "\033[0m"

historyPath = Path.cwd() / "history.txt"
sysPromptPath = Path.cwd() / "sysprompt.txt"
longTermMemoryPath = Path.cwd() / "longtermmemory.txt"
configPath = Path.cwd() / "config.txt"
ollamaClient = Client()
model = None

history = []
if (historyPath.exists()):
    history = json.loads(historyPath.read_text())

if (longTermMemoryPath.exists()):
    history.insert(0, {"role": "system", "content": longTermMemoryPath.read_text()})

if (sysPromptPath.exists()):
    history.insert(0, {"role": "system", "content": sysPromptPath.read_text()})

def globalExceptionHandler(excType, value, traceback):
    if issubclass(excType, KeyboardInterrupt):
        print(COLOR_RESET + "\n[exit]", end="")
        for i, msg in enumerate(history):
            if msg["role"] != "system":
                historyPath.write_text(json.dumps(history[i:]))
                break;
        sys.exit()

sys.excepthook = globalExceptionHandler

def cfgFindModel(modelName):
    for mdl in ollamaClient.list().models:
        if mdl["model"] == modelName:
            return mdl["model"]
    return None

if (configPath.exists()):
    for line in configPath.read_text().splitlines():
        if line.startswith("model="):
            model = cfgFindModel(line.split("=", 1)[1].strip())
            if model is None:
                model = ollamaClient.list().models[0]["model"]
                print("[config error] model \"" f"{line.split('=', 1)[1].strip()}\" " "not found")
else:
    configPath.write_text(f"model={model}\n")

outputTag = "{\"mode\":\"output\"}"
reasoningTag = "{\"mode\":\"reasoning\"}"

print("[model]", model)
while True:
    history.append({"role": "user", "content": input(COLOR_PROMPT + ">> " + COLOR_USER_TEXT)})
    print(COLOR_RESET, end="");
    stream = ollamaClient.chat(
        model=model,
        messages=history,
        stream=True)

    buf = ""
    outputMode = False
    history.append({"role": "assistant", "content": ""})
    for chunk in stream:
        history[-1]["content"] += chunk.message.content
        for c in chunk.message.content:
            buf += c
            if outputMode:
                if buf == reasoningTag[:len(buf)]:
                    if len(buf) == len(reasoningTag):
                        outputMode = False
                        buf = ""
                else:
                    print(buf, end="")
                    buf = ""
            else:
                if buf == outputTag[:len(buf)]:
                    if len(buf) == len(outputTag):
                        outputMode = True
                        buf = ""
                #elif c == "}":
                    #try to parse a json object
                    #see if it is a tool call
                    #call the tool call if it is a tool call
                else:
                    buf = ""
    print()
