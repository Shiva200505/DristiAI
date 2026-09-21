# Snapdragon deployment

1. Use a supported Windows on Snapdragon ARM64 environment and the current Qualcomm/GenieX installation instructions.
2. Install the exact runtime required by the selected model. Do not copy old QNN context-binary steps from unrelated versions.
3. Configure `DRISHTI_MODEL_RUNTIME=geniex` plus `DRISHTI_GENIEX_BASE_URL` for the supported local OpenAI-compatible service, or configure `DRISHTI_MODEL_RUNTIME=qnn` and a validated ONNX model for the QNN capability adapter.
4. Start the runtime independently and check `/api/system/runtime` before presenting the result.
5. Record a benchmark with device, model, precision, runtime, source, and timestamp. Only then can the UI compare it with development-machine measurements.

If the provider or device is unsupported, Drishti reports the reason and stays in a truthful CPU/fallback state. It never simulates NPU metrics.
