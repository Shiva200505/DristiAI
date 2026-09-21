class QnnBackend:
    """Explicit placeholder until a validated Qualcomm runtime is installed."""
    name = "QNN_ONNX_RUNTIME"

    def __init__(self):
        raise NotImplementedError("QNN backend is not available on this development machine; install and validate the target Qualcomm runtime first.")
