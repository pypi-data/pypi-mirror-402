#!/usr/bin/env python3
"""
Simple test script to validate streaming functionality.
This is for local development testing only.
"""

import asyncio
import os
from typing import Any
from voicerun_completions.client import generate_chat_completion, generate_chat_completion_stream
from voicerun_completions.types.messages import (
  ConversationHistory,
  UserMessage,
  AssistantMessage,
  ToolCall,
  FunctionCall,
  SystemMessage,
  ToolResultMessage,
)
from voicerun_completions.types.cache import CacheBreakpoint
from voicerun_completions.types.request import ChatCompletionRequest
from voicerun_completions.types.streaming import FinalResponseChunk


async def test_non_streaming():
    """Test that existing non-streaming functionality still works."""
    print("Testing non-streaming (backward compatibility)...")

    try:
        response = await generate_chat_completion({
            "provider": "openai",
            "api_key": os.getenv("OPENAI_API_KEY", "test-key"),
            "model": "gpt-4.1-mini",
            "messages": [{"role": "user", "content": "Hello!"}],
        })
        print(f"✅ Non-streaming response received: {type(response)}")
        print(f"Message: {response.message}")
        print(f"Finish reason: {response.finish_reason}")
    except Exception as e:
        print(f"❌ Non-streaming test failed: {e}")


async def test_streaming(provider: str, api_key: str, model: str, stream_sentences: bool):
    """Test the new streaming functionality."""
    print("\nTesting streaming...")

    try:
        stream = await generate_chat_completion_stream(
            request={
                "provider": provider,
                "api_key": api_key,
                "model": model,
                "messages": [{"role": "user", "content": "Say hello in five different languages."}],
            },
            stream_options={
                "stream_sentences": True,
                "clean_sentences": True,
            } if stream_sentences else None
        )

        print("✅ Streaming response initiated")
        chunk_count = 0

        async for chunk in stream:
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(chunk)
            print()

        print(f"✅ Streaming completed with {chunk_count} chunks")

    except Exception as e:
        print(f"❌ Streaming test failed: {e}")


async def test_streaming_whitespace(provider: str, api_key: str, model: str):
    """Test streaming functionality with potential whitespace."""
    print("\nTesting streaming...")

    try:
        stream = await generate_chat_completion_stream(
            ChatCompletionRequest(
                provider=provider,
                api_key=api_key,
                model=model,
                messages=[{"role": "user", "content": "Count to 5 slowly"}]
            ))

        print("✅ Streaming response initiated")
        chunk_count = 0

        async for chunk in stream:
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(chunk)
            print()

        print(f"✅ Streaming completed with {chunk_count} chunks")

    except Exception as e:
        print(f"❌ Streaming test failed: {e}")


async def test_streaming_long(provider: str, api_key: str, model: str, stream_sentences: bool = False):
    """Test streaming functionality with long response."""
    print("\nTesting streaming...")

    try:
        stream = await generate_chat_completion_stream(
            request={
                "provider": provider,
                "api_key": api_key,
                "model": model,
                "messages":[{"role": "user", "content": "Tell me a 500 word story"}]
            },
            stream_options={
                "stream_sentences": True,
                "clean_sentences": True,
            } if stream_sentences else None
        )

        print("✅ Streaming response initiated")
        chunk_count = 0

        async for chunk in stream:
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(chunk)
            print()

        print(f"✅ Streaming completed with {chunk_count} chunks")

    except Exception as e:
        print(f"❌ Streaming test failed: {e}")

async def test_streaming_dollars(provider: str, api_key: str, model: str, stream_sentences: bool = False):
    """Test streaming functionality with long response."""
    print("\nTesting streaming...")

    try:
        stream = await generate_chat_completion_stream(
            request={
                "provider": provider,
                "api_key": api_key,
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": "Could you tell me the price of a single bitcoin for years 2015-2020 with $XX.XX precision. Complete sentences. No special formatting."
                }]
            },
            stream_options={
                "stream_sentences": True,
                "clean_sentences": True,
                "min_sentence_length": 0
            } if stream_sentences else None,
        )

        print("✅ Streaming response initiated")
        chunk_count = 0

        async for chunk in stream:
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(chunk)
            print()

        print(f"✅ Streaming completed with {chunk_count} chunks")

    except Exception as e:
        print(f"❌ Streaming test failed: {e}")

async def test_streaming_with_tools(provider: str, api_key: str, model: str):
    """Test streaming with tool calls."""
    print("\nTesting streaming with tool calls...")

    tools: list[dict[str,Any]] = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    try:
        stream = await generate_chat_completion_stream({
            "provider": provider,
            "api_key": api_key,
            "model": model,
            "messages": [{"role": "user", "content": "What's the weather in NYC and in Boston?"}],
            "tools": tools,
            "tool_choice": "auto",
        })

        print("✅ Streaming with tools initiated")
        chunk_count = 0

        async for chunk in stream:
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(chunk)
            print()

        print(f"✅ Tool streaming completed with {chunk_count} chunks")

    except Exception as e:
        print(f"❌ Tool streaming test failed: {str(e)}")


async def test_streaming_with_tools_and_content():
    """Test streaming with tool calls and content."""
    print("\nTesting streaming with tool calls and content...")

    tools: list[dict[str,Any]] = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    try:
        stream = await generate_chat_completion_stream({
            "provider": "openai",
            "api_key": os.getenv("OPENAI_API_KEY", "test-key"),
            "model": "gpt-4.1-mini",
            "messages": [{"role": "user", "content": "Call get_weather and say Hello World in content in your response."}],
            "tools": tools,
            "tool_choice": "auto",
        })

        print("✅ Streaming with tools initiated")
        chunk_count = 0

        async for chunk in stream:
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(chunk)
            print()

        print(f"✅ Tool streaming completed with {chunk_count} chunks")

    except Exception as e:
        print(f"❌ Tool streaming test failed: {e}")


async def test_caching_with_tools(provider: str, api_key: str, model: str, stream: bool = False):
    """Test caching with tool calls."""
    print("\nTesting caching with tool calls...")

    tools: list[dict[str,Any]] = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            },
            "cache_breakpoint": {
                "ttl": "5m",
            }
        }
    ]

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "Give a summary of the user's content.",
            "cache_breakpoint": {
                "ttl": "5m",
            }
        },
        {
            "role": "user",
            "content": "<insert 4000 tokens here>",
            "cache_breakpoint": {
                "ttl": "5m",
            }
        }
    ]

    if stream:
        try:
            stream = await generate_chat_completion_stream({
                "provider": provider,
                "api_key": api_key,
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
            })

            print("✅ Streaming with tools initiated")
            chunk_count = 0

            async for chunk in stream:
                chunk_count += 1
                print(f"Chunk {chunk_count}:")
                print(chunk)
                print()

            print(f"✅ Tool streaming completed with {chunk_count} chunks")

        except Exception as e:
            print(f"❌ Tool streaming test failed: {e}")
    else:
        try:
            response = await generate_chat_completion({
                "provider": provider,
                "api_key": api_key,
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
            })
            print(f"Response: {response}")
        except Exception as e:
            print(f"❌ Non-streaming test failed: {e}")


async def test_cache_breakpoints(provider: str, api_key: str, model: str, stream: bool = False):
    """Test caching with tool calls."""
    print("\nTesting caching with tool calls...")

    tools: list[dict[str,Any]] = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            },
            "cache_breakpoint": {
                "ttl": "5m",
            }
        }
    ]

    messages: ConversationHistory = [
        SystemMessage(
            content="Answer the user's question.",
            cache_breakpoint=CacheBreakpoint(ttl="5m"),
        ),
        UserMessage(
            content="What's the weather in NYC?",
        ),
        AssistantMessage(
            content=None,
            tool_calls=[ToolCall(
                id="toolcall_0",
                type="function",
                index=0,
                function=FunctionCall(
                    name="get_weather",
                    arguments={
                        "location": "NYC"
                    }
                )
            )],
        ),
        ToolResultMessage(
            tool_call_id="toolcall_0",
            name="get_weather",
            content={
                "success": True,
                "weather": "75 degrees and sunny"
            },
        ),
        UserMessage(
            content="Thanks.",
            cache_breakpoint=CacheBreakpoint(ttl="5m"),
        )
    ]

    if stream:
        try:
            stream = await generate_chat_completion_stream({
                "provider": provider,
                "api_key": api_key,
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
            })

            print("✅ Streaming with tools initiated")
            chunk_count = 0

            async for chunk in stream:
                chunk_count += 1
                print(f"Chunk {chunk_count}:")
                print(chunk)
                print()

            print(f"✅ Tool streaming completed with {chunk_count} chunks")

        except Exception as e:
            print(f"❌ Tool streaming test failed: {e}")
    else:
        try:
            response = await generate_chat_completion({
                "provider": provider,
                "api_key": api_key,
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
            })
            print(f"Response: {response}")
        except Exception as e:
            print(f"❌ Non-streaming test failed: {e}")


async def test_streaming_empty_tool(provider: str, api_key: str, model: str):
    """Test streaming with tool calls."""
    print("\nTesting streaming with tool calls...")

    tools: list[dict[str,Any]] = [
        {
            "type": "function",
            "function": {
                "name": "get_order_total",
                "description": "Calculate final order total with taxes and fees",
                # TODO
                "parameters": {"type": "object", "properties": {}}
            }
        }
    ]

    try:
        stream = await generate_chat_completion_stream({
            "provider": provider,
            "api_key": api_key,
            "model": model,
            "messages": [{"role": "user", "content": "Can you check my order total."}],
            "tools": tools,
            "tool_choice": "auto",
        })

        print("✅ Streaming with empty tool initiated")
        chunk_count = 0

        async for chunk in stream:
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(chunk)
            print()

        print(f"✅ Tool streaming completed with {chunk_count} chunks")

    except Exception as e:
        print(f"❌ Tool streaming test failed: {str(e)}")


async def test_streaming_multi_turn(provider: str, api_key: str, model: str, stream_sentences: bool = False):
    """Test streaming functionality with multiple turns in the conversation."""
    print("\nTesting streaming with multi-turn conversation...")

    messages: list[dict[str, Any]] = []

    user_prompts = [
        "Hello! Can you tell me what 2+2 is?",
        "Great! Now what about 5*5?",
        "Perfect! Can you summarize our conversation so far?"
    ]

    try:
        for turn_num, user_prompt in enumerate(user_prompts, 1):
            print(f"\n--- Turn {turn_num} ---")

            # Add user message to conversation
            messages.append({"role": "user", "content": user_prompt})
            print(f"User: {user_prompt}")

            # Stream the response
            stream = await generate_chat_completion_stream(
                {
                    "provider": provider,
                    "api_key": api_key,
                    "model": model,
                    "messages": messages,
                },
                stream_options={
                    "stream_sentences": True,
                    "clean_sentences": True,
                } if stream_sentences else None,
            )

            print(f"✅ Turn {turn_num} streaming initiated")
            chunk_count = 0
            full_response = None

            async for chunk in stream:
                chunk_count += 1
                print(f"Chunk {chunk_count}:")
                print(chunk)
                print()

                # Get the complete response from the final chunk
                if isinstance(chunk, FinalResponseChunk):
                    full_response = chunk.response.message.content

            print(f"✅ Turn {turn_num} streaming completed with {chunk_count} chunks")

            # Add assistant response to conversation history
            if full_response:
                messages.append({"role": "assistant", "content": full_response})
                print(f"Assistant: {full_response}\n")
            else:
                print("⚠️ No response content received")

        print(f"✅ Multi-turn streaming test completed successfully with {len(user_prompts)} turns")

    except Exception as e:
        print(f"❌ Multi-turn streaming test failed: {e}")


async def test_thought_signature(provider: str, api_key: str, model: str, stream: bool):
    """Test thought signature."""
    print("\nTesting thought signature...")

    tools: list[dict[str,Any]] = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    if stream:
        try:
            stream = await generate_chat_completion_stream({
                "provider": provider,
                "api_key": api_key,
                "model": model,
                "messages": [{"role": "user", "content": "What's the weather in NYC and in Boston?"}],
                "tools": tools,
                "tool_choice": "auto",
            })

            print("✅ Streaming with tools initiated")
            chunk_count = 0

            async for chunk in stream:
                chunk_count += 1
                print(f"Chunk {chunk_count}:")
                print(chunk)
                print()

            print(f"✅ Tool streaming completed with {chunk_count} chunks")

        except Exception as e:
            print(f"❌ Tool streaming test failed: {e}")
    else:
        try:
            response = await generate_chat_completion({
                "provider": provider,
                "api_key": api_key,
                "model": model,
                "messages": [{"role": "user", "content": "What's the weather in NYC and in Boston?"}],
                "tools": tools,
                "tool_choice": "auto",
            })
            print(f"Response: {response}")
        except Exception as e:
            print(f"❌ Non-streaming test failed: {e}")




async def main():
    """Run all tests."""
    print("🚀 Testing voicerun-completions streaming support")
    print("=" * 60)

    # # Test backward compatibility first
    # await test_non_streaming()

    # # OPENAI

    # # Test basic streaming openai
    # await test_streaming(
    #     provider="openai",
    #     api_key=os.getenv("OPENAI_API_KEY", "test-key"),
    #     model="gpt-4.1-mini",
    #     stream_sentences=True,
    # )


    # # Test basic streaming with whitespace openai
    # await test_streaming_whitespace(
    #     provider="openai",
    #     api_key=os.getenv("OPENAI_API_KEY", "test-key"),
    #     model="gpt-4.1-mini",
    # )

    # # Test streaming with tools and content
    # await test_streaming_with_tools_and_content()


    # # Test streaming with tools openai
    # await test_streaming_with_tools(
    #     provider="openai",
    #     api_key=os.getenv("OPENAI_API_KEY", "test-key"),
    #     model="gpt-4.1-mini",
    # )

    # Test streaming with long response openai
    await test_streaming_long(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY", "test-key"),
        model="gpt-4.1-mini",
    )

    # # Test streaming with dollar amounts
    # await test_streaming_dollars(
    #     provider="openai",
    #     api_key=os.getenv("OPENAI_API_KEY", "test-key"),
    #     model="gpt-4.1-mini",
    #     stream_sentences=True
    # )

    # # Test streaming with tool with no args 
    # await test_streaming_empty_tool(
    #     provider="openai",
    #     api_key=os.getenv("OPENAI_API_KEY", "test-key"),
    #     model="gpt-4.1-mini",
    # )

    # # Test cache breakpoints ignored
    # await test_cache_breakpoints(
    #     provider="openai",
    #     api_key=os.getenv("OPENAI_API_KEY", "test-key"),
    #     model="gpt-4.1-mini",
    #     stream=False,
    # )

    # # Test cache breakpoints ignored streaming
    # await test_cache_breakpoints(
    #     provider="openai",
    #     api_key=os.getenv("OPENAI_API_KEY", "test-key"),
    #     model="gpt-4.1-mini",
    #     stream=True,
    # )





    # ANTHROPIC

    # # Test streaming with tools anthropic
    # await test_streaming_with_tools(
    #     provider="anthropic",
    #     api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
    #     model="claude-haiku-4-5",
    # )

    # # Test basic streaming anthropic
    # await test_streaming(
    #     provider="anthropic",
    #     api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
    #     model="claude-haiku-4-5",
    #     stream_sentences=False,
    # )

    # # Test basic streaming with whitespace anthropic
    # await test_streaming_whitespace(
    #     provider="anthropic",
    #     api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
    #     model="claude-haiku-4-5",
    # )

    # Test streaming with long response anthropic
    await test_streaming_long(
        provider="anthropic",
        api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
        model="claude-haiku-4-5",
    )

    # # Test streaming with dollar amounts
    # await test_streaming_dollars(
    #     provider="anthropic",
    #     api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
    #     model="gpt-4.1-mini",
    #     stream_sentences=True
    # )

    # # Test caching anthropic
    # await test_caching_with_tools(
    #     provider="anthropic",
    #     api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
    #     model="claude-haiku-4-5",
    #     stream=True,
    # )
    # await test_caching_with_tools(
    #     provider="anthropic",
    #     api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
    #     model="claude-haiku-4-5",
    #     stream=False,
    # )

    # # Test streaming with tool with no args 
    # await test_streaming_empty_tool(
    #     provider="anthropic",
    #     api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
    #     model="claude-haiku-4-5",
    # )

    # # Test anthropic cache breakpoints
    # await test_cache_breakpoints(
    #     provider="anthropic",
    #     api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
    #     model="claude-haiku-4-5",
    #     stream=False,
    # )

    # # Test anthropic cache breakpoints streaming
    # await test_cache_breakpoints(
    #     provider="anthropic",
    #     api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
    #     model="claude-haiku-4-5",
    #     stream=True,
    # )





    # # GOOGLE

    # # Test streaming with tools google
    # await test_streaming_with_tools(
    #     provider="google",
    #     api_key=os.getenv("GEMINI_API_KEY", "test-key"),
    #     model="gemini-2.5-flash",
    # )

    # # Test basic streaming google
    # await test_streaming(
    #     provider="google",
    #     api_key=os.getenv("GEMINI_API_KEY", "test-key"),
    #     model="gemini-2.5-flash",
    #     stream_sentences=False,
    # )

    # # Test streaming sentences google
    # await test_streaming(
    #     provider="google",
    #     api_key=os.getenv("GEMINI_API_KEY", "test-key"),
    #     model="gemini-2.5-flash",
    #     stream_sentences=True,
    # )

    # # Test basic streaming with whitespace google
    # await test_streaming_whitespace(
    #     provider="google",
    #     api_key=os.getenv("GEMINI_API_KEY", "test-key"),
    #     model="gemini-2.5-flash",
    # )

    # Test streaming with long response google
    await test_streaming_long(
        provider="google",
        api_key=os.getenv("GEMINI_API_KEY", "test-key"),
        model="gemini-2.5-flash",
    )

    # Test streaming sentences with long response google
    await test_streaming_long(
        provider="google",
        api_key=os.getenv("GEMINI_API_KEY", "test-key"),
        model="gemini-2.5-flash",
        stream_sentences=True,
    )

    # # Test cache breakpoints ignored
    # await test_cache_breakpoints(
    #     provider="google",
    #     api_key=os.getenv("GEMINI_API_KEY", "test-key"),
    #     model="gemini-2.5-flash",
    #     stream=False,
    # )

    # # Test streaming multiple turns google
    # await test_streaming_multi_turn(
    #     provider="google",
    #     api_key=os.getenv("GEMINI_API_KEY", "test-key"),
    #     model="gemini-2.5-flash",
    #     stream_sentences=True,
    # )

    # # Test thought signature captured no stream
    # await test_thought_signature(
    #     provider="google",
    #     api_key=os.getenv("GEMINI_API_KEY", "test-key"),
    #     model="gemini-3-flash-preview",
    #     stream=False
    # )

    # # Test thought signature captured stream
    # await test_thought_signature(
    #     provider="google",
    #     api_key=os.getenv("GEMINI_API_KEY", "test-key"),
    #     model="gemini-3-flash-preview",
    #     stream=True
    # )

    print("\n" + "=" * 60)
    print("🎉 Testing completed!")


if __name__ == "__main__":
    print("Note: Set api key environment variables for full testing")
    asyncio.run(main())