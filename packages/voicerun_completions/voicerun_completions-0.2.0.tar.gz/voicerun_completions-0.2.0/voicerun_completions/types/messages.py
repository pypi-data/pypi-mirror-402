import json
from typing import Any, List, Literal, Optional, Required, TypeAlias, TypedDict, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .cache import CacheBreakpoint, CacheBreakpointDict


class FunctionCallDict(TypedDict):
    """TypedDict for function call."""
    name: str
    arguments: dict[str, Any]


@dataclass
class FunctionCall:
    """Normalized function call representation across all LLM providers.

    Attributes:
        arguments: Dictionary of arguments passed to the function
        name: Name of the function to call
    """
    arguments: dict[str, Any]
    name: str

    def __str__(self) -> str:
        return json.dumps(self.serialize())

    def serialize(self) -> dict[str, Any]:
        """Serialize function call to dict representation."""
        return {"name": self.name, "arguments": self.arguments}

    @classmethod
    def deserialize(cls, data: dict) -> "FunctionCall":
        return cls(
            arguments=data["arguments"],
            name=data["name"],
        )


class ToolCallDict(TypedDict, total=False):
    """TypedDict for tool call."""
    id: Required[str]
    type: Required[Literal["function"]]
    function: Required[FunctionCallDict]
    index: int
    thought_signature: str  # base64 encoded


@dataclass
class ToolCall:
    """Normalized tool call representation across all LLM providers.

    Attributes:
        id: Unique identifier for this tool call
        type: Type of tool call (always "function")
        function: Function call details including name and arguments
        index: Optional index for ordering multiple tool calls
        thought_signature: Optional Google Gemini-specific field for maintaining context across turns
    """
    id: str
    type: Literal["function"]
    function: FunctionCall
    index: Optional[int] = None
    thought_signature: Optional[bytes] = None

    def __str__(self) -> str:
        return json.dumps(self.serialize())

    def serialize(self) -> dict[str, Any]:
        """Serialize tool call to dict representation."""
        result = {
            "id": self.id,
            "type": self.type,
            "function": self.function.serialize(),
        }
        if self.index is not None:
            result["index"] = self.index
        if self.thought_signature is not None:
            # Store as base64 string for JSON serialization
            import base64
            result["thought_signature"] = base64.b64encode(self.thought_signature).decode('utf-8')
        return result

    @classmethod
    def deserialize(cls, data: dict) -> "ToolCall":
        thought_signature = None
        if data.get("thought_signature"):
            import base64
            thought_signature = base64.b64decode(data["thought_signature"])
        return cls(
            id=data["id"],
            type=data["type"],
            function=FunctionCall.deserialize(data["function"]),
            index=data.get("index"),
            thought_signature=thought_signature
        )


class ConversationHistoryMessage(ABC):
    """Abstract base class for normalized conversation messages across all LLM providers.

    This class provides a common interface for different types of conversation messages
    (user, assistant, system, tool) with methods for serialization and deserialization.
    """

    @property
    @abstractmethod
    def role(self) -> str:
        """Message role."""
        pass

    @abstractmethod
    def serialize(self) -> dict[str, Any]:
        """Serialize message to dict representation."""
        pass

    def __str__(self) -> str:
        """Serialize message to string representation."""
        return json.dumps(self.serialize())

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "ConversationHistoryMessage":
        """Factory method to deserialize dict representation into appropriate message subclass based on role."""
        role = data.get("role")

        # Mapping of roles to their corresponding classes
        message_classes = {
            "user": UserMessage,
            "assistant": AssistantMessage,
            "system": SystemMessage,
            "tool": ToolResultMessage,
        }

        if role not in message_classes:
            raise ValueError(f"Unknown message role: {role}")

        message_class: type[ConversationHistoryMessage] = message_classes[role]
        return message_class.deserialize(data)


class UserMessageDict(TypedDict, total=False):
    """TypedDict for user message."""
    role: Required[Literal["user"]]
    content: Required[str]
    cache_breakpoint: CacheBreakpointDict


@dataclass
class UserMessage(ConversationHistoryMessage):
    """A user message.

    Attributes:
        content: Message content from the user
        cache_breakpoint: Optional Anthropic cache breakpoint for prompt caching optimization
    """
    content: str
    cache_breakpoint: Optional[CacheBreakpoint] = None

    @property
    def role(self) -> str:
        return "user"

    def serialize(self) -> dict[str, Any]:
        result: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.cache_breakpoint:
            result["cache_breakpoint"] = self.cache_breakpoint.serialize()
        return result

    @classmethod
    def deserialize(cls, data: dict) -> "UserMessage":
        """Deserialize user message from dict representation."""
        cache_breakpoint = None
        if data.get("cache_breakpoint"):
            cache_breakpoint = CacheBreakpoint.deserialize(data.get("cache_breakpoint"))
        return cls(
            content=data["content"],
            cache_breakpoint=cache_breakpoint,
        )


class AssistantMessageDict(TypedDict, total=False):
    """TypedDict for assistant message."""
    role: Required[Literal["assistant"]]
    content: str
    tool_calls: list[ToolCallDict]
    cache_breakpoint: CacheBreakpointDict
    thought_signature: str  # base64 encoded


@dataclass
class AssistantMessage(ConversationHistoryMessage):
    """An assistant message.

    Attributes:
        content: Assistant response string message
        tool_calls: Tool(s) the assistant called
        cache_breakpoint: Optional Anthropic cache breakpoint for prompt caching optimization
        thought_signature: Optional Google Gemini-specific field for text-only responses (non-function-call)
    """
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    cache_breakpoint: Optional[CacheBreakpoint] = None
    thought_signature: Optional[bytes] = None

    @property
    def role(self) -> str:
        return "assistant"

    def serialize(self) -> dict[str, Any]:
        result = {"role": self.role, "content": self.content}
        if self.tool_calls:
            result["tool_calls"] = [tc.serialize() for tc in self.tool_calls]
        if self.cache_breakpoint:
            result["cache_breakpoint"] = self.cache_breakpoint.serialize()
        if self.thought_signature is not None:
            # Store as base64 string for JSON serialization
            import base64
            result["thought_signature"] = base64.b64encode(self.thought_signature).decode('utf-8')
        return result

    @classmethod
    def deserialize(cls, data: dict) -> "AssistantMessage":
        """Deserialize assistant message from dict representation."""
        tool_calls = data.get("tool_calls")
        normalized_tool_calls = None
        if tool_calls:
            normalized_tool_calls = [ToolCall.deserialize(tc) for tc in tool_calls]
        cache_breakpoint = None
        if data.get("cache_breakpoint"):
            cache_breakpoint = CacheBreakpoint.deserialize(data.get("cache_breakpoint"))
        thought_signature = None
        if data.get("thought_signature"):
            import base64
            thought_signature = base64.b64decode(data["thought_signature"])

        return cls(
            content=data.get("content"),
            tool_calls=normalized_tool_calls,
            cache_breakpoint=cache_breakpoint,
            thought_signature=thought_signature,
        )


class SystemMessageDict(TypedDict, total=False):
    """TypedDict for system message."""
    role: Required[Literal["system"]]
    content: Required[str]
    cache_breakpoint: CacheBreakpointDict


@dataclass
class SystemMessage(ConversationHistoryMessage):
    """A system prompt message. For anthropic and google providers all SystemMessages in the
    ConversationHistory will be collapsed into a single system prompt.

    Attributes:
        content: System instruction or prompt content
        cache_breakpoint: Optional Anthropic cache breakpoint for prompt caching optimization
    """
    content: str
    cache_breakpoint: Optional[CacheBreakpoint] = None

    @property
    def role(self) -> str:
        return "system"

    def serialize(self) -> dict[str, Any]:
        result = {"role": self.role, "content": self.content}
        if self.cache_breakpoint:
            result["cache_breakpoint"] = self.cache_breakpoint.serialize()
        return result

    @classmethod
    def deserialize(cls, data: dict) -> "SystemMessage":
        """Deserialize system message from dict representation."""
        cache_breakpoint = None
        if data.get("cache_breakpoint"):
            cache_breakpoint = CacheBreakpoint.deserialize(data.get("cache_breakpoint"))
        return cls(
            content=data["content"],
            cache_breakpoint=cache_breakpoint,
        )


class ToolResultMessageDict(TypedDict, total=False):
    """TypedDict for tool result message."""
    role: Required[Literal["tool"]]
    tool_call_id: Required[str]
    content: Required[dict[str, Any]]
    name: str
    cache_breakpoint: CacheBreakpointDict


@dataclass
class ToolResultMessage(ConversationHistoryMessage):
    """A tool result message.

    Attributes:
        tool_call_id: Id of the tool call which this is a result of
        content: Result JSON payload of the tool call
        name: Name of the function which this is a result of
        cache_breakpoint: Optional Anthropic cache breakpoint for prompt caching optimization
    """
    tool_call_id: str
    content: dict[str, Any]
    name: Optional[str] = None
    cache_breakpoint: Optional[CacheBreakpoint] = None

    @property
    def role(self) -> str:
        return "tool"

    def serialize(self) -> dict[str, Any]:
        result = {
            "role": self.role,
            "tool_call_id": self.tool_call_id,
            "content": self.content,
        }
        if self.name is not None:
            result["name"] = self.name
        if self.cache_breakpoint:
            result["cache_breakpoint"] = self.cache_breakpoint.serialize()
        return result

    @classmethod
    def deserialize(cls, data: dict) -> "ToolResultMessage":
        """Deserialize tool result message from dict representation."""
        cache_breakpoint = None
        if data.get("cache_breakpoint"):
            cache_breakpoint = CacheBreakpoint.deserialize(data.get("cache_breakpoint"))
        return cls(
            tool_call_id=data["tool_call_id"],
            content=data["content"],
            name=data.get("name"),
            cache_breakpoint=cache_breakpoint,
        )


ConversationHistoryMessageDict = Union[
    UserMessageDict,
    AssistantMessageDict,
    SystemMessageDict,
    ToolResultMessageDict,
]

ConversationHistory: TypeAlias = list[ConversationHistoryMessage]
ConversationHistoryDict: TypeAlias = list[ConversationHistoryMessageDict]


def serialize_conversation(conversation: ConversationHistory) -> list[dict[str, Any]]:
    """Serialize conversation history into array of dicts."""
    serialized_conversation: list[dict[str, Any]] = []
    for msg in conversation:
        serialized_conversation.append(msg.serialize())
    return serialized_conversation


def deserialize_conversation(serialized_conversation: list[dict[str, Any]]) -> ConversationHistory:
    """Deserialize conversation history from array of dicts."""
    conversation: ConversationHistory = []
    for msg in serialized_conversation:
        conversation.append(ConversationHistoryMessage.deserialize(msg))
    return conversation
