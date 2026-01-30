#!/usr/bin/env python3
"""
Test script to validate fallback functionality.
This is for local development testing only.
"""

import asyncio
import os

from voicerun_completions.client import generate_chat_completion, generate_chat_completion_stream
from voicerun_completions.types.request import (
    ChatCompletionRequest,
    FallbackRequest,
    CompletionsProvider,
    RetryConfiguration,
)


# =============================================================================
# Unit Tests - No API calls
# =============================================================================

def test_apply_fallback_overrides_provider():
    """Test that fallback overrides provider correctly."""
    request = ChatCompletionRequest(
        provider=CompletionsProvider.OPENAI,
        api_key="openai-key",
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
    )

    fallback = FallbackRequest(
        provider=CompletionsProvider.ANTHROPIC,
        api_key="anthropic-key",
        model="claude-3",
    )

    result = request._apply_fallback(fallback)

    assert result.provider == CompletionsProvider.ANTHROPIC
    assert result.api_key == "anthropic-key"
    assert result.model == "claude-3"
    assert result.messages == request.messages  # Should inherit
    assert result.fallbacks is None  # Should not carry forward
    print("test_apply_fallback_overrides_provider")


def test_apply_fallback_preserves_unset_fields():
    """Test that fallback preserves fields not set in fallback."""
    request = ChatCompletionRequest(
        provider=CompletionsProvider.OPENAI,
        api_key="openai-key",
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.7,
        max_tokens=1000,
        timeout=30.0,
    )

    fallback = FallbackRequest(
        provider=CompletionsProvider.ANTHROPIC,
        # Only override provider, keep everything else
    )

    result = request._apply_fallback(fallback)

    assert result.provider == CompletionsProvider.ANTHROPIC
    assert result.api_key == "openai-key"  # Inherited
    assert result.model == "gpt-4"  # Inherited
    assert result.temperature == 0.7  # Inherited
    assert result.max_tokens == 1000  # Inherited
    assert result.timeout == 30.0  # Inherited
    print("test_apply_fallback_preserves_unset_fields")


def test_apply_fallback_handles_falsy_values():
    """Test that fallback correctly handles falsy values like 0 or False."""
    request = ChatCompletionRequest(
        provider=CompletionsProvider.OPENAI,
        api_key="openai-key",
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.7,
    )

    fallback = FallbackRequest(
        temperature=0.0,  # Falsy but valid
    )

    result = request._apply_fallback(fallback)

    assert result.temperature == 0.0  # Should be 0, not 0.7
    print("test_apply_fallback_handles_falsy_values")


def test_build_completion_attempts_single():
    """Test building attempts with no fallbacks."""
    request = ChatCompletionRequest(
        provider=CompletionsProvider.OPENAI,
        api_key="openai-key",
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
    )

    attempts = request._build_completion_attempts()

    assert len(attempts) == 1
    assert attempts[0].provider == CompletionsProvider.OPENAI
    print("test_build_completion_attempts_single")


def test_build_completion_attempts_with_fallbacks():
    """Test building attempts with multiple fallbacks."""
    request = ChatCompletionRequest(
        provider=CompletionsProvider.OPENAI,
        api_key="openai-key",
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
        fallbacks=[
            FallbackRequest(
                provider=CompletionsProvider.ANTHROPIC,
                api_key="anthropic-key",
                model="claude-3",
            ),
            FallbackRequest(
                provider=CompletionsProvider.GOOGLE,
                api_key="google-key",
                model="gemini-pro",
            ),
        ],
    )

    attempts = request._build_completion_attempts()

    assert len(attempts) == 3
    assert attempts[0].provider == CompletionsProvider.OPENAI
    assert attempts[1].provider == CompletionsProvider.ANTHROPIC
    assert attempts[2].provider == CompletionsProvider.GOOGLE
    # Verify fallbacks are not carried forward
    assert attempts[1].fallbacks is None
    assert attempts[2].fallbacks is None
    print("test_build_completion_attempts_with_fallbacks")


def test_normalize_retry_from_dict():
    """Test that retry config is normalized from dict."""
    request = ChatCompletionRequest(
        provider=CompletionsProvider.OPENAI,
        api_key="openai-key",
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
        retry={"max_retries": 5, "retry_delay": 2.0},
    )

    request._normalize()

    assert isinstance(request.retry, RetryConfiguration)
    assert request.retry.max_retries == 5
    assert request.retry.retry_delay == 2.0
    print("test_normalize_retry_from_dict")


def run_unit_tests():
    """Run all unit tests."""
    print("Running unit tests...")
    print("=" * 60)

    test_apply_fallback_overrides_provider()
    test_apply_fallback_preserves_unset_fields()
    test_apply_fallback_handles_falsy_values()
    test_build_completion_attempts_single()
    test_build_completion_attempts_with_fallbacks()
    test_normalize_retry_from_dict()

    print("=" * 60)
    print("All unit tests passed!")


# =============================================================================
# Integration Tests - Requires API keys
# =============================================================================

async def test_fallback_on_invalid_api_key():
    """Test that fallback is triggered when first provider fails with invalid key."""
    print("\nTesting fallback on invalid API key...")

    try:
        response = await generate_chat_completion({
            "provider": "openai",
            "api_key": "invalid-key-12345",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "fallbacks": [
                {
                    "provider": "anthropic",
                    "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                    "model": "claude-haiku-4-5",
                }
            ],
        })
        print(f"Response from fallback: {response.message.content[:100]}...")
        print("test_fallback_on_invalid_api_key")
    except Exception as e:
        print(f"test_fallback_on_invalid_api_key: {e}")


async def test_fallback_streaming_on_invalid_api_key():
    """Test that streaming fallback is triggered when first provider fails."""
    print("\nTesting streaming fallback on invalid API key...")

    try:
        stream = await generate_chat_completion_stream({
            "provider": "openai",
            "api_key": "invalid-key-12345",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Say hello briefly"}],
            "fallbacks": [
                {
                    "provider": "anthropic",
                    "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                    "model": "claude-haiku-4-5",
                }
            ],
        })

        chunk_count = 0
        async for chunk in stream:
            chunk_count += 1
            if chunk_count <= 3:
                print(f"Chunk {chunk_count}: {chunk}")

        print(f"Streaming fallback completed with {chunk_count} chunks")
        print("test_fallback_streaming_on_invalid_api_key")
    except Exception as e:
        print(f"test_fallback_streaming_on_invalid_api_key: {e}")


async def test_fallback_chain():
    """Test fallback chain with multiple providers."""
    print("\nTesting fallback chain...")

    try:
        response = await generate_chat_completion({
            "provider": "openai",
            "api_key": "invalid-key-1",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "fallbacks": [
                {
                    "provider": "anthropic",
                    "api_key": "invalid-key-2",
                    "model": "claude-3",
                },
                {
                    "provider": "google",
                    "api_key": os.getenv("GEMINI_API_KEY", ""),
                    "model": "gemini-2.0-flash",
                }
            ],
        })
        print(f"Response from final fallback: {response.message.content[:100]}...")
        print("test_fallback_chain")
    except Exception as e:
        print(f"test_fallback_chain: {e}")


async def test_no_fallback_on_success():
    """Test that fallback is not triggered when first provider succeeds."""
    print("\nTesting no fallback on success...")

    try:
        response = await generate_chat_completion({
            "provider": "openai",
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "model": "gpt-4.1-mini",
            "messages": [{"role": "user", "content": "Say 'primary provider' exactly"}],
            "fallbacks": [
                {
                    "provider": "anthropic",
                    "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                    "model": "claude-haiku-4-5",
                }
            ],
        })
        print(f"Response: {response.message.content}")
        print("test_no_fallback_on_success")
    except Exception as e:
        print(f"test_no_fallback_on_success: {e}")


async def test_retry_with_fallback():
    """Test retry configuration combined with fallback."""
    print("\nTesting retry with fallback...")

    try:
        response = await generate_chat_completion({
            "provider": "openai",
            "api_key": "invalid-key",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "retry": {
                "max_retries": 2,
                "retry_delay": 0.5,
            },
            "fallbacks": [
                {
                    "provider": "anthropic",
                    "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                    "model": "claude-haiku-4-5",
                }
            ],
        })
        print(f"Response after retry+fallback: {response.message.content[:100]}...")
        print("test_retry_with_fallback")
    except Exception as e:
        print(f"test_retry_with_fallback: {e}")


async def run_integration_tests():
    """Run all integration tests."""
    print("\nRunning integration tests...")
    print("=" * 60)

    await test_no_fallback_on_success()
    await test_fallback_on_invalid_api_key()
    await test_fallback_streaming_on_invalid_api_key()
    await test_fallback_chain()
    await test_retry_with_fallback()

    print("=" * 60)
    print("Integration tests completed!")


# =============================================================================
# Main
# =============================================================================

async def main():
    """Run all tests."""
    print("Testing fallback functionality")
    print("=" * 60)

    # Run unit tests (no API calls)
    run_unit_tests()

    # Run integration tests (requires API keys)
    print("\nNote: Integration tests require API keys in environment variables")
    await run_integration_tests()

    print("\n" + "=" * 60)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
