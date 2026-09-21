Write-Host "Drishti AI development setup"
python -m pip install -r requirements.txt
Write-Host "Optional tools: install bandit, semgrep, chromadb, and llama-cpp-python only when their local runtime is available."
Write-Host "Set DRISHTI_MODEL_PATH to a local GGUF file to enable the optional local LLM adapter."
