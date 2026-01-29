from enzu.api import generate, resolve_provider, run
from enzu.engine import Engine
from enzu.session import Session, SessionBudgetExceeded
from enzu.contract import (
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MIN_WORD_COUNT,
    apply_task_defaults,
    has_budget_limit,
    has_success_check,
    task_spec_from_payload,
)
from enzu.models import (
    Budget,
    BudgetUsage,
    Check,
    ExecutionReport,
    Limits,
    ProgressEvent,
    ProviderResult,
    RLMExecutionReport,
    RLMStep,
    SuccessCriteria,
    TaskSpec,
    TrajectoryStep,
    VerificationResult,
)
from enzu.providers.base import BaseProvider
from enzu.providers.openai_compat import OpenAICompatProvider
from enzu.providers.registry import list_providers, register_provider
from enzu.rlm import RLMEngine
from enzu.schema import (
    report_schema,
    run_payload_schema,
    schema_bundle,
    task_input_schema,
    task_spec_schema,
)

# Optional: search tools (require EXA_API_KEY)
try:
    from enzu.tools.exa import (
        ExaClient,
        exa_search,
        exa_news,
        exa_papers,
        exa_contents,
        exa_similar,
    )
    _HAS_SEARCH = True
except (ImportError, ValueError):
    _HAS_SEARCH = False

__all__ = [
    "run",
    "resolve_provider",
    "Session",
    "SessionBudgetExceeded",
    "Limits",
    "Check",
    "BaseProvider",
    "Budget",
    "BudgetUsage",
    "DEFAULT_MAX_OUTPUT_TOKENS",
    "DEFAULT_MIN_WORD_COUNT",
    "Engine",
    "ExecutionReport",
    "generate",
    "OpenAICompatProvider",
    "list_providers",
    "register_provider",
    "ProgressEvent",
    "ProviderResult",
    "RLMEngine",
    "RLMExecutionReport",
    "RLMStep",
    "apply_task_defaults",
    "has_budget_limit",
    "has_success_check",
    "SuccessCriteria",
    "TaskSpec",
    "task_spec_from_payload",
    "TrajectoryStep",
    "VerificationResult",
    "report_schema",
    "run_payload_schema",
    "schema_bundle",
    "task_input_schema",
    "task_spec_schema",
]

# Add search tools to exports if available
if _HAS_SEARCH:
    __all__.extend([
        "ExaClient",
        "exa_search",
        "exa_news",
        "exa_papers",
        "exa_contents",
        "exa_similar",
    ])
