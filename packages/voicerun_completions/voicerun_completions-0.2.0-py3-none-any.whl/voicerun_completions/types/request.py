from typing import Any, Dict, List, Literal, Optional, Required, TypeAlias, TypedDict, Union
from enum import StrEnum
from dataclasses import dataclass

from .messages import ConversationHistory, ConversationHistoryDict, ConversationHistoryMessage
from .cache import CacheBreakpoint, CacheBreakpointDict


def coalesce(a, b):
    """Return a if a is not None, otherwise return b."""
    return a if a is not None else b


class CompletionsProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    VERTEX_ANTHROPIC = "vertex_anthropic"


class FunctionDefinitionDict(TypedDict, total=False):
    """TypedDict for `FunctionDefinition`."""
    name: Required[str]
    description: Required[str]
    parameters: Required[Dict[str, Any]]
    strict: bool


@dataclass
class FunctionDefinition:
    """Function definition for tool calling.

    Attributes:
        name: Name of the function
        description: Description of what the function does
        parameters: JSON schema describing the function's parameters
        strict: Whether to enable strict mode for parameter validation (OpenAI only)
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    strict: Optional[bool] = None

    @classmethod
    def deserialize(cls, data: dict) -> "FunctionDefinition":
        """Deserialize function definition from dictionary representation."""
        return cls(
            name=data["name"],
            description=data["description"],
            parameters=data["parameters"],
            strict=data.get("strict", None),
        )


class ToolDefinitionDict(TypedDict, total=False):
    """TypedDict for `ToolDefinition`."""
    type: Required[Literal["function"]]
    function: Required[FunctionDefinitionDict]
    cache_breakpoint: CacheBreakpointDict


@dataclass
class ToolDefinition:
    """Tool definition for LLM tool calling.

    Attributes:
        type: Type of tool (always "function")
        function: Function definition containing name, description, and parameters
        cache_breakpoint: Optional Anthropic cache breakpoint for prompt caching optimization
    """
    type: Literal["function"]
    function: FunctionDefinition
    cache_breakpoint: Optional[CacheBreakpoint] = None

    @classmethod
    def deserialize(cls, data: dict) -> "ToolDefinition":
        """Deserialize tool definition from dictionary representation."""
        cache_breakpoint = None
        if data.get("cache_breakpoint"):
            cache_breakpoint = CacheBreakpoint.deserialize(data.get("cache_breakpoint"))
        return cls(
            type=data["type"],
            function=FunctionDefinition.deserialize(data["function"]),
            cache_breakpoint=cache_breakpoint,
        )


ToolChoice: TypeAlias = Union[Literal["none", "auto", "required"], str]


def _normalize_provider(provider: Union[str, CompletionsProvider]) -> CompletionsProvider:
    """Convert potential string provider into CompletionsProvider."""
    if isinstance(provider, CompletionsProvider):
        return provider
    if isinstance(provider, str):
        try:
            return CompletionsProvider(provider.lower())
        except ValueError:
            raise ValueError(f"Invalid provider: {provider}.")


def _normalize_messages(messages: list[Union[dict, ConversationHistoryMessage]]) -> ConversationHistory:
    """Convert list of dicts or message objects to normalized ConversationHistoryMessage objects."""
    normalized_messages: ConversationHistory = []

    for msg in messages:
        if isinstance(msg, ConversationHistoryMessage):
            normalized_messages.append(msg)
        elif isinstance(msg, dict):
            normalized_messages.append(ConversationHistoryMessage.deserialize(msg))
        else:
            raise TypeError(f"Messages must be dict or ConversationHistoryMessage, got {type(msg)}")

    return normalized_messages


def _normalize_tools(tools: Optional[list[Union[dict, ToolDefinition]]]) -> Optional[list[ToolDefinition]]:
    """Convert list of dicts or tool def objects to list of normalized ToolDefinitions."""
    if not tools:
        return None

    normalized_tools: list[ToolDefinition] = []
    for tool in tools:
        if isinstance(tool, ToolDefinition):
            normalized_tools.append(tool)
        elif isinstance(tool, dict):
            normalized_tools.append(ToolDefinition.deserialize(tool))
        else:
            raise TypeError(f"Tools must be dict or ToolDefinition, got {type(tool)}")

    return normalized_tools


class StreamOptionsDict(TypedDict, total=False):
    """TypedDict for `StreamOptions`."""
    stream_sentences: bool = False
    clean_sentences: bool = True
    min_sentence_length: int = 6
    punctuation_marks: Optional[list[str]] = None
    punctuation_language: Optional[str] = None


@dataclass
class StreamOptions:
    """Options for configuring streaming behavior.

    Attributes:
        stream_sentences: Whether to stream response by sentences instead of tokens
        clean_sentences: Whether to clean markdown and special characters from sentences for speech
            Only applicable if stream_sentences = True
            Defaults to True
        min_sentence_length: Minimum length (in characters) for a sentence to be yielded
            Only applicable if stream_sentences = True
            Defaults to 6 characters
        punctuation_marks: Optional set of punctuation marks to use for sentence boundaries
            Only applicable if stream_sentences = True
            Defaults to comprehensive set covering most languages
        punctuation_language: Optional language code to use language-specific punctuation
            Only applicable if stream_sentences = True
            Supported: 'en', 'zh', 'ko', 'ja', 'es', 'fr', 'it', 'de'
    """
    stream_sentences: bool = False
    clean_sentences: bool = True
    min_sentence_length: int = 6
    punctuation_marks: Optional[list[str]] = None
    punctuation_language: Optional[str] = None


class RetryConfigurationDict(TypedDict, total=False):
    """TypedDict for `RetryConfiguration`."""
    enabled: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_multiplier: float = 2.0


@dataclass
class RetryConfiguration:
    """ChatCompletionRequest retry configuration.

    Attributes:
        enabled: Enable retry (default: True)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 1.0)
        backoff_multiplier: Multiplier for exponential backoff (default: 2.0)

    Note:
        Retry logic follows OpenAI's recommended exponential backoff pattern.
    """
    enabled: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_multiplier: float = 2.0


def _normalize_retry(retry: Optional[Union[RetryConfiguration, dict]]) -> Optional[RetryConfiguration]:
    """Convert dict to RetryConfiguration if needed."""
    if retry is None:
        return None
    if isinstance(retry, RetryConfiguration):
        return retry
    if isinstance(retry, dict):
        return RetryConfiguration(**retry)
    raise TypeError(f"Retry must be dict or RetryConfiguration, got {type(retry)}")


class FallbackRequestDict(TypedDict, total=False):
    """TypedDict for `FallbackRequest`."""
    provider: CompletionsProvider
    api_key: str
    model: str
    messages: Union[ConversationHistory, ConversationHistoryDict]
    temperature: float
    tools: list[Union[ToolDefinition, ToolDefinitionDict]]
    tool_choice: ToolChoice
    timeout: float
    max_tokens: int
    retry: Union[RetryConfiguration, RetryConfigurationDict]
    vendor_kwargs: Dict[str, Any]


@dataclass
class FallbackRequest:
    """Chat completion fallback request. Any parameters supplied in this request will override
    the original request parameters in the fallback completion request. Parameters not supplied
    in this fallback request will default to the parameters from the original completion request.

    Attributes:
        provider: LLM provider to use (OpenAI, Anthropic, or Google)
        api_key: API key for authentication with the provider
        model: Model name to use for completion
        messages: Conversation history as a list of messages
        temperature: Sampling temperature for response randomness (0.0 to 1.0)
        tools: Optional list of tool definitions for function calling
        tool_choice: How the model should choose which tools to call
        timeout: Request timeout in seconds
        max_tokens: Maximum number of tokens in the response
        retry: Options for configuring retry behavior
        vendor_kwargs: Optional dictionary of vendor-specific keyword arguments
            (e.g., {"service_tier": "priority"} for OpenAI)
    """
    provider: Optional[CompletionsProvider] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    messages: Optional[ConversationHistory] = None
    temperature: Optional[float] = None
    tools: Optional[list[ToolDefinition]] = None
    tool_choice: Optional[ToolChoice] = None
    timeout: Optional[float] = None
    max_tokens: Optional[int] = None
    retry: Optional[RetryConfiguration] = None
    vendor_kwargs: Optional[Dict[str, Any]] = None


class ChatCompletionRequestDict(TypedDict, total=False):
    """TypedDict for `ChatCompletionRequest`."""
    provider: Required[Union[str, CompletionsProvider]]
    api_key: Required[str]
    model: Required[str]
    messages: Required[Union[ConversationHistory, ConversationHistoryDict]]
    temperature: float
    tools: list[ToolDefinition]
    tool_choice: ToolChoice
    timeout: float
    max_tokens: int
    retry: Union[RetryConfiguration, RetryConfigurationDict]
    fallbacks: List[Union[FallbackRequest, FallbackRequestDict]]
    vendor_kwargs: Dict[str, Any]


@dataclass
class ChatCompletionRequest:
    """Normalized chat completion request for any LLM provider.

    Attributes:
        provider: LLM provider to use (OpenAI, Anthropic, or Google)
        api_key: API key for authentication with the provider
        model: Model name to use for completion
        messages: Conversation history as a list of messages
        temperature: Sampling temperature for response randomness (0.0 to 1.0)
        tools: Optional list of tool definitions for function calling
        tool_choice: How the model should choose which tools to call
        timeout: Request timeout in seconds
        max_tokens: Maximum number of tokens in the response
        retry: Options for configuring retry behavior
        fallbacks: Ordered list of fallback requests
        vendor_kwargs: Optional dictionary of vendor-specific keyword arguments
            (e.g., {"service_tier": "priority"} for OpenAI)
    """
    provider: CompletionsProvider
    api_key: str
    model: str
    messages: ConversationHistory
    temperature: Optional[float] = None
    tools: Optional[list[ToolDefinition]] = None
    tool_choice: Optional[ToolChoice] = None
    timeout: Optional[float] = None
    max_tokens: Optional[int] = None
    retry: Optional[RetryConfiguration] = None
    fallbacks: Optional[List[FallbackRequest]] = None
    vendor_kwargs: Optional[Dict[str, Any]] = None

    def _apply_fallback(self, fallback: FallbackRequest) -> "ChatCompletionRequest":
        """Create a new ChatCompletionRequest with parameters overridden by the fallback.

        Non-None values from the FallbackRequest will override the corresponding
        fields in the original request. Fields not present in FallbackRequest
        or set to None will retain their original values.

        Args:
            fallback: FallbackRequest containing override parameters

        Returns:
            A new ChatCompletionRequest with merged parameters
        """
        if isinstance(fallback, dict):
            fallback = FallbackRequest(**fallback)
        return ChatCompletionRequest(
            provider=coalesce(fallback.provider, self.provider),
            api_key=coalesce(fallback.api_key, self.api_key),
            model=coalesce(fallback.model, self.model),
            messages=coalesce(fallback.messages, self.messages),
            temperature=coalesce(fallback.temperature, self.temperature),
            tools=coalesce(fallback.tools, self.tools),
            tool_choice=coalesce(fallback.tool_choice, self.tool_choice),
            timeout=coalesce(fallback.timeout, self.timeout),
            max_tokens=coalesce(fallback.max_tokens, self.max_tokens),
            retry=coalesce(fallback.retry, self.retry),
            # Do not carry forward the fallback chain
            fallbacks=None,
            vendor_kwargs=coalesce(fallback.vendor_kwargs, self.vendor_kwargs),
        )

    def _normalize(self) -> "ChatCompletionRequest":
        """Normalize request fields in place.

        Returns:
            Self for method chaining
        """
        self.provider = _normalize_provider(self.provider)
        self.messages = _normalize_messages(self.messages)
        self.tools = _normalize_tools(self.tools)
        self.retry = _normalize_retry(self.retry)
        return self

    def _build_completion_attempts(self) -> List["ChatCompletionRequest"]:
        """Build list of completion attempts including fallbacks.

        Returns the original request (normalized) followed by any fallback
        variants, each normalized and ready for execution.

        Returns:
            List of normalized ChatCompletionRequests to attempt in order
        """
        attempts = [self._normalize()]
        if self.fallbacks:
            for fallback in self.fallbacks:
                attempts.append(self._apply_fallback(fallback)._normalize())
        return attempts
