from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from openai import OpenAI

from enzu.models import ProgressEvent, ProviderResult, TaskSpec
from enzu.providers.base import BaseProvider
from enzu.retry import with_retry


class OpenAICompatProvider(BaseProvider):
    """
    Unified provider for all OpenAI-compatible APIs.
    
    Supports both Open Responses API (per openresponses.org spec) and
    Chat Completions API. Tries Responses API first if supported, falls
    back to Chat Completions for compatibility.
    """

    def __init__(
        self,
        name: str,
        *,
        api_key: Optional[str] = None,
        client: Optional[OpenAI] = None,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        supports_responses: bool = False,
    ) -> None:
        self.name = name
        self._supports_responses = supports_responses
        if client is None:
            self._client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                default_headers=headers,
                organization=organization,
                project=project,
            )
        else:
            self._client = client

    def generate(self, task: TaskSpec) -> ProviderResult:
        """
        Generate response using Open Responses API if supported, else Chat Completions.
        
        Per openresponses.org spec, Responses API uses 'input' parameter and
        returns 'output_text' field. Chat Completions uses 'messages' and
        returns 'choices[0].message.content'.
        """
        if self._supports_responses:
            try:
                return self._generate_responses(task)
            except Exception:
                return self._generate_chat_completions(task)
        return self._generate_chat_completions(task)

    @with_retry()
    def _generate_responses(self, task: TaskSpec) -> ProviderResult:
        """Generate using Open Responses API (openresponses.org spec)."""
        input_text = self._build_input(task)
        response = self._client.responses.create(
            model=task.model,
            input=input_text,
            max_output_tokens=task.max_output_tokens,
            temperature=task.temperature,
        )
        output_text = self._extract_responses_output_text(response)
        usage = self._extract_usage(response)
        return ProviderResult(
            output_text=output_text,
            raw=response,
            usage=usage,
            provider=self.name,
            model=task.model,
        )

    @with_retry()
    def _generate_chat_completions(self, task: TaskSpec) -> ProviderResult:
        """Generate using Chat Completions API (fallback)."""
        messages = self._build_messages(task)
        response = self._client.chat.completions.create(
            model=task.model,
            messages=messages,
            max_tokens=task.max_output_tokens,
            temperature=task.temperature,
        )
        output_text = self._extract_chat_output_text(response)
        usage = self._extract_usage(response)
        return ProviderResult(
            output_text=output_text,
            raw=response,
            usage=usage,
            provider=self.name,
            model=task.model,
        )

    def stream(
        self,
        task: TaskSpec,
        on_progress: Optional[Callable[[ProgressEvent], None]] = None,
    ) -> ProviderResult:
        """
        Stream response using Open Responses API if supported, else Chat Completions.
        
        Open Responses uses semantic events like 'response.output_text.delta'.
        Chat Completions uses 'choices[0].delta.content'.
        """
        if self._supports_responses:
            try:
                return self._stream_responses(task, on_progress)
            except Exception:
                return self._stream_chat_completions(task, on_progress)
        return self._stream_chat_completions(task, on_progress)

    @with_retry()
    def _stream_responses(self, task: TaskSpec, on_progress: Optional[Callable[[ProgressEvent], None]]) -> ProviderResult:
        """Stream using Open Responses API (openresponses.org spec)."""
        input_text = self._build_input(task)
        output_chunks: list[str] = []
        usage: Dict[str, Any] = {}
        try:
            stream = self._client.responses.create(
                model=task.model,
                input=input_text,
                max_output_tokens=task.max_output_tokens,
                temperature=task.temperature,
                stream=True,
            )
            for event in stream:
                event_type = getattr(event, "type", None)
                if event_type == "response.output_text.delta":
                    delta = getattr(event, "delta", "")
                    if delta:
                        output_chunks.append(delta)
                        if on_progress:
                            on_progress(
                                ProgressEvent(
                                    phase="generation",
                                    message=delta,
                                    is_partial=True,
                                    data={"provider": self.name},
                                )
                            )
                elif event_type == "response.completed":
                    response = getattr(event, "response", None)
                    if response is not None:
                        usage = self._extract_usage(response)
            output_text = "".join(output_chunks).strip()
            if not output_text:
                return self._generate_responses(task)
            return ProviderResult(
                output_text=output_text,
                raw={"streamed": True},
                usage=usage,
                provider=self.name,
                model=task.model,
            )
        except Exception:
            if on_progress:
                on_progress(
                    ProgressEvent(
                        phase="generation",
                        message=f"{self.name}_responses_stream_failed_fallback",
                        data={"provider": self.name},
                    )
                )
            return self._generate_responses(task)

    @with_retry()
    def _stream_chat_completions(
        self, task: TaskSpec, on_progress: Optional[Callable[[ProgressEvent], None]]
    ) -> ProviderResult:
        """Stream using Chat Completions API (fallback)."""
        messages = self._build_messages(task)
        output_chunks: list[str] = []
        usage: Dict[str, Any] = {}
        try:
            stream = self._client.chat.completions.create(
                model=task.model,
                messages=messages,
                max_tokens=task.max_output_tokens,
                temperature=task.temperature,
                # Request final usage chunk for budget accounting where supported.
                stream_options={"include_usage": True},
                stream=True,
            )
            for chunk in stream:
                delta = self._extract_chat_delta(chunk)
                if delta:
                    output_chunks.append(delta)
                    if on_progress:
                        on_progress(
                            ProgressEvent(
                                phase="generation",
                                message=delta,
                                is_partial=True,
                                data={"provider": self.name},
                            )
                        )
                if chunk.usage:
                    usage = self._extract_usage(chunk)
            output_text = "".join(output_chunks).strip()
            if not output_text:
                return self._generate_chat_completions(task)
            return ProviderResult(
                output_text=output_text,
                raw={"streamed": True},
                usage=usage,
                provider=self.name,
                model=task.model,
            )
        except Exception:
            if on_progress:
                on_progress(
                    ProgressEvent(
                        phase="generation",
                        message=f"{self.name}_chat_stream_failed_fallback_generate",
                        data={"provider": self.name},
                    )
                )
            return self._generate_chat_completions(task)

    def _build_input(self, task: TaskSpec) -> str:
        """
        Build input string for Open Responses API.
        
        Per openresponses.org spec, Responses API uses 'input' parameter
        (string or structured). Includes success criteria if present.
        """
        content = task.input_text
        criteria_lines = []
        if task.success_criteria.required_substrings:
            criteria_lines.append(
                "Required substrings: "
                + ", ".join(task.success_criteria.required_substrings)
            )
        if task.success_criteria.required_regex:
            criteria_lines.append(
                "Required regex: " + ", ".join(task.success_criteria.required_regex)
            )
        if task.success_criteria.min_word_count:
            criteria_lines.append(
                f"Minimum word count: {task.success_criteria.min_word_count}"
            )
        if task.success_criteria.case_insensitive:
            criteria_lines.append("Case-insensitive checks: true")
        if criteria_lines:
            criteria_text = "\n".join(criteria_lines)
            content = f"{content}\n\nSuccess criteria:\n{criteria_text}"
        return content

    def _build_messages(self, task: TaskSpec) -> list[Dict[str, str]]:
        """
        Build messages array for Chat Completions API.
        
        Includes success criteria in the user message if present.
        """
        content = self._build_input(task)
        return [{"role": "user", "content": content}]

    @staticmethod
    def _extract_responses_output_text(response: Any) -> str:
        """
        Extract text from Open Responses API response.
        
        Per openresponses.org spec, Responses API returns 'output_text' field
        directly, or nested in 'output' items.
        """
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text
        output = getattr(response, "output", None)
        if not output:
            return ""
        chunks: list[str] = []
        for item in output:
            content = getattr(item, "content", None)
            if not content:
                continue
            for part in content:
                if getattr(part, "type", None) == "output_text":
                    chunks.append(getattr(part, "text", ""))
        return "".join(chunks).strip()

    @staticmethod
    def _extract_chat_output_text(response: Any) -> str:
        """
        Extract text from Chat Completions response.
        
        Response shape: response.choices[0].message.content
        """
        if not hasattr(response, "choices") or not response.choices:
            return ""
        choice = response.choices[0]
        if not hasattr(choice, "message"):
            return ""
        message = choice.message
        if not hasattr(message, "content"):
            return ""
        return message.content or ""

    @staticmethod
    def _extract_chat_delta(chunk: Any) -> str:
        """
        Extract delta text from Chat Completions streaming chunk.
        
        Chunk shape: chunk.choices[0].delta.content
        """
        if not hasattr(chunk, "choices") or not chunk.choices:
            return ""
        choice = chunk.choices[0]
        if not hasattr(choice, "delta"):
            return ""
        delta = choice.delta
        if not hasattr(delta, "content"):
            return ""
        return delta.content or ""

    @staticmethod
    def _extract_usage(response: Any) -> Dict[str, Any]:
        """
        Extract usage stats from response.
        
        Handles both CompletionUsage objects and dicts.
        """
        usage = getattr(response, "usage", None)
        if usage is None:
            return {}
        if hasattr(usage, "model_dump"):
            return usage.model_dump()
        if isinstance(usage, dict):
            return usage
        return dict(usage)
