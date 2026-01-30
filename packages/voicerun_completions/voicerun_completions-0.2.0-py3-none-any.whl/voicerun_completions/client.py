from typing import Any, Optional, Union, AsyncIterable
from loguru import logger

from .types.request import (
    CompletionsProvider,
    ChatCompletionRequest,
    ChatCompletionRequestDict,
    StreamOptions,
    StreamOptionsDict,
)
from .types.streaming import ChatCompletionChunk
from .types.response import ChatCompletionResponse
from .providers.base import CompletionClient
from .providers.openai.openai_client import OpenAiCompletionClient
from .providers.anthropic.anthropic_client import AnthropicCompletionClient
from .providers.google.google_client import GoogleCompletionClient
from .providers.vertex_anthropic.vertex_anthropic_client import VertexAnthropicCompletionClient


def _get_client(provider: CompletionsProvider) -> CompletionClient:
    """Get the completion client for the given provider."""
    if provider == CompletionsProvider.OPENAI:
        return OpenAiCompletionClient()
    elif provider == CompletionsProvider.ANTHROPIC:
        return AnthropicCompletionClient()
    elif provider == CompletionsProvider.GOOGLE:
        return GoogleCompletionClient()
    elif provider == CompletionsProvider.VERTEX_ANTHROPIC:
        return VertexAnthropicCompletionClient()
    else:
        raise ValueError(f"Invalid provider: {provider}")


async def generate_chat_completion(
    request: Union[ChatCompletionRequest, ChatCompletionRequestDict]
) -> ChatCompletionResponse:
    """
    Generate chat completion.

    Args:
        request: ChatCompletionRequest object or dict with request parameters

    Returns:
        ChatCompletionResponse with the complete response

    Note:
        Retry logic follows OpenAI's recommended exponential backoff pattern.
    """
    if isinstance(request, dict):
        request = ChatCompletionRequest(**request)

    completion_attempts: list[ChatCompletionRequest] = request._build_completion_attempts()
    last_exception = None
    for completion_request in completion_attempts:
        try:
            client = _get_client(completion_request.provider)
            return await client.generate_chat_completion(completion_request)                
        except Exception as e:
            logger.warning(f"Completion request failed with {str(e)}")
            last_exception = e

    raise Exception(f"Failed to generate completion. Last exception {str(last_exception)}")


async def generate_chat_completion_stream(
    request: Union[ChatCompletionRequest, ChatCompletionRequestDict],
    stream_options: Optional[Union[StreamOptions, StreamOptionsDict]] = None,
) -> AsyncIterable[ChatCompletionChunk]:
    """
    Generate streaming chat completion.

    Args:
        request: ChatCompletionRequest object or dict with request parameters
        stream_options: Options for configuring streaming behavior

    Returns:
        AsyncIterable of ChatCompletionChunk objects (typed chunks)

    Retry Behavior:
        When retry enabled, the function will retry ONLY the initial connection
        (before streaming starts). Retries use exponential backoff (1s, 2s, 4s, etc.).
        Once streaming begins, failures are NOT retried to prevent duplicate content.

        ✅ RETRIES (Initial Connection Failures):
           - Connection failures
           - Network errors before streaming starts
           - Rate limits (429)
           - Server errors (500, 502, 503)
           - Authentication errors (401)
           - Timeout errors

        ❌ NO RETRY (Mid-Stream Failures):
           - Once streaming begins, failures are NOT retried
           - This prevents duplicate content in real-time applications
           - Mid-stream failures raise exceptions immediately

        Example:
            # Connection retry attempt 1: ❌ Timeout
            # Wait 1 second...
            # Connection retry attempt 2: ✅ Success!
            # Stream chunk 1: "Hello..." ✅
            # Stream chunk 2: "world..."  ✅
            # [If chunk 3 fails → raises exception immediately, no retry]

        This ensures reliability without duplicate audio/messages.
    """
    if isinstance(request, dict):
        request = ChatCompletionRequest(**request)

    if stream_options and isinstance(stream_options, dict):
        stream_options = StreamOptions(**stream_options)

    completion_attempts: list[ChatCompletionRequest] = request._build_completion_attempts()

    async def _stream() -> AsyncIterable[ChatCompletionChunk]:
        last_exception = None

        for completion_request in completion_attempts:
            try:
                client = _get_client(completion_request.provider)
                stream = client.generate_chat_completion_stream(completion_request, stream_options)
                aiter = stream.__aiter__()
                first_chunk = await aiter.__anext__()
            except StopAsyncIteration:
                # Empty stream from this provider, try next fallback
                continue
            except Exception as e:
                logger.warning(f"Streaming connection failed with {str(e)}")
                last_exception = e
                continue

            # Connection established - yield first chunk and remaining (no more fallbacks)
            yield first_chunk
            async for chunk in aiter:
                yield chunk
            return

        raise Exception(f"Failed to stream generate completion. Last exception {str(last_exception)}")

    return _stream()
