from pathlib import Path
import os


def main() -> int:
    model = os.getenv("DRISHTI_MODEL_PATH")
    if not model:
        print("No DRISHTI_MODEL_PATH configured.")
        print("The deterministic fallback remains fully functional.")
        print("To enable optional local LLM explanations, set DRISHTI_MODEL_PATH to a local GGUF file.")
        return 0
    path = Path(model).expanduser()
    if not path.is_file():
        print(f"Model path does not exist: {path}")
        return 1
    print(f"Local model ready: {path}")
    print("Model bytes stay local; benchmark it before making performance claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
