from __future__ import annotations

from enzu.models import Budget, SuccessCriteria, TaskSpec
from enzu.providers.openai_compat import OpenAICompatProvider


class _FakeDelta:
    content = "hi"


class _FakeChoice:
    delta = _FakeDelta()


class _FakeChunk:
    def __init__(self, usage: dict | None = None) -> None:
        self.choices = [_FakeChoice()]
        self.usage = usage


class _FakeStream:
    def __iter__(self):
        yield _FakeChunk({"output_tokens": 1, "total_tokens": 1})


class _FakeChatCompletions:
    def __init__(self) -> None:
        self.kwargs: dict | None = None

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self.kwargs = kwargs
        return _FakeStream()


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeChatCompletions()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat()


def test_stream_chat_completions_requests_usage() -> None:
    client = _FakeClient()
    provider = OpenAICompatProvider(name="openai", client=client)
    task = TaskSpec(
        task_id="stream-usage",
        input_text="say hi",
        model="mock-model",
        budget=Budget(max_output_tokens=5),
        success_criteria=SuccessCriteria(min_word_count=1),
    )

    result = provider.stream(task)

    assert result.output_text == "hi"
    assert client.chat.completions.kwargs is not None
    assert client.chat.completions.kwargs["stream_options"] == {"include_usage": True}
