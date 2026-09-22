# Qualcomm validation path

This document records the official sources used for the Qualcomm adapter design and the boundary between verified facts and future validation.

- [Qualcomm AI Hub Models](https://github.com/qualcomm/ai-hub-models) documents model collection metadata, AI Hub compilation/profiling, supported runtimes, and target devices.
- [Qualcomm GenieX](https://github.com/qualcomm/GenieX) documents local model execution on Snapdragon Windows ARM64 and its OpenAI-compatible local service.
- [GenieX run notes](https://github.com/qualcomm/GenieX/blob/main/notes/run.md) document QAIRT model assets, QNN/Hexagon requirements, and runtime errors such as missing `QnnHtp.dll`.
- [GenieX benchmark notes](https://github.com/qualcomm/GenieX/blob/main/notes/bench.md) document Qualcomm Device Cloud benchmark workflows.
- [ONNX Runtime execution providers](https://onnxruntime.ai/docs/execution-providers/) lists Qualcomm QNN as an execution-provider path.

## Current operator notes

The current AI Hub Models documentation exposes a catalog/CLI path (`qai-hub-models models`, `info`, and `fetch`) and separates local asset retrieval from Workbench compilation/profiling. Workbench operations require a Qualcomm account and API token; that token belongs in the operator’s Qualcomm CLI configuration, never in Drishti source code or browser settings.

The same documentation currently notes that Snapdragon X Elite/X2 Elite Windows users should use AMD64 Python for the AI Hub Models package; Windows ARM64 Python is not the supported installation path for that package. Verify the target model’s runtime, precision, chipset, and device support before selecting a deployment artifact.

GenieX and QNN are separate integration paths. Drishti’s GenieX adapter checks the local OpenAI-compatible `/v1/models` endpoint. The QNN adapter only reports provider/model-session capability and deliberately does not expose generic text generation for an arbitrary ONNX graph.

The repository does not claim a model is Snapdragon/NPU compatible merely because it is named in a Qualcomm repository. A target run must record the physical or remote device, model identifier, precision, runtime, provider, job/evidence source, timestamp, and measured result. The current Intel Windows development machine has no such evidence and therefore reports `NOT MEASURED ON SNAPDRAGON HARDWARE`.
