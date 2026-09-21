# Model management

Model files are operator-installed artifacts. Drishti does not silently download or execute them. Before enabling a model, record its source, version, format, checksum, size, runtime, precision, and intended device.

`/api/system/runtime` reports the active provider and health. `TEMPLATE_FALLBACK` means no generative model is installed; it does not mean AI ran. A future installer can add checksum verification and model metadata without changing the provider interface.
