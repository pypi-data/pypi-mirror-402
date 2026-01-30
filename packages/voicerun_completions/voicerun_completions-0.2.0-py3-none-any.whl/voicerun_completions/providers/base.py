import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterable, Optional

from ..types.streaming import ChatCompletionChunk
from ..types.response import ChatCompletionResponse
from ..types.request import ChatCompletionRequest, StreamOptions
from ..types.messages import ToolCall, FunctionCall
from ..retry import retry_with_backoff


@dataclass
class PartialToolCall:
    """Internal state for accumulating tool call data."""
    id: str
    type: str
    function_name: str
    arguments_buffer: str = ""
    index: Optional[int] = None

    def is_complete(self) -> bool:
        """Check if the accumulated arguments form valid JSON."""
        # TODO: better way of doing this?
        try:
            json.loads(self.arguments_buffer)
            return True
        except json.JSONDecodeError:
            return False
        
    def to_tool_call(self) -> ToolCall:
        """Convert this partial to ToolCall. Empty arguments if invalid json."""

        arguments = {}
        try:
            arguments = json.loads(self.arguments_buffer)
        except:
            # Received invalid json arguments
            pass

        return ToolCall(
            id=self.id,
            type=self.type,
            function=FunctionCall(
                name=self.function_name,
                arguments=arguments,
            ),
            index=self.index,
        )


class StreamProcessor(ABC):
    """Processes LLM provider specific completion stream and returns ChatCompletionChunks to yield to client.
    Accumulates streaming tool call deltas and emits complete tool calls.
    """

    @abstractmethod
    async def process_stream(
        self,
        stream: AsyncIterable[Any]
    ) -> AsyncIterable[ChatCompletionChunk]:
        """Process a stream of provider completion chunks and yield normalized chunks."""
        pass


class CompletionClient(ABC):
    """Abstract base class for LLM completion clients."""

    @abstractmethod
    def _denormalize_request(
        self,
        request: ChatCompletionRequest,
    ) -> dict[str, Any]:
        pass


    @abstractmethod
    def _normalize_response(
        self,
        response: Any,
    ) -> ChatCompletionResponse:
        pass


    @abstractmethod
    async def _get_completion(
        self,
        **kwargs
    ) -> Any:
        pass


    @abstractmethod
    async def _get_completion_stream(
        self,
        **kwargs
    ) -> AsyncIterable[Any]:
        """Get streaming completion from provider."""
        pass


    @abstractmethod
    def _get_stream_processor(
        self,
        stream_options: Optional[StreamOptions] = None,
    ) -> StreamProcessor:
        """Get provider-specific StreamProcessor."""
        pass


    async def _execute_completion(
        self,
        request: ChatCompletionRequest,
    ) -> ChatCompletionResponse:
        """Execute the completion request without retry logic."""
        denormalized_request = self._denormalize_request(request)
        completion = await self._get_completion(**denormalized_request)
        return self._normalize_response(completion)


    async def generate_chat_completion(
        self,
        request: ChatCompletionRequest,
    ) -> ChatCompletionResponse:
        """
        Generate chat completion.

        Args:
            request: Normalized chat completion request

        Returns:
            ChatCompletionResponse with normalized data
        """
        if request.retry and request.retry.enabled:
            return await retry_with_backoff(
                self._execute_completion,
                retry_config=request.retry,
                request=request,
            )
        return await self._execute_completion(request)


    def _setup_stream(
        self,
        request: ChatCompletionRequest,
        stream_options: Optional[StreamOptions] = None,
    ) -> AsyncIterable[ChatCompletionChunk]:
        """Set up the completion stream. Does not start iteration."""
        denormalized_request = self._denormalize_request(request)
        processor = self._get_stream_processor(stream_options)
        completion_stream = self._get_completion_stream(**denormalized_request)
        return processor.process_stream(completion_stream)


    async def _connect_stream(
        self,
        request: ChatCompletionRequest,
        stream_options: Optional[StreamOptions] = None,
    ) -> tuple[ChatCompletionChunk, AsyncIterable[ChatCompletionChunk]]:
        """Establish stream connection and return first chunk with iterator.

        Raises StopAsyncIteration if stream is empty.
        """
        stream = self._setup_stream(request, stream_options)
        aiter = stream.__aiter__()
        first_chunk = await aiter.__anext__()
        return (first_chunk, aiter)


    async def generate_chat_completion_stream(
        self,
        request: ChatCompletionRequest,
        stream_options: Optional[StreamOptions] = None,
    ) -> AsyncIterable[ChatCompletionChunk]:
        """
        Generate streaming chat completion.

        Args:
            request: Normalized chat completion request
            stream_options: Options for configuring streaming behavior

        Returns:
            AsyncIterable of ChatCompletionStreamChunk with normalized data

        Retry Behavior:
            Retries ONLY the initial connection (before streaming starts).
            Once streaming begins, failures are NOT retried to prevent duplicate content.
        """
        if not (request.retry and request.retry.enabled):
            async for chunk in self._setup_stream(request, stream_options):
                yield chunk
            return

        try:
            first_chunk, aiter = await retry_with_backoff(
                self._connect_stream,
                retry_config=request.retry,
                request=request,
                stream_options=stream_options,
            )
        except StopAsyncIteration:
            # Empty stream
            return

        # Yield first chunk and remaining chunks (no retry for mid-stream failures)
        yield first_chunk
        async for chunk in aiter:
            yield chunk
