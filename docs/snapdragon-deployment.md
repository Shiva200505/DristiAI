# Snapdragon Deployment Notes

The development machine is not treated as Snapdragon hardware. Before a Snapdragon claim is made:

1. Install the validated Qualcomm/ONNX Runtime QNN package for the target Windows environment.
2. Confirm `onnxruntime.get_available_providers()` exposes a QNN provider and that the intended model actually loads through it.
3. Run `benchmarks/run_benchmarks.py` on the target device and preserve the generated JSON with `device_label=SNAPDRAGON_DEVICE`.
4. Replace the CPU model adapter through `ModelRegistry`; do not change UI labels manually.

No NPU percentage, power draw, latency, or model support is assumed by this repository.
