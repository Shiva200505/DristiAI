# Limitations

The deterministic rules are a focused security baseline, not a complete SAST engine. Semgrep/Bandit/OSV results depend on optional installations and their own coverage. TypeScript syntax verification currently uses the available Node check and does not replace `tsc`. The QNN adapter can validate an ONNX Runtime provider/session but does not invent a generic text-generation interface for arbitrary ONNX graphs. The current UI still has a Node realtime gateway and a FastAPI integration service; they share contracts, while a future release can collapse them behind one process.
