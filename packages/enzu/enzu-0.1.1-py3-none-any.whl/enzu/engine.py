from __future__ import annotations

import re
import time
import os
from typing import Callable, Dict, List, Optional

from enzu.models import (
    BudgetUsage,
    ExecutionReport,
    ProgressEvent,
    TaskSpec,
    TrajectoryStep,
    VerificationResult,
    utc_now,
)
from enzu.providers.base import BaseProvider
from . import telemetry


class Engine:
    def run(
        self,
        task: TaskSpec,
        provider: BaseProvider,
        on_progress: Optional[Callable[[ProgressEvent], None]] = None,
        fallback_providers: Optional[List[BaseProvider]] = None,
    ) -> ExecutionReport:
        progress_events: list[ProgressEvent] = []
        trajectory: list[TrajectoryStep] = []
        errors: list[str] = []

        def emit(event: ProgressEvent) -> None:
            progress_events.append(event)
            if on_progress:
                on_progress(event)
            # Only log progress events when streaming logs are enabled.
            if telemetry.stream_enabled() or os.getenv("ENZU_LOGFIRE_PROGRESS", "").strip().lower() in {"1", "true", "yes", "on"}:
                telemetry.log(
                    "info",
                    "progress_event",
                    phase=event.phase,
                    event_message=event.message,
                    data=event.data,
                )

        with telemetry.span(
            "engine.run", task_id=task.task_id, provider=provider.name, model=task.model
        ):
            emit(
                ProgressEvent(
                    phase="start",
                    message="task_started",
                    data={"task_id": task.task_id, "provider": provider.name},
                )
            )

            # Budget limits are enforced before provider calls to keep costs bounded.
            max_output_tokens = task.max_output_tokens
            if task.budget.max_output_tokens is not None:
                if max_output_tokens is None:
                    max_output_tokens = task.budget.max_output_tokens
                elif max_output_tokens > task.budget.max_output_tokens:
                    errors.append("task.max_output_tokens exceeds budget.max_output_tokens")
                    emit(
                        ProgressEvent(
                            phase="error",
                            message="budget_limit_exceeded_preflight",
                            data={"limit": "max_output_tokens"},
                        )
                    )
                    return self._final_report(
                        task=task,
                        provider=provider,
                        output_text=None,
                        progress_events=progress_events,
                        trajectory=trajectory,
                        errors=errors,
                        started_at=None,
                        usage={},
                    )

            task = task.model_copy(update={"max_output_tokens": max_output_tokens})

            started_at = utc_now()
            started_ts = time.time()

            # Build list of providers to try (primary + fallbacks)
            all_providers = [provider] + (fallback_providers or [])
            output_text = None
            usage: Dict[str, object] = {}
            successful_provider = provider

            for current_provider in all_providers:
                try:
                    with telemetry.span("provider.stream", provider=current_provider.name):
                        provider_result = current_provider.stream(task, on_progress=emit)
                    finished_at = utc_now()
                    trajectory.append(
                        TrajectoryStep(
                            step_index=len(trajectory),
                            provider=current_provider.name,
                            model=task.model,
                            request=task.input_text,
                            response=provider_result.output_text,
                            error=None,
                            started_at=started_at,
                            finished_at=finished_at,
                            usage=provider_result.usage,
                        )
                    )
                    output_text = provider_result.output_text
                    usage = provider_result.usage
                    successful_provider = current_provider
                    break  # Success, exit the loop
                except Exception as exc:
                    finished_at = utc_now()
                    trajectory.append(
                        TrajectoryStep(
                            step_index=len(trajectory),
                            provider=current_provider.name,
                            model=task.model,
                            request=task.input_text,
                            response=None,
                            error=str(exc),
                            started_at=started_at,
                            finished_at=finished_at,
                            usage={},
                        )
                    )
                    if current_provider == all_providers[-1]:
                        # Last provider failed, return error
                        errors.append(str(exc))
                        emit(
                            ProgressEvent(
                                phase="error",
                                message="provider_error",
                                data={"error": str(exc), "provider": current_provider.name},
                            )
                        )
                        return self._final_report(
                            task=task,
                            provider=current_provider,
                            output_text=None,
                            progress_events=progress_events,
                            trajectory=trajectory,
                            errors=errors,
                            started_at=started_ts,
                            usage={},
                        )
                    # Not the last provider, log and continue to next
                    errors.append(f"{current_provider.name}: {exc}")
                    emit(
                        ProgressEvent(
                            phase="error",
                            message="provider_fallback",
                            data={"error": str(exc), "provider": current_provider.name},
                        )
                    )
                    started_at = utc_now()  # Reset for next provider
                    continue

            emit(
                ProgressEvent(
                    phase="verification",
                    message="verification_started",
                    data={"task_id": task.task_id},
                )
            )
            verification = self._verify_output(task, output_text)
            elapsed_seconds = time.time() - started_ts
            budget_usage = self._budget_usage(task, usage, elapsed_seconds)
            budget_exceeded = bool(budget_usage.limits_exceeded)

            # Fallback errors don't count as failures if we succeeded
            final_errors = [] if output_text else errors
            success = verification.passed and not budget_exceeded and not final_errors
            emit(
                ProgressEvent(
                    phase="complete",
                    message="task_completed",
                    data={"success": success, "provider": successful_provider.name},
                )
            )
            return ExecutionReport(
                success=success,
                task_id=task.task_id,
                provider=successful_provider.name,
                model=task.model,
                output_text=output_text,
                verification=verification,
                budget_usage=budget_usage,
                progress_events=progress_events,
                trajectory=trajectory,
                errors=errors,  # Keep fallback errors for debugging
            )

    def _verify_output(self, task: TaskSpec, output_text: str) -> VerificationResult:
        reasons: list[str] = []
        passed = True
        case_insensitive = task.success_criteria.case_insensitive
        check_text = output_text.casefold() if case_insensitive else output_text
        for required in task.success_criteria.required_substrings:
            needle = required.casefold() if case_insensitive else required
            if needle not in check_text:
                passed = False
                reasons.append(f"missing_substring:{required}")
        regex_flags = re.MULTILINE | (re.IGNORECASE if case_insensitive else 0)
        for pattern in task.success_criteria.required_regex:
            if re.search(pattern, output_text, regex_flags) is None:
                passed = False
                reasons.append(f"missing_regex:{pattern}")
        if task.success_criteria.min_word_count:
            word_count = len(output_text.split())
            if word_count < task.success_criteria.min_word_count:
                passed = False
                reasons.append(
                    f"min_word_count:{task.success_criteria.min_word_count}"
                )
        return VerificationResult(passed=passed, reasons=reasons)

    def _budget_usage(
        self, task: TaskSpec, usage: Dict[str, object], elapsed_seconds: float
    ) -> BudgetUsage:
        output_tokens = self._read_int(usage, ["output_tokens", "completion_tokens"])
        total_tokens = self._read_int(usage, ["total_tokens"])
        cost_usd = self._read_float(usage, ["cost_usd"])

        limits_exceeded: list[str] = []
        if task.budget.max_seconds and elapsed_seconds > task.budget.max_seconds:
            limits_exceeded.append("max_seconds")
        if task.budget.max_output_tokens and output_tokens:
            if output_tokens > task.budget.max_output_tokens:
                limits_exceeded.append("max_output_tokens")
        if task.budget.max_total_tokens and total_tokens:
            if total_tokens > task.budget.max_total_tokens:
                limits_exceeded.append("max_total_tokens")
        if task.budget.max_cost_usd and cost_usd is not None:
            if cost_usd > task.budget.max_cost_usd:
                limits_exceeded.append("max_cost_usd")

        return BudgetUsage(
            elapsed_seconds=elapsed_seconds,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            limits_exceeded=limits_exceeded,
        )

    @staticmethod
    def _read_int(usage: Dict[str, object], keys: list[str]) -> Optional[int]:
        for key in keys:
            value = usage.get(key)
            if isinstance(value, int):
                return value
        return None

    @staticmethod
    def _read_float(usage: Dict[str, object], keys: list[str]) -> Optional[float]:
        for key in keys:
            value = usage.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return None

    def _final_report(
        self,
        task: TaskSpec,
        provider: BaseProvider,
        output_text: Optional[str],
        progress_events: list[ProgressEvent],
        trajectory: list[TrajectoryStep],
        errors: list[str],
        started_at: Optional[float],
        usage: Dict[str, object],
    ) -> ExecutionReport:
        elapsed_seconds = 0.0 if started_at is None else time.time() - started_at
        budget_usage = self._budget_usage(task, usage, elapsed_seconds)
        verification = VerificationResult(passed=False, reasons=["no_output"])
        return ExecutionReport(
            success=False,
            task_id=task.task_id,
            provider=provider.name,
            model=task.model,
            output_text=output_text,
            verification=verification,
            budget_usage=budget_usage,
            progress_events=progress_events,
            trajectory=trajectory,
            errors=errors,
        )
