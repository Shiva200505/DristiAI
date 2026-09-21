class CpuLlamaBackend:
    def __init__(self, model_path: str):
        from llama_cpp import Llama
        self.model = Llama(model_path=model_path, n_ctx=4096, verbose=False)

    def generate(self, prompt: str, max_tokens: int = 256):
        response = self.model(prompt, max_tokens=max_tokens, temperature=0.1, stream=True)
        for chunk in response:
            text = chunk.get("choices", [{}])[0].get("text", "")
            if text:
                yield text
