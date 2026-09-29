"""Embedding provider used by the repository index."""

import requests


class OpenAIEmbeddings:
    model = "text-embedding-3-small"

    def __init__(self, api_key):
        self.api_key = api_key

    def embed(self, texts):
        if not texts:
            return []
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": texts},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()["data"]
        return [item["embedding"] for item in sorted(data, key=lambda item: item["index"])]
