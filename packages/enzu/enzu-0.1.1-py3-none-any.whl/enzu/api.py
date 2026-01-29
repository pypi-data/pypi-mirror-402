from __future__ import annotations

import os
from urllib.parse import urlparse
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import uuid4

from enzu.contract import (
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MIN_WORD_COUNT,
    task_spec_from_payload,
)
from enzu.engine import Engine
from enzu.models import (
    Budget,
    Check,
    ExecutionReport,
    Limits,
    RLMExecutionReport,
    SuccessCriteria,
    TaskSpec,
)
from enzu.providers.base import BaseProvider
from enzu.providers.openai_compat import OpenAICompatProvider
from enzu.providers.registry import get_provider_config, register_provider
from enzu.rlm import RLMEngine


def run(
    task: Union[str, TaskSpec, Dict[str, Any]],
    *,
    model: Optional[str] = None,
    provider: Optional[Union[str, BaseProvider]] = None,
    fallback_providers: Optional[List[str]] = None,
    data: Optional[str] = None,
    tokens: Optional[int] = None,
    seconds: Optional[float] = None,
    cost: Optional[float] = None,
    contains: Optional[List[str]] = None,
    matches: Optional[List[str]] = None,
    min_words: Optional[int] = None,
    # Explicit goal (optional). In RLM mode, prompt IS the goal by default.
    # Use this to override when goal differs from prompt.
    goal: Optional[str] = None,
    limits: Optional[Limits] = None,
    check: Optional[Check] = None,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
    referer: Optional[str] = None,
    app_name: Optional[str] = None,
    organization: Optional[str] = None,
    project: Optional[str] = None,
    max_steps: Optional[int] = None,
    verify_on_final: bool = True,
    on_progress: Optional[Callable[[str], None]] = None,
    return_report: bool = False,
    # Mode selection: "auto" (default), "chat", or "rlm".
    # auto: uses context size to decide (>64k tokens → rlm).
    mode: Optional[str] = None,
) -> Union[str, ExecutionReport, RLMExecutionReport]:
    """
    Run a task. Returns the answer.

    Mode selection (mode parameter):
    - "auto" (default): auto-detect based on context size and signals
    - "chat": single-shot generation
    - "rlm": iterative goal-oriented execution

    Auto mode triggers RLM when any of:
    - data provided
    - cost/seconds budget specified
    - explicit goal specified
    - context > 64k tokens (~256k chars)

    RLM mode:
    - prompt IS the goal by default
    - Model self-judges when goal is achieved via FINAL()
    - Budget is the hard constraint
    - Loops until: goal achieved OR budget exhausted

    Example (goal-oriented):
        run("Find the root cause", data=logs, model="gpt-4", cost=5.00)

    Example (large context auto-triggers RLM):
        run("Analyze this", data=huge_document, model="gpt-4")

    Example (force chat mode):
        run("Write a haiku", model="gpt-4", mode="chat")

    Example (force RLM mode):
        run("Complex task", model="gpt-4", mode="rlm")

    Set return_report=True for the full ExecutionReport/RLMExecutionReport.
    """
    task_payload = task if isinstance(task, dict) else None
    if task_payload:
        # Allow CLI-shaped payloads so Python users can reuse task JSON directly.
        if provider is None:
            provider = task_payload.get("provider")
        if data is None:
            data = task_payload.get("context") or task_payload.get("data")
        payload_mode = task_payload.get("mode")
        if payload_mode is not None and mode is None:
            mode = str(payload_mode).lower()
    provider = provider or "openrouter"

    # Keep Python mode values aligned with CLI/schema (chat, rlm, auto).
    if mode is not None and mode not in {"chat", "rlm", "auto"}:
        raise ValueError("mode must be 'chat', 'rlm', or 'auto'.")

    # Mode resolution:
    # 1. Explicit mode (chat/rlm) → use it
    # 2. mode=auto or mode=None → auto-detect based on signals
    if mode in ("chat", "rlm"):
        resolved_mode = mode
    else:
        # Auto-detect mode based on:
        # - Budget signals (cost/seconds) → rlm (goal-oriented work)
        # - Explicit goal → rlm
        # - Data provided → rlm
        # - Large context (>64k tokens ≈ 256k chars) → rlm
        # - Otherwise → chat
        task_text = task if isinstance(task, str) else ""
        data_text = data or ""
        total_chars = len(task_text) + len(data_text)
        # 64k tokens ≈ 256k chars (assuming ~4 chars/token)
        AUTO_RLM_CHAR_THRESHOLD = 256_000

        wants_goal_oriented = (
            data is not None
            or cost is not None
            or seconds is not None
            or goal is not None
            or total_chars > AUTO_RLM_CHAR_THRESHOLD
        )
        resolved_mode = "rlm" if wants_goal_oriented else "chat"

    # RLM without explicit data: prompt contains everything.
    # Default to empty string so sandbox has valid context structure.
    effective_data = data if data is not None else ""

    report = _run_internal(
        task,
        model=model,
        provider=provider,
        fallback_providers=fallback_providers,
        tokens=tokens,
        seconds=seconds,
        cost=cost,
        contains=contains,
        matches=matches,
        min_words=min_words,
        goal=goal,
        limits=limits,
        check=check,
        temperature=temperature,
        mode=resolved_mode,
        data=effective_data if resolved_mode == "rlm" else data,
        api_key=api_key,
        referer=referer,
        app_name=app_name,
        organization=organization,
        project=project,
        rlm_max_steps=max_steps,
        rlm_verify_on_final=verify_on_final,
        on_progress=on_progress,
    )
    if return_report:
        return report
    if isinstance(report, RLMExecutionReport):
        return report.answer or ""
    return report.output_text or ""


def _run_internal(
    task: Union[str, TaskSpec, Dict[str, Any]],
    *,
    model: Optional[str],
    provider: Union[str, BaseProvider],
    fallback_providers: Optional[List[str]],
    tokens: Optional[int],
    seconds: Optional[float],
    cost: Optional[float],
    contains: Optional[List[str]],
    matches: Optional[List[str]],
    min_words: Optional[int],
    goal: Optional[str],
    limits: Optional[Limits],
    check: Optional[Check],
    temperature: Optional[float],
    mode: str,
    data: Optional[str],
    api_key: Optional[str],
    referer: Optional[str],
    app_name: Optional[str],
    organization: Optional[str],
    project: Optional[str],
    rlm_max_steps: Optional[int],
    rlm_verify_on_final: bool,
    on_progress: Optional[Callable[[str], None]],
) -> Union[ExecutionReport, RLMExecutionReport]:
    """Internal: run task and return full report."""
    # RLM mode: data provided. When no explicit success criteria, prompt IS the goal.
    is_rlm = data is not None
    spec = _build_task_spec(
        task,
        model=model,
        tokens=tokens,
        seconds=seconds,
        cost=cost,
        contains=contains,
        matches=matches,
        min_words=min_words,
        goal=goal,
        limits=limits,
        check=check,
        temperature=temperature,
        is_rlm=is_rlm,
    )

    provider_instance = _resolve_provider(
        provider,
        api_key=api_key,
        referer=referer,
        app_name=app_name,
        organization=organization,
        project=project,
    )

    # Resolve fallback providers
    fallback_provider_instances = None
    if fallback_providers:
        fallback_provider_instances = [
            _resolve_provider(
                p,
                api_key=api_key,
                referer=referer,
                app_name=app_name,
                organization=organization,
                project=project,
            )
            for p in fallback_providers
        ]

    if mode == "rlm":
        engine = RLMEngine(
            max_steps=rlm_max_steps or 8,
            verify_on_final=rlm_verify_on_final,
        )
        return engine.run(
            spec,
            provider_instance,
            data=data,
            on_progress=on_progress,
            fallback_providers=fallback_provider_instances,
        )
    if mode != "chat":
        raise ValueError("mode must be 'chat' or 'rlm'")
    engine = Engine()
    return engine.run(
        spec,
        provider_instance,
        on_progress=on_progress,
        fallback_providers=fallback_provider_instances,
    )


def _merge_limits(
    limits: Optional[Limits],
    tokens: Optional[int],
    seconds: Optional[float],
    cost: Optional[float],
) -> Limits:
    """Merge inline kwargs with Limits object. Inline wins."""
    base = limits or Limits()
    return Limits(
        tokens=tokens if tokens is not None else base.tokens,
        total=base.total,
        seconds=seconds if seconds is not None else base.seconds,
        cost=cost if cost is not None else base.cost,
    )


def _merge_check(
    check: Optional[Check],
    contains: Optional[List[str]],
    matches: Optional[List[str]],
    min_words: Optional[int],
    goal: Optional[str] = None,
) -> Check:
    """Merge inline kwargs with Check object. Inline wins."""
    base = check or Check()
    return Check(
        contains=contains if contains is not None else base.contains,
        matches=matches if matches is not None else base.matches,
        min_words=min_words if min_words is not None else base.min_words,
        goal=goal if goal is not None else base.goal,
    )




def _apply_task_overrides(
    spec: TaskSpec,
    *,
    model: Optional[str],
    tokens: Optional[int],
    seconds: Optional[float],
    cost: Optional[float],
    contains: Optional[List[str]],
    matches: Optional[List[str]],
    min_words: Optional[int],
    goal: Optional[str],
    limits: Optional[Limits],
    check: Optional[Check],
    temperature: Optional[float],
) -> TaskSpec:
    # Explicit kwargs override TaskSpec fields to keep run() precedence.
    updates: Dict[str, Any] = {}
    if model is not None:
        updates["model"] = model
    if temperature is not None:
        updates["temperature"] = temperature

    has_limit_override = (
        tokens is not None
        or seconds is not None
        or cost is not None
        or (limits is not None and any([limits.tokens, limits.total, limits.seconds, limits.cost]))
    )
    if has_limit_override:
        base_budget = spec.budget
        max_output_tokens = (
            tokens
            if tokens is not None
            else (limits.tokens if limits is not None and limits.tokens is not None else base_budget.max_output_tokens)
        )
        updates["budget"] = Budget(
            max_output_tokens=max_output_tokens,
            max_total_tokens=limits.total if limits is not None and limits.total is not None else base_budget.max_total_tokens,
            max_seconds=seconds if seconds is not None else (limits.seconds if limits is not None and limits.seconds is not None else base_budget.max_seconds),
            max_cost_usd=cost if cost is not None else (limits.cost if limits is not None and limits.cost is not None else base_budget.max_cost_usd),
        )
        if max_output_tokens is not None:
            updates["max_output_tokens"] = max_output_tokens

    has_check_override = (
        check is not None
        or contains is not None
        or matches is not None
        or min_words is not None
        or goal is not None
    )
    if has_check_override:
        base_check = check or Check(
            contains=spec.success_criteria.required_substrings,
            matches=spec.success_criteria.required_regex,
            min_words=spec.success_criteria.min_word_count,
            goal=spec.success_criteria.goal,
        )
        merged = _merge_check(base_check, contains, matches, min_words, goal)
        # Goal-based: no need for min_word_count fallback.
        # Mechanical: need at least min_word_count=1 if no other checks.
        min_word_count = merged.min_words
        if not merged.goal and not merged.contains and not merged.matches and not merged.min_words:
            min_word_count = 1
        updates["success_criteria"] = SuccessCriteria(
            required_substrings=merged.contains,
            required_regex=merged.matches,
            min_word_count=min_word_count,
            case_insensitive=spec.success_criteria.case_insensitive,
            goal=merged.goal,
        )

    if updates:
        return spec.model_copy(update=updates)
    return spec


def _build_task_spec(
    task: Union[str, TaskSpec, Dict[str, Any]],
    *,
    model: Optional[str],
    tokens: Optional[int],
    seconds: Optional[float],
    cost: Optional[float],
    contains: Optional[List[str]],
    matches: Optional[List[str]],
    min_words: Optional[int],
    goal: Optional[str],
    limits: Optional[Limits],
    check: Optional[Check],
    temperature: Optional[float],
    is_rlm: bool = False,
) -> TaskSpec:
    if isinstance(task, TaskSpec):
        return _apply_task_overrides(
            task,
            model=model,
            tokens=tokens,
            seconds=seconds,
            cost=cost,
            contains=contains,
            matches=matches,
            min_words=min_words,
            goal=goal,
            limits=limits,
            check=check,
            temperature=temperature,
        )
    if isinstance(task, dict):
        # Shared normalization with CLI for JSON payloads.
        spec = task_spec_from_payload(task, model_override=model)
        return _apply_task_overrides(
            spec,
            model=None,
            tokens=tokens,
            seconds=seconds,
            cost=cost,
            contains=contains,
            matches=matches,
            min_words=min_words,
            goal=goal,
            limits=limits,
            check=check,
            temperature=temperature,
        )
    if isinstance(task, str):
        if model is None:
            raise ValueError("model is required when task is a string.")
        final_limits = _merge_limits(limits, tokens, seconds, cost)
        final_check = _merge_check(check, contains, matches, min_words, goal)

        budget = Budget(
            max_output_tokens=final_limits.tokens or DEFAULT_MAX_OUTPUT_TOKENS,
            max_total_tokens=final_limits.total,
            max_seconds=final_limits.seconds,
            max_cost_usd=final_limits.cost,
        )

        # Success criteria resolution:
        # 1. Explicit goal → use it
        # 2. Explicit checks (contains/matches/min_words) → use them
        # 3. RLM mode (data provided) → prompt IS the goal (model self-judges)
        # 4. Chat mode → simple generation, just need output
        if final_check.goal:
            success_criteria = SuccessCriteria(goal=final_check.goal)
        elif final_check.contains or final_check.matches or final_check.min_words:
            success_criteria = SuccessCriteria(
                required_substrings=final_check.contains,
                required_regex=final_check.matches,
                min_word_count=final_check.min_words,
            )
        elif is_rlm:
            # RLM mode with no explicit criteria: prompt IS the goal.
            # Model works toward achieving the prompt and self-judges completion.
            success_criteria = SuccessCriteria(goal=task)
        else:
            # Chat mode: simple generation.
            success_criteria = SuccessCriteria(min_word_count=DEFAULT_MIN_WORD_COUNT)

        return TaskSpec(
            task_id=f"task-{uuid4().hex[:8]}",
            input_text=task,
            model=model,
            budget=budget,
            success_criteria=success_criteria,
            max_output_tokens=final_limits.tokens,
            temperature=temperature,
            metadata={},
        )
    raise TypeError("task must be a string, TaskSpec, or dict.")


def generate(
    text: str,
    *,
    provider: Union[str, BaseProvider],
    model: str,
    budget: Optional[Union[Budget, Dict[str, Any]]] = None,
    success_criteria: Optional[Union[SuccessCriteria, Dict[str, Any]]] = None,
    max_output_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
    task_id: Optional[str] = None,
    return_report: bool = False,
    on_progress: Optional[Callable[[str], None]] = None,
) -> Union[str, ExecutionReport]:
    """Deprecated: use run() instead."""
    if budget is None:
        budget = Budget(max_output_tokens=256)
    if success_criteria is None:
        success_criteria = SuccessCriteria(min_word_count=1)
    spec = TaskSpec(
        task_id=task_id or f"task-{uuid4().hex[:8]}",
        input_text=text,
        model=model,
        budget=budget if isinstance(budget, Budget) else Budget(**budget),
        success_criteria=(
            success_criteria
            if isinstance(success_criteria, SuccessCriteria)
            else SuccessCriteria(**success_criteria)
        ),
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        metadata=metadata or {},
    )
    provider_instance = _resolve_provider(provider)
    engine = Engine()
    report = engine.run(spec, provider_instance, on_progress=on_progress)
    if return_report:
        return report
    return report.output_text or ""


def _resolve_provider(
    provider: Union[str, BaseProvider],
    *,
    api_key: Optional[str] = None,
    referer: Optional[str] = None,
    app_name: Optional[str] = None,
    organization: Optional[str] = None,
    project: Optional[str] = None,
) -> BaseProvider:
    """
    Resolve provider from string name or return BaseProvider instance.
    
    Uses registry to map provider names to configs. Supports custom
    providers via register_provider().
    """
    if isinstance(provider, BaseProvider):
        return provider
    name = provider.lower()
    config = get_provider_config(name)
    if config is None:
        raise ValueError(f"Unknown provider: {provider}. Use register_provider() to add custom providers.")
    
    base_url = config.get("base_url")
    supports_responses = config.get("supports_responses", False)
    headers: Dict[str, str] = {}
    
    if name == "openrouter":
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if referer or os.getenv("OPENROUTER_REFERER"):
            headers["HTTP-Referer"] = referer or os.getenv("OPENROUTER_REFERER", "")
        if app_name or os.getenv("OPENROUTER_APP_NAME"):
            headers["X-Title"] = app_name or os.getenv("OPENROUTER_APP_NAME", "")
    elif name == "openai":
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        organization = organization or os.getenv("OPENAI_ORG")
        project = project or os.getenv("OPENAI_PROJECT")
    else:
        api_key_env = f"{name.upper()}_API_KEY"
        api_key = api_key or os.getenv(api_key_env)
        # Local OpenAI-compatible servers often ignore auth; provide a dummy key if missing.
        if not api_key and _is_local_base_url(base_url):
            api_key = "local"
    
    return OpenAICompatProvider(
        name=name,
        api_key=api_key,
        base_url=base_url,
        headers=headers if headers else None,
        organization=organization if name == "openai" else None,
        project=project if name == "openai" else None,
        supports_responses=supports_responses,
    )


def _resolve_local_model_id(base_url: Optional[str]) -> Optional[str]:
    """Best-effort model auto-detection for local OpenAI-compatible servers."""
    if not base_url or not _is_local_base_url(base_url):
        return None
    try:
        import json
        import urllib.request
        url = base_url.rstrip("/") + "/models"
        with urllib.request.urlopen(url, timeout=2) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        data = payload.get("data") if isinstance(payload, dict) else payload
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return first.get("id")
        return None
    except Exception:
        return None


def resolve_provider(
    provider: Union[str, BaseProvider],
    *,
    api_key: Optional[str] = None,
    referer: Optional[str] = None,
    app_name: Optional[str] = None,
    organization: Optional[str] = None,
    project: Optional[str] = None,
) -> BaseProvider:
    """Public wrapper so CLI and users do not import a private helper."""
    return _resolve_provider(
        provider,
        api_key=api_key,
        referer=referer,
        app_name=app_name,
        organization=organization,
        project=project,
    )


def _is_local_base_url(base_url: Optional[str]) -> bool:
    if not base_url:
        return False
    parsed = urlparse(base_url)
    return parsed.hostname in {"localhost", "127.0.0.1", "::1"}
