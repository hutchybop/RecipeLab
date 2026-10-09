from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.services.llm_adapter import LLMAdapter


class _FakeResponsesAPI:
    def __init__(self, text: str):
        self.text = text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.text, output=[])


class _FakeChatCompletionsAPI:
    def __init__(self, text: str):
        self.text = text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self.text)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class _FakeClient:
    def __init__(self, *, responses_text: str = "{}", chat_text: str = "{}"):
        self.responses = _FakeResponsesAPI(responses_text)
        self.chat = SimpleNamespace(completions=_FakeChatCompletionsAPI(chat_text))


class LLMAdapterTests(unittest.TestCase):
    def test_normalizes_endpoint_to_base_url(self):
        adapter = LLMAdapter(
            provider="openai_compatible",
            endpoint="https://opencode.ai/zen/v1/chat/completions",
            api_key="k",
            model="gpt-5.4",
            client=_FakeClient(),
        )
        self.assertEqual(adapter.base_url, "https://opencode.ai/zen/v1")

    def test_routes_gpt_models_to_responses_api(self):
        client = _FakeClient(responses_text='{"ok":true}', chat_text='{"should":"not_be_used"}')
        adapter = LLMAdapter(
            provider="openai_compatible",
            endpoint="https://opencode.ai/zen/v1",
            api_key="k",
            model="gpt-5.4",
            client=client,
        )

        result = adapter.generate_recipe("Return JSON")
        self.assertEqual(result, '{"ok":true}')
        self.assertEqual(len(client.responses.calls), 1)
        self.assertEqual(len(client.chat.completions.calls), 0)

    def test_routes_non_gpt_models_to_chat_completions(self):
        client = _FakeClient(responses_text='{"should":"not_be_used"}', chat_text='{"ok":true}')
        adapter = LLMAdapter(
            provider="openai_compatible",
            endpoint="https://opencode.ai/zen/v1",
            api_key="k",
            model="deepseek-v4-flash",
            client=client,
        )

        result = adapter.generate_recipe("Return JSON")
        self.assertEqual(result, '{"ok":true}')
        self.assertEqual(len(client.responses.calls), 0)
        self.assertEqual(len(client.chat.completions.calls), 1)


if __name__ == "__main__":
    unittest.main()
