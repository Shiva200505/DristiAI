# Qualcomm validation path

This document records the official sources used for the Qualcomm adapter design and the boundary between verified facts and future validation.

- [Qualcomm AI Hub Models](https://github.com/qualcomm/ai-hub-models) documents model collection metadata, AI Hub compilation/profiling, supported runtimes, and target devices.
- [Qualcomm GenieX](https://github.com/qualcomm/GenieX) documents local model execution on Snapdragon Windows ARM64 and its OpenAI-compatible local service.
- [GenieX run notes](https://github.com/qualcomm/GenieX/blob/main/notes/run.md) document QAIRT model assets, QNN/Hexagon requirements, and runtime errors such as missing `QnnHtp.dll`.
- [GenieX benchmark notes](https://github.com/qualcomm/GenieX/blob/main/notes/bench.md) document Qualcomm Device Cloud benchmark workflows.
- [ONNX Runtime execution providers](https://onnxruntime.ai/docs/execution-providers/) lists Qualcomm QNN as an execution-provider path.

The repository does not claim a model is Snapdragon/NPU compatible merely because it is named in a Qualcomm repository. A target run must record the physical or remote device, model identifier, precision, runtime, provider, job/evidence source, timestamp, and measured result. The current Intel Windows development machine has no such evidence and therefore reports `NOT MEASURED ON SNAPDRAGON HARDWARE`.
