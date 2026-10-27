"""Shared contracts package for NeuralCFO + Moonshot Mode."""
from packages.contracts.envelope import ErrorDetail, ErrorEnvelope, ToolResultEnvelope
from packages.contracts.finance import (
    CaseResult,
    ExplainChangeData,
    FakeFinanceService,
    FinanceService,
    MetricRequest,
    MetricResponseData,
    ScenarioChange,
    ScenarioDefinition,
    ScenarioRunRequest,
    ScenarioRunResponseData,
    SourceRowData,
    WeeklyCashPoint,
)
from packages.contracts.moonshot import (
    ClarificationOption,
    ClarificationQuestion,
    FakeMoonshotWorkflow,
    MoonshotReport,
    MoonshotWorkflow,
    NeedsInputResult,
    RankedStrategy,
    StageEvent,
)
from packages.contracts.evidence import (
    Claim,
    ClaimTag,
    EvidenceLink,
    EvidenceResolution,
    EvidenceResolver,
    EvidenceTargetType,
)
from packages.contracts.llm import (
    FakeLLMProvider,
    LLMProvider,
    LLMResponse,
    LLMStreamChunk,
    Message,
    ToolCall,
    ToolDefinition,
)
from packages.contracts.embeddings import EmbeddingProvider, FakeEmbeddingProvider
from packages.contracts.stt import FakeSttProvider, SttProvider, SttResult
from packages.contracts.search import FakeSearchProvider, SearchProvider, SearchResult
from packages.contracts.memory import FakeMemoryStore, MemoryItem, MemoryStore, MemoryTrace
