assistant:
	.venv/bin/python3 assistant.py

install:
	python3 -m venv .venv
	.venv/bin/pip install ollama
