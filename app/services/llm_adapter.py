from __future__ import annotations

import json
from urllib import error, request

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


class LLMAdapterError(RuntimeError):
    pass


class LLMAdapter:
    def __init__(
        self,
        *,
        provider: str,
        endpoint: str,
        api_key: str,
        model: str,
        timeout_seconds: int = 45,
        client=None,
    ):
        self.provider = provider
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.base_url = self._normalize_base_url(endpoint)
        self.client = client

    def generate_recipe(self, prompt: str) -> str:
        if self.provider in {"openai", "openai_compatible"}:
            return self._openai_generate(prompt)
        if self.provider == "ollama":
            return self._ollama_generate(prompt)
        raise LLMAdapterError(f"Unsupported LLM_PROVIDER '{self.provider}'")

    @staticmethod
    def _normalize_base_url(endpoint: str) -> str:
        normalized = (endpoint or "").strip().rstrip("/")
        if not normalized:
            return "https://api.openai.com/v1"

        lower = normalized.lower()
        for suffix in ("/chat/completions", "/responses"):
            if lower.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break

        return normalized.rstrip("/")

    @staticmethod
    def _uses_responses_api(model: str) -> bool:
        model_name = (model or "").strip().lower()
        return model_name.startswith("gpt-")

    def _get_openai_client(self):
        if self.client is not None:
            return self.client
        if OpenAI is None:
            raise LLMAdapterError(
                "openai package is not installed. Install dependencies from requirements.txt"
            )
        return OpenAI(base_url=self.base_url, api_key=self.api_key)

    def _openai_generate(self, prompt: str) -> str:
        if not self.model:
            raise LLMAdapterError("LLM_MODEL is required for openai_compatible provider")

        client = self._get_openai_client()
        if self._uses_responses_api(self.model):
            return self._openai_responses_generate(client, prompt)
        return self._openai_chat_generate(client, prompt)

    def _openai_chat_generate(self, client, prompt: str) -> str:
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You generate strict JSON recipe payloads. Return JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:
            raise LLMAdapterError(f"LLM request failed: {exc}") from exc

        try:
            content = response.choices[0].message.content
        except Exception as exc:
            raise LLMAdapterError("Unable to parse LLM response payload") from exc

        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            fragments: list[str] = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    fragments.append(item["text"])
                elif hasattr(item, "text") and isinstance(item.text, str):
                    fragments.append(item.text)
            joined = "\n".join(part for part in fragments if part.strip()).strip()
            if joined:
                return joined

        raise LLMAdapterError("Unable to parse LLM response payload")

    def _openai_responses_generate(self, client, prompt: str) -> str:
        try:
            response = client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": "You generate strict JSON recipe payloads. Return JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:
            raise LLMAdapterError(f"LLM request failed: {exc}") from exc

        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        output = getattr(response, "output", None) or []
        text_fragments: list[str] = []
        for item in output:
            contents = getattr(item, "content", None) or []
            for block in contents:
                text_value = getattr(block, "text", None)
                if isinstance(text_value, str) and text_value.strip():
                    text_fragments.append(text_value)

        merged = "\n".join(part for part in text_fragments if part.strip()).strip()
        if merged:
            return merged

        raise LLMAdapterError("Unable to parse LLM response payload")

    def _ollama_generate(self, prompt: str) -> str:
        if not self.model:
            raise LLMAdapterError("LLM_MODEL is required for ollama provider")

        endpoint = self.endpoint or "http://localhost:11434/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        return self._post_json(
            endpoint=endpoint,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "curl/8.7.1",
            },
            payload=payload,
            response_path=("response",),
        )

    def _post_json(self, *, endpoint: str, headers: dict[str, str], payload: dict, response_path: tuple) -> str:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(endpoint, data=data, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise LLMAdapterError(f"LLM request failed ({exc.code}): {body}") from exc
        except Exception as exc:  # pragma: no cover
            raise LLMAdapterError(f"LLM request failed: {exc}") from exc

        try:
            parsed = json.loads(raw)
            for key in response_path:
                parsed = parsed[key]
            if not isinstance(parsed, str):
                raise ValueError("response content is not a string")
            return parsed.strip()
        except Exception as exc:
            raise LLMAdapterError("Unable to parse LLM response payload") from exc
