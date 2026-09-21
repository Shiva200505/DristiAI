# AI architecture

`ModelRegistry` selects a provider from explicit configuration and installed capabilities:

- `CPU_LLAMA_CPP`: real local GGUF inference when `DRISHTI_MODEL_PATH` and `llama-cpp-python` are available.
- `GENIEX_OPENAI`: real requests to a configured local GenieX OpenAI-compatible endpoint.
- `QNN_ONNX_RUNTIME`: capability-probed ONNX Runtime QNN session. A generic ONNX session is not mislabeled as text generation.
- `TEMPLATE_FALLBACK`: deterministic explanation only, clearly marked non-semantic.

Provider health exposes availability, model, runtime, latency where measured, and the exact error state. Repository text is placed in the untrusted context portion of prompts. Prompts instruct the provider not to invent scanner results, tests, CWE mappings, runtime capabilities, or guarantees.

Embedding retrieval uses Sentence Transformers only when an explicitly configured local model is available. The persisted index labels the emergency hash vector path as `EMERGENCY_HASH_FALLBACK`; that path is for offline smoke tests and is not described as semantic retrieval.
