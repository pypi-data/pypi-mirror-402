#!/usr/bin/env python3
"""
Test script for Anthropic Vertex AI provider.
Requires: gcloud auth application-default login
"""

import asyncio
import os
from voicerun_completions.client import generate_chat_completion_stream
from voicerun_completions.types.request import ToolDefinitionDict


async def test_vertex_anthropic(region: str = "us-east5", stream_sentences: bool = False):
    """Test Anthropic Vertex AI provider."""
    print(f"\nTesting vertex_anthropic in {region}...")

    try:
        stream = await generate_chat_completion_stream(
            {
                "provider": "vertex_anthropic",
                "api_key": "",  # Not used - uses ADC
                "model": "claude-opus-4-5@20251101",
                "messages": [{"role": "user", "content": "Say hello in one sentence."}],
                "vendor_kwargs": {
                    "region": region,
                    "project_id": os.getenv("GCP_PROJECT_ID", "prim-ai-development"),
                }
            },
            stream_options={
                "stream_sentences": True,
                "clean_sentences": True,
            } if stream_sentences else None,
        )

        print("✅ Anthropic Vertex streaming initiated")
        chunk_count = 0

        async for chunk in stream:
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(chunk)
            print()

        print(f"✅ Anthropic Vertex streaming completed with {chunk_count} chunks")

    except Exception as e:
        print(f"❌ Anthropic Vertex test failed: {e}")


async def test_vertex_anthropic_with_tools(region: str = "us-east5"):
    """Test Anthropic Vertex AI provider with tool calls."""
    print(f"\nTesting vertex_anthropic with tools in {region}...")

    tools: list[ToolDefinitionDict] = [
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
            "provider": "vertex_anthropic",
            "api_key": "",  # Not used - uses ADC
            "model": "claude-opus-4-5@20251101",
            "messages": [{"role": "user", "content": "What's the weather in NYC?"}],
            "tools": tools,
            "tool_choice": "auto",
            "vendor_kwargs": {
                "region": region,
                "project_id": os.getenv("GCP_PROJECT_ID", "prim-ai-development"),
            }
        })

        print("✅ Anthropic Vertex with tools initiated")
        chunk_count = 0

        async for chunk in stream:
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(chunk)
            print()

        print(f"✅ Anthropic Vertex tool streaming completed with {chunk_count} chunks")

    except Exception as e:
        print(f"❌ Anthropic Vertex tool test failed: {e}")


async def main():
    """Run Anthropic Vertex tests."""
    print("🚀 Testing Anthropic Vertex AI provider")
    print("=" * 60)

    # Test basic streaming (us-east5)
    await test_vertex_anthropic(region="us-east5")

    # Test basic streaming (asia-southeast1 - Singapore)
    await test_vertex_anthropic(region="asia-southeast1")

    # Test streaming with sentence buffering
    # await test_vertex_anthropic(region="us-east5", stream_sentences=True)

    # Test streaming with tools
    # await test_vertex_anthropic_with_tools(region="us-east5")

    print("\n" + "=" * 60)
    print("🎉 Anthropic Vertex testing completed!")


if __name__ == "__main__":
    print("Note: Run 'gcloud auth application-default login' first")
    print(f"Using project: {os.getenv('GCP_PROJECT_ID', 'prim-ai-development')}")
    asyncio.run(main())
