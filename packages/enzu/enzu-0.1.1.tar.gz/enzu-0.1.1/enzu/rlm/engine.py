"""
RLM Engine with guardrails for code-first patterns.

Provides structured feedback to guide the model toward:
1. Using code for context manipulation (filtering, chunking)
2. Using llm_query sparingly for semantic tasks only
3. Using safe helpers for error-free execution
"""
from __future__ import annotations

import re
import time
from uuid import uuid4
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from enzu.contract import DEFAULT_MIN_WORD_COUNT
from enzu.models import (
    Budget,
    BudgetUsage,
    RLMExecutionReport,
    RLMStep,
    StepFeedback,
    SuccessCriteria,
    TaskSpec,
    VerificationResult,
)
from enzu.providers.base import BaseProvider
from enzu.repl import PythonSandbox, SAFE_HELPERS
from .. import telemetry


# Error classification: maps error patterns to actionable hints
ERROR_HINTS = {
    "KeyError": "Use safe_get(d, key, default) for dict access",
    "'NoneType' object is not subscriptable": "Use safe_get(d, key, default) for dict access",
    "'NoneType' object is not iterable": "Use safe_rows(context) to extract list safely",
    "object has no attribute": "Use safe_rows(context) to handle None/missing attributes",
    "not supported between instances": "Use safe_sort(context, key) for type-safe sorting",
    "'NoneType' object has no attribute": "Check for None before accessing attributes",
    "list index out of range": "Check list length before indexing",
    # Raise a clear setup hint when search tools are missing.
    "Search tools unavailable": "Set EXA_API_KEY to enable Exa search tools",
}


def classify_error(error: Optional[str]) -> Optional[str]:
    """Map error message to actionable hint."""
    if not error:
        return None
    for pattern, hint in ERROR_HINTS.items():
        if pattern in error:
            return hint
    return None


def _read_usage_int(usage: dict, keys: Tuple[str, ...]) -> Optional[int]:
    """Normalize provider usage keys (e.g., completion_tokens -> output_tokens)."""
    for key in keys:
        value = usage.get(key)
        if isinstance(value, int):
            return value
    return None


def _trim_text(text: Optional[str], limit: int = 2000) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit]


def _format_success_criteria(criteria: SuccessCriteria) -> str:
    """
    Render success criteria for the system prompt.

    Two modes:
    1. Goal-based: tell model the goal, trust its FINAL() judgment
    2. Mechanical: list specific checks (substrings, regex, word count)
    """
    # Goal-based: model self-judges when goal is achieved.
    if criteria.goal:
        return (
            f"Goal: {criteria.goal}\n\n"
            "Work toward this goal. Call FINAL(answer) when you believe the goal is achieved.\n"
            "You are the judge of success. Continue until you are confident or budget runs out.\n\n"
        )

    # Mechanical: predefined checks.
    lines: list[str] = []
    if criteria.required_substrings:
        lines.append(
            "Required substrings: " + ", ".join(criteria.required_substrings)
        )
    if criteria.required_regex:
        lines.append("Required regex: " + ", ".join(criteria.required_regex))
    if criteria.min_word_count:
        lines.append(f"Minimum word count: {criteria.min_word_count}")
    if criteria.case_insensitive:
        lines.append("Case-insensitive checks: true")
    if not lines:
        return ""
    bullets = "\n- ".join(lines)
    return (
        "Success criteria (stop only when met):\n"
        "- " + bullets + "\n"
        "If criteria are not met, continue and try again.\n\n"
    )


def _has_strong_success_criteria(criteria: SuccessCriteria) -> bool:
    """
    Return True when criteria set a concrete stop condition.

    Strong criteria:
    - Mechanical: required_substrings, required_regex, or min_word_count > default
    - Goal-based: goal field is set (model self-judges completion)
    """
    if criteria.required_substrings or criteria.required_regex:
        return True
    if criteria.min_word_count and criteria.min_word_count > DEFAULT_MIN_WORD_COUNT:
        return True
    # Goal-based success: model self-judges, no mechanical checks needed.
    if criteria.goal:
        return True
    return False


def analyze_code_patterns(code: str) -> List[str]:
    """
    Detect anti-patterns in code to guide toward better RLM patterns.
    
    Returns list of warnings about patterns that waste compute or miss opportunities.
    """
    if not code:
        return []

    warnings = []

    # Over-delegation: llm_query inside a loop (called N times at runtime)
    has_loop = re.search(r'(for|while)\s+.+:', code)
    llm_calls = len(re.findall(r'llm_query\s*\(', code))
    if has_loop and llm_calls >= 1:
        # Check if llm_query appears after the loop statement (likely inside loop body)
        loop_match = re.search(r'(for|while)\s+.+:', code)
        if loop_match:
            post_loop = code[loop_match.end():]
            if 'llm_query' in post_loop:
                warnings.append(
                    f"llm_query inside loop (called N times at runtime). "
                    "Batch chunks: llm_query(f'Process:\\n{{chunk1}}\\n{{chunk2}}')"
                )

    # Passing full context to llm_query without filtering
    if re.search(r'llm_query\([^)]*\b(context|data)\b[^)]*\)', code):
        # Check if context/data is being sliced/filtered
        if not re.search(r'(context|data)\[', code) and 'for' not in code:
            warnings.append(
                "Passing full context to llm_query. "
                "Filter/chunk first: chunks = [context[1][i:i+1000] for i in range(0, len(context[1]), 1000)]"
            )

    # Code-doable tasks delegated to llm_query
    code_doable = ['count', 'filter', 'sort', 'format', 'join', 'split', 'len']
    for keyword in code_doable:
        if re.search(rf'llm_query\([^)]*\b{keyword}\b[^)]*\)', code, re.I):
            warnings.append(
                f"'{keyword}' can be done in code. Reserve llm_query for semantic tasks "
                "(classification, summarization, interpretation)."
            )

    return warnings


def extract_code(model_output: str) -> Tuple[Optional[str], int]:
    """
    Extract code from model output.
    
    Returns (first_block, total_block_count) for feedback.
    Takes first block (not last) because first usually contains setup code.
    """
    matches = re.findall(r"```(?:python|repl)?\s*\n(.*?)```", model_output, re.DOTALL)
    if not matches:
        return None, 0
    return matches[0].strip(), len(matches)


def build_feedback(
    stdout: str,
    error: Optional[str],
    code: Optional[str],
    block_count: int,
) -> StepFeedback:
    """Build structured feedback from execution result."""
    violation = f"multiple_blocks:{block_count}" if block_count > 1 else None
    hint = classify_error(error)
    pattern_warnings = analyze_code_patterns(code) if code else []

    return StepFeedback(
        violation=violation,
        hint=hint,
        available_helpers=list(SAFE_HELPERS.keys()),
        pattern_warnings=pattern_warnings,
        stdout=stdout,
        error=error,
    )


def format_feedback(feedback: StepFeedback) -> str:
    """Format StepFeedback into prompt section."""
    lines = []

    # Structural violations
    if feedback.violation:
        if feedback.violation.startswith("multiple_blocks"):
            count = feedback.violation.split(":")[1]
            lines.append(
                f"[VIOLATION] You wrote {count} code blocks. "
                "Only the first was executed. Consolidate into one block."
            )

    # Verification rejection feedback
    if feedback.rejection_reasons:
        reasons = ", ".join(feedback.rejection_reasons)
        lines.append(f"[REJECTED] Answer failed verification: {reasons}")

    # Execution results
    if feedback.stdout:
        lines.append(f"[OUTPUT]\n{feedback.stdout}")

    if feedback.error:
        lines.append(f"[ERROR]\n{feedback.error}")

    # Error recovery hints
    if feedback.hint:
        lines.append(f"[HINT] {feedback.hint}")

    # Code pattern guidance
    for warning in feedback.pattern_warnings:
        lines.append(f"[PATTERN] {warning}")

    return "\n".join(lines)


# System prompt additions for code-first patterns
SYSTEM_PROMPT_GUARDRAILS = """
## Code-First Patterns

The prompt lives in `context`. Write code to manipulate it:

1. Probe: print(context[0]) for the query; print(context[1][:500]) for data if present
2. Filter in code: relevant = [x for x in chunks if 'keyword' in x]
3. Delegate to sub-LLMs: use llm_query or llm_batch (see below)
4. Aggregate in code: counts = {k: v for k, v in results}

## Sub-LLM Calls: llm_query vs llm_batch

**llm_query(prompt)** - Sequential single call
- Use for: one-off queries, dependent operations
- Example: `result = llm_query("Summarize this text")`

**llm_batch(prompts)** - Parallel batch calls (MUCH FASTER)
- Use for: independent queries that can run simultaneously
- Returns list in same order as inputs
- Example:
  ```python
  prompts = [f"Classify: {chunk}" for chunk in filtered_chunks]
  results = llm_batch(prompts)  # All run in parallel
  ```

CRITICAL: When you have multiple independent sub-queries, ALWAYS use llm_batch instead of loops with llm_query. This reduces latency by N× where N is the number of queries.

## When to Use llm_query/llm_batch

USE for: semantic classification, summarization, meaning extraction
DO NOT use for: counting, filtering, sorting, formatting, string ops

## Safe Helpers (available in namespace)

- safe_get(d, key, default): Dict access that never crashes
- safe_rows(context): Extract list from any structure
- safe_sort(context, key): Sort without type errors

## Rules

- ONE code block per response. Multiple blocks = only first executes.
- Filter before delegating. Don't pass full context to sub-LLMs.
- Use llm_batch for parallel queries, not loops with llm_query.
"""

# Search tools guidance (injected when search tools are available)
SEARCH_TOOLS_GUIDANCE = """
## Web Research Tools

### RECOMMENDED: High-Level Functions (use these first)

**research(topic)** - All-in-one research function
```python
# Simple usage - does search, filter, and format for you
result = research("AI agents")
print(result["stats"])  # {'total_found': 15, 'kept': 8, 'context_length': 12000}

# The context is ready for llm_query
summary = llm_query(f"Write a newsletter about:\\n{result['context']}")
FINAL(summary)
```

**research() options:**
```python
result = research(
    "AI agents",
    num_results=10,        # Results per search
    min_score=0.5,         # Quality filter (0-1)
    max_characters=None,   # None = no per-result limit
    max_chars_per_source=None,  # None = no per-source truncation
    include_news=True,     # Add news articles
    include_papers=True,   # Add research papers
    days_back=7,           # Recent content only
)
```
Note: research() auto-adds results to the context store when available.
Note: Context formatting includes Published dates when present.

**explore(url)** - Find similar content from a good source
```python
result = explore("https://good-article.com/...")
summary = llm_query(f"Summarize related content:\\n{result['context']}")
```
Note: explore() auto-adds results to the context store when available.
Note: Context formatting includes Published dates when present.

**format_sources(sources)** - Create citation list
```python
refs = format_sources(result["sources"])
FINAL(summary + "\\n\\n" + refs)
```

### Low-Level Functions (for fine control)

**exa_search(query)** - Direct search
```python
results = exa_search("AI", num_results=5, category="news", days_back=7)
# Returns: [{"url", "title", "text", "score", "highlights", "published_date"}, ...]
```

**exa_news(query)** / **exa_papers(query)** - Category shortcuts
**exa_similar(url)** - Find related pages
**exa_contents(urls)** - Fetch specific URLs
Note: exa_* functions auto-add results to the context store when available.

### Categories: "news", "research paper", "github", "company", "pdf", "tweet"

## Workflow Example

```python
# Step 1: Research the topic (defaults to last 7 days)
topic = "AI agents"
result = research(topic, include_news=True)
print(f"Found {result['stats']['kept']} quality sources")

# Step 2: If not enough, search more
if result['stats']['kept'] < 3:
    more = research(topic, min_score=0.3, num_results=20)

# Step 3: Get accumulated context and synthesize
context = ctx_get(max_chars=40000, max_chars_per_source=None)
newsletter = llm_query(f'''
Write a newsletter section about {topic}.

Sources:
{context}

Include:
- Key insights and trends
- Notable quotes with attribution
- 3-5 bullet point takeaways
''')

# Step 4: Finish with citations
FINAL(newsletter + "\\n\\n" + format_sources(ctx_sources()))
```

## Context Management (for accumulating research)

**ctx_add(sources, query)** - Add sources to persistent store (deduped)
**ctx_get(max_chars=50000, max_chars_per_source=None)** - Get accumulated context for llm_query (includes Published date)
**ctx_stats()** - Check what's accumulated
**ctx_sources()** - Get list of all sources
**ctx_has_query(q)** - Check if query was already done (avoid re-searching)
**ctx_save(path)** - Save for later (actu.me persistence)
**ctx_load(path)** - Load previous research

**exa_cost()** - Check search API costs for this session

## Context Bootstrapping

- If ctx_stats()["num_sources"] == 0, run research() or exa_search() first.
- Persist context with ctx_save(path) after gathering sources.
"""

# Package installation guidance (injected when enable_pip=True)
PIP_INSTALL_GUIDANCE = """
## Dynamic Package Installation

**pip_install(*packages)** - Install any pip package during execution

Examples:
```python
# Install single package
pip_install("numpy")
import numpy as np

# Install multiple packages at once
pip_install("pandas", "scipy", "matplotlib")
import pandas as pd

# Standard library always available (no install needed)
import re, math, json, datetime
```

The RLM tracks which packages are installed. You can install any package from PyPI as needed for your task.

BEST PRACTICE: Install packages before using them. Check if you need specialized libraries (numpy for math, pandas for data, beautifulsoup4 for HTML parsing, etc.) and install them first.
"""

# Strategy hints for larger context (injected when length >= 10K chars)
STRATEGY_HINTS = """
## Strategy by Context Size
- Small (<10K chars): Direct analysis, few llm_query calls
- Medium (10K-100K): Chunk by structure (lines, paragraphs, ###)
- Large (>100K): Probe first, filter by keywords, batch llm_query

## Efficient Patterns
- Probe: print(context[0]) to read the query; print(context[1][:500]) to sample data if present
- Filter in code: relevant = [x for x in chunks if 'keyword' in x]
- Batch llm_query: result = llm_query(f"Process all:\\n{chunk1}\\n{chunk2}")
- Aggregate in code: counts = Counter(results)

## Anti-patterns (costly)
- llm_query per line (N calls) -> batch into ~5-10 calls max
- llm_query(context) without filtering -> slice or filter first
- llm_query for counting/sorting -> use Python
"""


class RLMEngine:
    """
    RLM (Recursive Language Model) engine following the paper's architecture:
    - Main RLM: orchestrates via code, delegates semantic work to sub-LLMs
    - Sub-LLMs: have tools (search, etc.) to do actual work

    This separation keeps main context small and encourages proper delegation.
    See: arxiv.org/html/2512.24601v1, primeintellect.ai/blog/rlm
    """

    def __init__(
        self,
        *,
        max_steps: int = 8,
        output_char_limit: int = 8192,
        allowed_imports: Optional[List[str]] = None,
        verify_on_final: bool = True,
        # Paper architecture: main RLM delegates to sub-RLMs that have tools.
        # True = llm_query spawns sub-RLM with sandbox (paper's recommendation).
        # False = llm_query makes direct LLM call without sandbox.
        recursive_subcalls: bool = True,
        max_recursion_depth: int = 1,
        subcall_max_steps: int = 3,
        subcall_max_output_tokens: int = 1024,
        subcall_verify_on_final: bool = False,
        enable_pip: bool = False,
        prompt_style: str = "paper",
        # Paper architecture: main RLM has no tools, sub-RLMs have tools.
        # False = main delegates tool use to sub-RLMs (paper's recommendation).
        # True = main has direct tool access (simpler but bloats context).
        inject_search_tools: bool = False,
        # Sub-RLMs get tools by default (paper's "sub-LLMs receive tools").
        subcall_inject_search_tools: bool = True,
    ) -> None:
        self._max_steps = max_steps
        self._output_char_limit = output_char_limit
        self._allowed_imports = allowed_imports or ["re", "math", "json", "datetime", "collections", "itertools", "functools"]
        self._enable_pip = enable_pip
        if prompt_style not in {"paper", "extended"}:
            raise ValueError("prompt_style must be 'paper' or 'extended'.")
        self._prompt_style = prompt_style
        # When True, FINAL() is rejected if verification fails and loop continues.
        # When False, FINAL() is accepted immediately (verification still runs after loop).
        self._verify_on_final = verify_on_final
        self._recursive_subcalls = recursive_subcalls
        self._max_recursion_depth = max(0, max_recursion_depth)
        self._subcall_max_steps = subcall_max_steps
        self._subcall_max_output_tokens = subcall_max_output_tokens
        self._subcall_verify_on_final = subcall_verify_on_final
        self._inject_search_tools = inject_search_tools
        self._subcall_inject_search_tools = subcall_inject_search_tools

    @staticmethod
    def _build_context(query: str, data: Any) -> List[Any]:
        """Construct the RLM prompt chunks (query first, data after)."""
        if data is None:
            return [query]
        if isinstance(data, list):
            return [query, *data]
        return [query, data]

    @staticmethod
    def _context_stats(context: Any) -> Tuple[str, int, List[int]]:
        """Summarize context for prompt metadata."""
        if isinstance(context, (list, tuple)):
            lengths = [len(str(item)) for item in context]
            return type(context).__name__, sum(lengths), lengths
        text = str(context)
        return type(context).__name__, len(text), [len(text)]

    def _build_sub_engine(self) -> "RLMEngine":
        """Create sub-RLM for recursive calls. Per paper: sub-RLMs have tools."""
        return RLMEngine(
            max_steps=self._subcall_max_steps,
            output_char_limit=self._output_char_limit,
            allowed_imports=list(self._allowed_imports),
            verify_on_final=self._subcall_verify_on_final,
            # Sub-RLMs don't recurse further (depth limit enforced in _run_subcall).
            recursive_subcalls=False,
            max_recursion_depth=0,
            subcall_max_steps=self._subcall_max_steps,
            subcall_max_output_tokens=self._subcall_max_output_tokens,
            subcall_verify_on_final=self._subcall_verify_on_final,
            prompt_style="extended",  # Sub-RLMs need tool docs in prompt.
            # Paper: "sub-LLMs receive tools" - this is where tools live.
            inject_search_tools=self._subcall_inject_search_tools,
            subcall_inject_search_tools=False,
        )

    def _run_subcall(
        self,
        *,
        parent_task: TaskSpec,
        provider: BaseProvider,
        prompt: str,
        depth: int,
    ) -> RLMExecutionReport:
        """Run a depth-limited recursive RLM subcall."""
        import json
        # Subcall prompt stored in context. Mark as subcall for testing/debugging.
        sub_metadata = {
            k: v
            for k, v in parent_task.metadata.items()
            if k not in {"prelude_code", "prelude_allow_final"}
        }
        sub_metadata["_subcall_prompt"] = prompt  # Enables MockProvider detection
        if sub_metadata.get("subcall_mode") == "research" and not str(prompt).startswith("__DECIDE__:"):
            # Deterministic research subcall: execute tool code before any model step.
            query = json.dumps(prompt)
            sub_metadata["prelude_code"] = (
                "import json\n"
                f"query = {query}\n"
                "sources = []\n"
                "try:\n"
                "    result = research(\n"
                "        query,\n"
                "        include_news=True,\n"
                "        days_back=180,\n"
                "        min_score=0.2,\n"
                "        num_results=6,\n"
                "        max_characters=4000,\n"
                "        max_chars_per_source=600,\n"
                "    )\n"
                "    raw = result.get('sources', [])\n"
                "    for s in raw[:3]:\n"
                "        sources.append({\n"
                "            'title': s.get('title', ''),\n"
                "            'url': s.get('url', ''),\n"
                "            'published_date': s.get('published_date', ''),\n"
                "            'text': (s.get('text', '') or '')[:300],\n"
                "        })\n"
                "except Exception:\n"
                "    sources = []\n"
                "FINAL(json.dumps(sources))\n"
            )
            sub_metadata["prelude_allow_final"] = True
        sub_task = TaskSpec(
            task_id=f"{parent_task.task_id}:sub:{uuid4().hex[:8]}",
            input_text="Execute prelude code and return JSON only.",
            model=parent_task.model,
            budget=Budget(max_output_tokens=self._subcall_max_output_tokens),
            success_criteria=SuccessCriteria(min_word_count=1),
            metadata=sub_metadata,
        )
        sub_engine = self._build_sub_engine()
        return sub_engine.run(
            sub_task,
            provider,
            data="",
            depth=depth,
            prompt_env=prompt,
        )

    def run(
        self,
        task: TaskSpec,
        provider: BaseProvider,
        *,
        data: str,
        namespace: Optional[Dict[str, Any]] = None,
        on_progress: Optional[Callable[[str], None]] = None,
        depth: int = 0,
        prompt_env: Optional[Any] = None,
        fallback_providers: Optional[List[BaseProvider]] = None,
    ) -> RLMExecutionReport:
        steps: list[RLMStep] = []
        errors: list[str] = []
        # Align RLM token cap with chat Engine preflight.
        max_output_tokens = task.max_output_tokens
        if task.budget.max_output_tokens is not None:
            if max_output_tokens is None:
                max_output_tokens = task.budget.max_output_tokens
            elif max_output_tokens > task.budget.max_output_tokens:
                errors.append("task.max_output_tokens exceeds budget.max_output_tokens")
                budget_usage = self._budget_usage(task, {}, 0.0)
                return RLMExecutionReport(
                    success=False,
                    task_id=task.task_id,
                    provider=provider.name,
                    model=task.model,
                    answer=None,
                    steps=steps,
                    budget_usage=budget_usage,
                    errors=errors,
                )
        if max_output_tokens != task.max_output_tokens:
            task = task.model_copy(update={"max_output_tokens": max_output_tokens})
        # Require explicit criteria so RLM stops on a real condition.
        if (
            not _has_strong_success_criteria(task.success_criteria)
            and not task.metadata.get("allow_weak_success_criteria")
        ):
            errors.append("success_criteria_missing_or_weak")
            budget_usage = self._budget_usage(task, {}, 0.0)
            return RLMExecutionReport(
                success=False,
                task_id=task.task_id,
                provider=provider.name,
                model=task.model,
                answer=None,
                steps=steps,
                budget_usage=budget_usage,
                errors=errors,
            )

        start_ts = time.time()
        usage_accumulator = {"output_tokens": 0, "total_tokens": 0}
        remaining = _BudgetTracker(task.budget)
        context_path = task.metadata.get("context_path")
        context_before: Optional[Dict[str, Any]] = None
        # Paper format: store the prompt in the REPL as `context`, not in the system prompt.
        context_env = (
            prompt_env
            if prompt_env is not None
            else self._build_context(task.input_text, data)
        )
        context_type, context_len, context_lengths = self._context_stats(context_env)

        def emit(message: str) -> None:
            if on_progress:
                on_progress(message)
            # Skip noisy token stream events unless explicitly enabled.
            if message.startswith("llm_stream:") and not telemetry.stream_enabled():
                return
            telemetry.log("info", "rlm_progress", progress_message=message)

        def direct_llm_query(prompt: str, *, span_name: str) -> str:
            if remaining.is_exhausted():
                raise RuntimeError("budget_exhausted")
            # Build list of providers to try (primary + fallbacks)
            all_providers = [provider] + (fallback_providers or [])
            last_exception = None
            for current_provider in all_providers:
                try:
                    with telemetry.span(span_name, prompt_len=len(prompt), provider=current_provider.name):
                        result = current_provider.stream(
                            task.model_copy(update={"input_text": prompt}),
                            on_progress=lambda event: emit(f"llm_stream:{event.message}"),
                        )
                    self._accumulate_usage(usage_accumulator, result.usage)
                    remaining.consume(result.usage)
                    telemetry.log(
                        "info",
                        "llm_query_done",
                        prompt=_trim_text(prompt),
                        output=_trim_text(result.output_text),
                        output_len=len(result.output_text),
                        provider=current_provider.name,
                    )
                    return result.output_text
                except Exception as exc:
                    last_exception = exc
                    if current_provider == all_providers[-1]:
                        # Last provider, re-raise
                        raise
                    # Log fallback and continue
                    errors.append(f"{current_provider.name}: {exc}")
                    telemetry.log(
                        "warning",
                        "llm_query_fallback",
                        provider=current_provider.name,
                        error=str(exc),
                    )
                    continue
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("No providers available")

        def sandbox_llm_query(prompt: str) -> str:
            if remaining.is_exhausted():
                raise RuntimeError("budget_exhausted")
            if self._recursive_subcalls and depth < self._max_recursion_depth:
                with telemetry.span("rlm.llm_query_recursive", prompt_len=len(prompt)):
                    sub_report = self._run_subcall(
                        parent_task=task,
                        provider=provider,
                        prompt=prompt,
                        depth=depth + 1,
                    )
                sub_usage = {
                    "output_tokens": sub_report.budget_usage.output_tokens,
                    "total_tokens": sub_report.budget_usage.total_tokens,
                    "cost_usd": sub_report.budget_usage.cost_usd,
                }
                self._accumulate_usage(usage_accumulator, sub_usage)
                remaining.consume(sub_usage)
                telemetry.log(
                    "info",
                    "llm_query_recursive_done",
                    prompt=_trim_text(prompt),
                    output=_trim_text(sub_report.answer),
                    output_len=len(sub_report.answer or ""),
                )
                return sub_report.answer or ""
            return direct_llm_query(prompt, span_name="rlm.llm_query")

        def llm_batch(prompts: list) -> list:
            """
            Execute multiple LLM queries in parallel for optimal latency.
            Returns results in the same order as input prompts.

            Implementation: provider.stream() is synchronous, so we use
            loop.run_in_executor() to run calls in a thread pool without
            blocking the event loop. This enables true concurrent execution.
            """
            import asyncio
            import concurrent.futures
            import threading

            if remaining.is_exhausted():
                raise RuntimeError("budget_exhausted")

            if not prompts:
                return []

            if self._recursive_subcalls and depth < self._max_recursion_depth:
                lock = threading.Lock()

                def query_one_subcall(prompt: str, index: int) -> tuple:
                    if remaining.is_exhausted():
                        raise RuntimeError("budget_exhausted")
                    with telemetry.span(
                        "rlm.llm_batch.subcall",
                        prompt_len=len(prompt),
                        batch_index=index,
                    ):
                        sub_report = self._run_subcall(
                            parent_task=task,
                            provider=provider,
                            prompt=prompt,
                            depth=depth + 1,
                        )
                    sub_usage = {
                        "output_tokens": sub_report.budget_usage.output_tokens,
                        "total_tokens": sub_report.budget_usage.total_tokens,
                        "cost_usd": sub_report.budget_usage.cost_usd,
                    }
                    with lock:
                        self._accumulate_usage(usage_accumulator, sub_usage)
                        remaining.consume(sub_usage)
                    telemetry.log(
                        "info",
                        "llm_batch_subcall_done",
                        batch_index=index,
                        prompt=_trim_text(prompt),
                        output=_trim_text(sub_report.answer),
                        output_len=len(sub_report.answer or ""),
                    )
                    return (index, sub_report.answer or "")

                with telemetry.span("rlm.llm_batch", batch_size=len(prompts)):
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(query_one_subcall, p, i)
                            for i, p in enumerate(prompts)
                        ]
                        results = [future.result() for future in futures]
                return [output for _, output in sorted(results)]

            def query_one_sync(prompt: str, index: int) -> tuple:
                """
                Synchronous query wrapper for thread pool execution.
                Returns (index, result) tuple to maintain input order.
                Supports provider fallback on failure.
                """
                all_providers = [provider] + (fallback_providers or [])
                for current_provider in all_providers:
                    try:
                        with telemetry.span(
                            "rlm.llm_batch.query",
                            prompt_len=len(prompt),
                            batch_index=index,
                            provider=current_provider.name,
                        ):
                            result = current_provider.stream(
                                task.model_copy(update={"input_text": prompt}),
                                on_progress=lambda event: emit(f"llm_stream:batch[{index}]:{event.message}"),
                            )
                        # Track usage and budget for this query
                        self._accumulate_usage(usage_accumulator, result.usage)
                        remaining.consume(result.usage)
                        telemetry.log(
                            "info",
                            "llm_batch_query_done",
                            batch_index=index,
                            prompt=_trim_text(prompt),
                            output=_trim_text(result.output_text),
                            output_len=len(result.output_text),
                            provider=current_provider.name,
                        )
                        return (index, result.output_text)
                    except Exception as exc:
                        if current_provider == all_providers[-1]:
                            raise
                        telemetry.log(
                            "warning",
                            "llm_batch_query_fallback",
                            batch_index=index,
                            provider=current_provider.name,
                            error=str(exc),
                        )
                        continue
                raise RuntimeError("No providers available")

            async def run_batch():
                """
                Run all queries concurrently using thread pool.
                loop.run_in_executor() returns awaitable futures that
                asyncio.gather() can coordinate.
                """
                with telemetry.span("rlm.llm_batch", batch_size=len(prompts)):
                    loop = asyncio.get_event_loop()
                    # Wrap each sync call in run_in_executor for concurrent execution
                    futures = [
                        loop.run_in_executor(None, query_one_sync, p, i)
                        for i, p in enumerate(prompts)
                    ]
                    results = await asyncio.gather(*futures)
                    # Sort by index to preserve input order
                    return [output for _, output in sorted(results)]

            # Execute in event loop (create new if none exists)
            try:
                loop = asyncio.get_running_loop()
                # Already in event loop: run in separate thread to avoid nesting
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, run_batch())
                    return future.result()
            except RuntimeError:
                # No event loop: safe to create and run
                return asyncio.run(run_batch())

        with telemetry.span(
            "rlm.run", task_id=task.task_id, provider=provider.name, model=task.model
        ):
            if context_path:
                try:
                    from enzu.tools.context import ctx_load, ctx_stats
                    path = Path(context_path)
                    if path.exists():
                        ctx_load(str(path))
                    # Snapshot before run to detect growth and avoid redundant writes.
                    context_before = ctx_stats()
                    telemetry.log(
                        "info",
                        "context_loaded",
                        path=str(path),
                        stats=context_before,
                    )
                except Exception:
                    context_before = None

            # Prompt lives in the REPL environment per the paper format.
            sandbox = PythonSandbox(
                data=data,
                context=context_env,
                llm_query=sandbox_llm_query,
                llm_batch=llm_batch,
                namespace=namespace,
                allowed_imports=self._allowed_imports,
                output_char_limit=self._output_char_limit,
                timeout_seconds=task.budget.max_seconds,
                inject_safe_helpers=True,
                # Paper: main RLM delegates tools to sub-RLMs via llm_query().
                inject_search_tools=self._inject_search_tools,
                enable_pip=self._enable_pip,
            )

            prelude_code = task.metadata.get("prelude_code")
            if prelude_code:
                with telemetry.span("rlm.prelude", code_len=len(prelude_code)):
                    result = sandbox.exec(prelude_code)
                telemetry.log(
                    "info",
                    "rlm_prelude_result",
                    stdout=_trim_text(result.stdout),
                    error=_trim_text(result.error),
                )
                if sandbox.answer.get("ready"):
                    if task.metadata.get("prelude_allow_final"):
                        answer = sandbox.answer.get("content") or ""
                        verification = self._verify_output(task, answer)
                        if verification.passed:
                            telemetry.log("info", "rlm_prelude_final_accept")
                            elapsed_seconds = time.time() - start_ts
                            budget_usage = self._budget_usage(
                                task, usage_accumulator, elapsed_seconds
                            )
                            return RLMExecutionReport(
                                success=True,
                                task_id=task.task_id,
                                provider=provider.name,
                                model=task.model,
                                answer=answer,
                                steps=steps,
                                budget_usage=budget_usage,
                                errors=[],
                            )
                        telemetry.log(
                            "info",
                            "rlm_prelude_final_reject",
                            reasons=verification.reasons,
                        )
                    # Prevent prelude from short-circuiting the run unless allowed.
                    sandbox.answer["ready"] = False
                    sandbox.answer["content"] = ""

            # Use explicit marker so stubs do not enable search guidance.
            has_search_tools = bool(
                sandbox.namespace.get("__search_tools_available__")
            )
            prompt = self._system_prompt(
                task,
                data_len=context_len,
                context_type=context_type,
                context_lengths=context_lengths,
                has_search_tools=has_search_tools,
            )
            telemetry.log(
                "info",
                "rlm_prompt_init",
                task_id=task.task_id,
                data_len=context_len,
                has_search_tools=has_search_tools,
                prompt=_trim_text(prompt),
            )
            for step_index in range(self._max_steps):
                if self._budget_exceeded(task, start_ts, usage_accumulator):
                    errors.append("budget_exceeded")
                    telemetry.log(
                        "info",
                        "rlm_budget_exceeded",
                        step_index=step_index,
                        usage=usage_accumulator,
                    )
                    break
                emit(f"rlm_step_started:{step_index}")
                with telemetry.span("rlm.step", step_index=step_index):
                    model_output = direct_llm_query(prompt, span_name="rlm.step_query")
                    telemetry.log(
                        "info",
                        "rlm_model_output",
                        step_index=step_index,
                        text=_trim_text(model_output),
                    )

                    # Extract code with block count for feedback
                    code, block_count = extract_code(model_output)
                    telemetry.log(
                        "info",
                        "rlm_code_extract",
                        step_index=step_index,
                        block_count=block_count,
                        code_len=len(code or ""),
                    )

                    stdout = None
                    error = None
                    budget_pct = remaining.percentage_used()
                    feedback = None
                    accepted = False
                    if code:
                        with telemetry.span(
                            "sandbox.exec",
                            step_index=step_index,
                            code_len=len(code),
                        ):
                            result = sandbox.exec(code)
                        stdout = result.stdout
                        error = result.error
                        telemetry.log(
                            "info",
                            "sandbox_result",
                            step_index=step_index,
                            code=_trim_text(code),
                            stdout=_trim_text(stdout),
                            error=_trim_text(error),
                        )
                        # Build structured feedback
                        feedback = build_feedback(stdout, error, code, block_count)
                    else:
                        if self._final_from_output(model_output, sandbox):
                            feedback = StepFeedback()
                        # No code block found
                        if feedback is None:
                            feedback = build_feedback("", "no_code_block", None, 0)

                    if feedback is not None:
                        telemetry.log(
                            "info",
                            "rlm_feedback",
                            step_index=step_index,
                            violation=feedback.violation,
                            hint=feedback.hint,
                            pattern_warnings=feedback.pattern_warnings,
                            rejection_reasons=feedback.rejection_reasons,
                            error=_trim_text(feedback.error),
                            stdout=_trim_text(feedback.stdout),
                        )

                    if sandbox.answer.get("ready"):
                        if self._verify_on_final:
                            verification = self._verify_output(
                                task, sandbox.answer.get("content") or ""
                            )
                            if verification.passed:
                                accepted = True
                            else:
                                sandbox.answer["ready"] = False
                                feedback.rejection_reasons = verification.reasons
                                telemetry.log(
                                    "info",
                                    "rlm_final_reject",
                                    step_index=step_index,
                                    reasons=verification.reasons,
                                )
                        else:
                            accepted = True

                    if feedback is not None:
                        prompt = self._advance_prompt(
                            prompt, model_output, feedback, budget_pct
                        )
                        telemetry.log(
                            "info",
                            "rlm_prompt_next",
                            step_index=step_index,
                            prompt=_trim_text(prompt),
                        )

                    steps.append(
                        RLMStep(
                            step_index=step_index,
                            prompt=prompt,
                            model_output=model_output,
                            code=code,
                            stdout=stdout,
                            error=error,
                        )
                    )
                    if accepted:
                        telemetry.log(
                            "info",
                            "rlm_final_accept",
                            step_index=step_index,
                        )
                        break

            elapsed_seconds = time.time() - start_ts
            budget_usage = self._budget_usage(task, usage_accumulator, elapsed_seconds)
            answer = sandbox.answer.get("content")
            verification = self._verify_output(task, answer or "")
            if not verification.passed:
                errors.extend(
                    [f"verification_failed:{reason}" for reason in verification.reasons]
                )
            telemetry.log(
                "info",
                "rlm_verification",
                passed=verification.passed,
                reasons=verification.reasons,
                answer=_trim_text(answer),
            )
            success = (
                bool(answer)
                and not errors
                and not budget_usage.limits_exceeded
                and verification.passed
            )
            if not answer:
                errors.append("no_answer")
                telemetry.log("info", "rlm_no_answer")

            if context_path:
                try:
                    from enzu.tools.context import ctx_save, ctx_stats
                    after = ctx_stats()
                    if _context_grew(context_before, after):
                        Path(context_path).parent.mkdir(parents=True, exist_ok=True)
                        # Persist only when new sources were added.
                        ctx_save(context_path)
                        telemetry.log(
                            "info",
                            "context_saved",
                            path=str(context_path),
                            stats=after,
                        )
                except Exception:
                    pass
            telemetry.log(
                "info",
                "rlm_run_complete",
                success=success,
                errors=errors,
                budget_used=budget_usage.limits_exceeded,
                answer=_trim_text(answer),
            )
            return RLMExecutionReport(
                success=success,
                task_id=task.task_id,
                provider=provider.name,
                model=task.model,
                answer=answer,
                steps=steps,
                budget_usage=budget_usage,
                errors=errors,
            )

    def _system_prompt(
        self,
        task: TaskSpec,
        *,
        data_len: int,
        context_type: str = "str",
        context_lengths: Optional[List[int]] = None,
        has_search_tools: bool = False,
    ) -> str:
        """Build the system prompt text."""
        chunk_lengths = context_lengths or [data_len]
        base_prompt = (
            "You are tasked with answering a query with associated context. You can access, "
            "transform, and analyze this context interactively in a REPL environment that can "
            "recursively query sub-LLMs, which you are strongly encouraged to use as much as "
            "possible. You will be queried iteratively until you provide a final answer.\n\n"
            f"Your context is a {context_type} with {data_len} total characters, and is broken "
            f"up into chunks of char lengths: {chunk_lengths}.\n\n"
            "The REPL environment is initialized with:\n"
            "1. A 'context' variable containing all information related to the query.\n"
            "2. 'llm_query(prompt)' - query a sub-LLM (has tools: search, research, etc.).\n"
            "3. 'llm_batch(prompts)' - parallel sub-LLM queries (faster for multiple items).\n"
            "4. 'print()' to debug and observe outputs (truncated).\n\n"
            "Sub-LLMs have access to tools you don't. Delegate tasks requiring external "
            "information (search, research, web content) to them via llm_query/llm_batch.\n\n"
            "Make sure to explicitly look through the entire context. The context contains the "
            "answer to the query, so it is important that you parse it carefully and "
            "completely.\n\n"
            "You can use the REPL environment for as many iterations as you need to answer the "
            "query. In the REPL environment, you should primarily do computation. Write out the "
            "final answer when you are ready. You are not required to use the REPL environment "
            "if it is not helpful.\n\n"
            "When you want to execute Python code, you should wrap it in a block of triple "
            "backticks with the python language specifier (```repl```). For example:\n\n"
            "```repl\n"
            "# Example: delegate search to sub-LLM\n"
            "result = llm_query('Search for recent news about AI agents and summarize')\n"
            "print(result)\n"
            "```\n\n"
            "IMPORTANT: When you are done, call FINAL with your final output.\n"
            "Example: FINAL(\"my final answer\")\n\n"
            "Think step by step and use the REPL environment to do the necessary work."
        )
        # Optional tool guidance from callers (e.g., automode filesystem tools).
        tools_guidance = task.metadata.get("tools_guidance") or ""
        # Show criteria early so the model aims for the stop condition.
        criteria_text = _format_success_criteria(task.success_criteria)
        prompt = self._model_prompt_extra(task.model) + base_prompt + criteria_text
        if self._prompt_style == "extended":
            # Extended prompt adds local guardrails and tool guidance.
            suppress_probe = bool(task.metadata.get("suppress_probe_guidance"))

            def strip_probe(text: str) -> str:
                # Remove probe hints when caller provides an explicit REPL workflow.
                lines = [line for line in text.splitlines() if "Probe:" not in line]
                return "\n".join(lines)

            guardrails = SYSTEM_PROMPT_GUARDRAILS
            strategy = STRATEGY_HINTS if data_len >= 10000 else ""
            search_guidance = SEARCH_TOOLS_GUIDANCE if has_search_tools else ""
            if suppress_probe:
                guardrails = strip_probe(guardrails)
                strategy = strip_probe(strategy)
                search_guidance = strip_probe(search_guidance)
            pip_guidance = PIP_INSTALL_GUIDANCE if self._enable_pip else ""
            prompt = (
                prompt
                + guardrails
                + search_guidance
                + pip_guidance
                + strategy
                + tools_guidance
            )
        elif tools_guidance:
            prompt = prompt + tools_guidance
        # Query stays in the REPL context per the paper.
        return prompt

    @staticmethod
    def _model_prompt_extra(model_name: str) -> str:
        model_key = model_name.lower()
        model_prompt_extras = {
            "qwen": (
                "IMPORTANT: Be very careful about using llm_query too many times. "
                "There is a cost to each call. Aim for around ~200k characters in each "
                "llm_query call. Thus, you should batch/aggregate information at each "
                "step and only make a small number of llm_query calls.\n\n"
            ),
            "gpt": "",
        }
        for prefix, extra in model_prompt_extras.items():
            if model_key.startswith(prefix):
                return extra
        return ""
    def _advance_prompt(
        self,
        prompt: str,
        model_output: str,
        feedback: StepFeedback,
        budget_pct: Optional[Dict[str, int]] = None,
    ) -> str:
        """Build next prompt with structured feedback and budget awareness."""
        feedback_text = format_feedback(feedback)

        # Build budget awareness line
        budget_line = ""
        if budget_pct:
            max_pct = max(budget_pct.values()) if budget_pct else 0
            budget_line = f"Budget used: {max_pct}%"
            if max_pct >= 80:
                budget_line += " - WRAP UP SOON"
            elif max_pct >= 50:
                budget_line += " - be efficient"
            budget_line += "\n"

        next_prompt = (
            f"{prompt}\n"
            "---\n"
            f"{budget_line}"
            "Model output:\n"
            f"{model_output}\n"
            "---\n"
            f"{feedback_text}\n"
            "---\n"
            "Write another ```repl``` block or call FINAL()/FINAL_VAR().\n"
        )
        return next_prompt

    def _final_from_output(self, model_output: str, sandbox: PythonSandbox) -> bool:
        match = re.search(r"FINAL\((.*?)\)", model_output, re.DOTALL)
        if match:
            content = match.group(1).strip()
            content = content.strip('"').strip("'")
            sandbox.answer["content"] = content
            sandbox.answer["ready"] = True
            return True
        match = re.search(r"FINAL_VAR\((.*?)\)", model_output, re.DOTALL)
        if match:
            var_name = match.group(1).strip()
            sandbox.answer["content"] = str(sandbox.get_global(var_name))
            sandbox.answer["ready"] = True
            return True
        return False

    @staticmethod
    def _accumulate_usage(accumulator: dict, usage: dict) -> None:
        output_tokens = _read_usage_int(usage, ("output_tokens", "completion_tokens"))
        total_tokens = _read_usage_int(usage, ("total_tokens",))
        cost_usd = usage.get("cost_usd")
        if isinstance(output_tokens, int):
            accumulator["output_tokens"] += output_tokens
        if isinstance(total_tokens, int):
            accumulator["total_tokens"] += total_tokens
        if isinstance(cost_usd, (int, float)):
            accumulator["cost_usd"] = accumulator.get("cost_usd", 0.0) + float(cost_usd)

    def _budget_exceeded(self, task: TaskSpec, start_ts: float, usage: dict) -> bool:
        elapsed = time.time() - start_ts
        output_tokens = _read_usage_int(usage, ("output_tokens", "completion_tokens"))
        total_tokens = _read_usage_int(usage, ("total_tokens",))
        if task.budget.max_seconds and elapsed > task.budget.max_seconds:
            return True
        if task.budget.max_output_tokens and output_tokens is not None:
            if output_tokens > task.budget.max_output_tokens:
                return True
        if task.budget.max_total_tokens and total_tokens is not None:
            if total_tokens > task.budget.max_total_tokens:
                return True
        return False

    def _budget_usage(
        self, task: TaskSpec, usage: dict, elapsed_seconds: float
    ) -> BudgetUsage:
        output_tokens = _read_usage_int(usage, ("output_tokens", "completion_tokens"))
        total_tokens = _read_usage_int(usage, ("total_tokens",))
        limits_exceeded = []
        if task.budget.max_seconds and elapsed_seconds > task.budget.max_seconds:
            limits_exceeded.append("max_seconds")
        if task.budget.max_output_tokens and output_tokens is not None:
            if output_tokens > task.budget.max_output_tokens:
                limits_exceeded.append("max_output_tokens")
        if task.budget.max_total_tokens and total_tokens is not None:
            if total_tokens > task.budget.max_total_tokens:
                limits_exceeded.append("max_total_tokens")
        return BudgetUsage(
            elapsed_seconds=elapsed_seconds,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=usage.get("cost_usd"),
            limits_exceeded=limits_exceeded,
        )

    @staticmethod
    def _verify_output(task: TaskSpec, output_text: str) -> VerificationResult:
        """
        Verify output against success criteria.

        Two modes:
        1. Goal-based: model's FINAL() call is the verification. If output exists,
           model judged itself complete. Pass without mechanical checks.
        2. Mechanical: check required_substrings, required_regex, min_word_count.
        """
        reasons: list[str] = []
        passed = True

        # Goal-based: model self-judges. FINAL() with output = success.
        # The model knows when it achieved the goal. Trust it.
        if task.success_criteria.goal:
            if not output_text:
                return VerificationResult(passed=False, reasons=["no_output"])
            # Model called FINAL() with content = goal achieved.
            return VerificationResult(passed=True, reasons=[])

        # Mechanical verification: predefined checks.
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


def _context_grew(
    before: Optional[Dict[str, Any]],
    after: Dict[str, Any],
) -> bool:
    """Return True when context store gained sources or text."""
    if not before:
        return (
            after.get("num_sources", 0) > 0
            or after.get("num_queries", 0) > 0
            or after.get("total_text_chars", 0) > 0
        )
    return (
        after.get("num_sources", 0) > before.get("num_sources", 0)
        or after.get("num_queries", 0) > before.get("num_queries", 0)
        or after.get("total_text_chars", 0) > before.get("total_text_chars", 0)
    )


class _BudgetTracker:
    def __init__(self, budget: Any) -> None:
        self._budget = budget
        self._output_tokens = 0
        self._total_tokens = 0
        self._cost_usd = 0.0

    def consume(self, usage: dict) -> None:
        output_tokens = _read_usage_int(usage, ("output_tokens", "completion_tokens"))
        total_tokens = _read_usage_int(usage, ("total_tokens",))
        cost_usd = usage.get("cost_usd")
        if isinstance(output_tokens, int):
            self._output_tokens += output_tokens
        if isinstance(total_tokens, int):
            self._total_tokens += total_tokens
        if isinstance(cost_usd, (int, float)):
            self._cost_usd += float(cost_usd)

    def is_exhausted(self) -> bool:
        if (
            self._budget.max_output_tokens
            and self._output_tokens >= self._budget.max_output_tokens
        ):
            return True
        if (
            self._budget.max_total_tokens
            and self._total_tokens >= self._budget.max_total_tokens
        ):
            return True
        if self._budget.max_cost_usd and self._cost_usd >= self._budget.max_cost_usd:
            return True
        return False

    def percentage_used(self) -> Dict[str, int]:
        """Return percentage used for each budget dimension."""
        pct: Dict[str, int] = {}
        if self._budget.max_output_tokens:
            pct["output_tokens"] = round(
                100 * self._output_tokens / self._budget.max_output_tokens
            )
        if self._budget.max_total_tokens:
            pct["total_tokens"] = round(
                100 * self._total_tokens / self._budget.max_total_tokens
            )
        if self._budget.max_cost_usd:
            pct["cost_usd"] = round(100 * self._cost_usd / self._budget.max_cost_usd)
        return pct
