import sys
import json
from enum import Enum
from pathlib import Path
from ollama import Client

COLOR_PROMPT = "\033[1;31m"
COLOR_USER_TEXT = "\033[1;36m"
COLOR_RESET = "\033[0m"

outputTag = "[MODE:OUTPUT]"
reasoningTag = "[MODE:REASONING]"
toolTag = "[MODE:TOOL]"
historyPath = Path.cwd() / "history.txt"
sysPromptPath = Path.cwd() / "sysprompt.txt"
longTermMemoryPath = Path.cwd() / "longtermmemory.txt"
configPath = Path.cwd() / "config.txt"
ollamaClient = Client()

def cfgFindModel(modelName):
    for mdl in ollamaClient.list().models:
        if mdl["model"] == modelName:
            return mdl["model"]
    return None

class Mode(Enum):
    OUTPUT = 0
    REASONING = 1
    TOOL = 2
    POSSIBLE = 3
    NOSWITCH = 4

def tryModeSwitch(buf):
    if buf == outputTag[:len(buf)] or buf == reasoningTag[:len(buf)] or buf == toolTag[:len(buf)]:
        if buf == outputTag:
            return Mode.OUTPUT
        elif buf == reasoningTag:
            return Mode.REASONING
        elif buf == toolTag:
            return Mode.TOOL
        else:
            return Mode.POSSIBLE
    return Mode.NOSWITCH

def callTool(obj):
    try:
        if obj["tool"] == "remember":
            #return toolRemember(obj["args"])
            return None
        elif obj["tool"] == "forget":
            #return toolForget(obj["args"])
            return None
        else:
            return None
    except KeyError:
        return None

def tryParseToolCall(toolHistory, buf):
    try:
        obj = json.loads(buf)
        result = callTool(obj)
        if result == None:
            toolHistory.append({"role": "tool", "content": "error: tool not found"})
        else:
            toolHistory.append({"role": "tool", "content": result})
    except json.JSONDecodeError:
        pass

def main():
    history = []
    if (historyPath.exists()):
        history = json.loads(historyPath.read_text())

    if (longTermMemoryPath.exists()):
        history.insert(0, {"role": "system", "content": longTermMemoryPath.read_text()})

    if (sysPromptPath.exists()):
        history.insert(0, {"role": "system", "content": sysPromptPath.read_text()})

    def keyboardInterruptHandler(excType, value, traceback):
        if issubclass(excType, KeyboardInterrupt):
            print(COLOR_RESET + "\n[exit]", end="")
            for i, msg in enumerate(history):
                if msg["role"] != "system":
                    history.append({"role": "user", "content": "keyboard interrupt"})
                    historyPath.write_text(json.dumps(history[i:]))
                    break;
        else:
            sys.__excepthook__(excType, value,traceback)
        sys.exit()

    sys.excepthook = keyboardInterruptHandler
    model = None
    if (configPath.exists()):
        for line in configPath.read_text().splitlines():
            if line.startswith("model="):
                model = cfgFindModel(line.split("=", 1)[1].strip())
                if model is None:
                    model = ollamaClient.list().models[0]["model"]
                    print("[config] error: model \"" f"{line.split('=', 1)[1].strip()}\" " "not found")
    else:
        configPath.write_text(f"model={model}\n")

    print("[model]", model)
    while True:
        history.append({"role": "user", "content": input(COLOR_PROMPT + ">> " + COLOR_USER_TEXT)})
        print(COLOR_RESET, end="");
        stream = ollamaClient.chat(
            model=model,
            messages=history,
            stream=True)

        mode = Mode.REASONING
        history.append({"role": "assistant", "content": ""})
        buf = ""
        toolHistory = []
        for chunk in stream:
            history[-1]["content"] += chunk.message.content
            for c in chunk.message.content:
                buf += c
                ret = tryModeSwitch(buf);
                if ret == Mode.OUTPUT or ret == Mode.REASONING or ret == Mode.TOOL:
                    if mode == Mode.TOOL:
                        toolHistory.append({"role": "tool", "content": "error: invalid json"})
                    mode = ret
                    buf = ""
                elif ret == Mode.NOSWITCH:
                    if mode == Mode.OUTPUT:
                        print(buf, end="", flush=True)
                        buf = ""
                    elif mode == Mode.REASONING:
                        buf = ""

                if mode == Mode.TOOL:
                    tryParseToolCall(toolHistory, buf)

        history.extend(toolHistory)
        toolHistory.clear()
        print()

if __name__ == "__main__":
    main()
