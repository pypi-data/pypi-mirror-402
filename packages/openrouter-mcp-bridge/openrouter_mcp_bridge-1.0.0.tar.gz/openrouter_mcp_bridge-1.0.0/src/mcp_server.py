#!/usr/bin/env python3
"""
OpenRouter MCP Server - Simple API Bridge
Version 1.0.0
A minimal MCP server to interface with OpenRouter API.
Created by @htooayelwinict (forked from @shelakh/codex-bridge)

Following Carmack's principle: "Simplicity is prerequisite for reliability"
Following Torvalds' principle: "Good taste in code - knowing what NOT to write"

This server does ONE thing: bridge Claude to OpenRouter API. Nothing more.
Non-interactive execution with JSON output and batch processing support.
Async HTTP calls using httpx for optimal performance.

OpenBridge: Lightweight MCP server for OpenRouter API integration.
"""

import asyncio
import json
import os
import re
import time
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("open-bridge")


class OpenRouterClient:
    """Async client for OpenRouter API."""

    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable not set. "
                "Get your API key from https://openrouter.ai/keys"
            )

        self.model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o")
        self.timeout = int(os.environ.get("OPENROUTER_TIMEOUT", "90"))

    async def _call_api(
        self,
        messages: list[dict[str, str]],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make async API call to OpenRouter."""
        request_timeout = timeout or self.timeout

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/htooayelwinict/open-bridge",
            "X-Title": "Open Bridge"
        }

        payload = {
            "model": self.model,
            "messages": messages
        }

        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                response = await client.post(
                    self.OPENROUTER_API_URL,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            raise TimeoutError(
                f"OpenRouter API request timed out after {request_timeout} seconds"
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"OpenRouter API error: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            raise RuntimeError(f"OpenRouter API request failed: {str(e)}")

    async def query(
        self,
        query: str,
        timeout: Optional[int] = None
    ) -> str:
        """Simple query with user message."""
        messages = [{"role": "user", "content": query}]
        result = await self._call_api(messages, timeout)
        return result["choices"][0]["message"]["content"]

    async def query_with_json_format(
        self,
        query: str,
        timeout: Optional[int] = None
    ) -> str:
        """Query with JSON format instruction."""
        formatted_query = f"""{query}

Please respond in valid JSON format with this structure:
- "result": Your detailed answer/response
- "confidence": "high", "medium", or "low"
- "reasoning": Brief explanation of your analysis

Format your response as valid JSON only."""

        messages = [{"role": "user", "content": formatted_query}]
        result = await self._call_api(messages, timeout)
        return result["choices"][0]["message"]["content"]


def _get_timeout() -> int:
    """Get timeout from environment variable or default to 90 seconds."""
    try:
        return int(os.environ.get("OPENROUTER_TIMEOUT", "90"))
    except ValueError:
        return 90


def _format_prompt_for_json(query: str) -> str:
    """Append JSON format instructions to query for structured output."""
    return f"""{query}

Please respond in valid JSON format with this structure:
- "result": Your detailed answer/response
- "confidence": "high", "medium", or "low"
- "reasoning": Brief explanation of your analysis

Format your response as valid JSON only."""


def _extract_json_from_response(response: str) -> Optional[Dict]:
    """Extract JSON from mixed text response using regex."""
    lines = response.split('\n')
    clean_lines = []
    json_started = False

    for line in lines:
        # Look for JSON content
        if '{' in line:
            json_started = True
        if json_started:
            clean_lines.append(line)

    clean_response = '\n'.join(clean_lines)

    # Try to find complete JSON objects
    json_pattern = r'\{(?:[^{}]|{[^{}]*})*\}'
    matches = re.findall(json_pattern, clean_response, re.DOTALL)

    for match in matches:
        try:
            parsed = json.loads(match.strip())
            # Validate it has expected structure
            if isinstance(parsed, dict) and any(key in parsed for key in ['result', 'response', 'answer']):
                return parsed
        except json.JSONDecodeError:
            continue

    return None


def _format_response(raw_response: str, format_type: str, execution_time: float, directory: str) -> str:
    """Format response according to specified output format."""
    if format_type == "text":
        return raw_response

    elif format_type == "json":
        # Try to extract JSON from response first
        extracted_json = _extract_json_from_response(raw_response)

        if extracted_json:
            # Wrap extracted JSON in standard structure
            return json.dumps({
                "status": "success",
                "response": extracted_json,
                "metadata": {
                    "execution_time": execution_time,
                    "directory": directory,
                    "format": "json"
                }
            }, indent=2)
        else:
            # Fallback: wrap raw response
            return json.dumps({
                "status": "success",
                "response": raw_response,
                "metadata": {
                    "execution_time": execution_time,
                    "directory": directory,
                    "format": "json"
                }
            }, indent=2)

    elif format_type == "code":
        # Extract code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', raw_response, re.DOTALL)

        return json.dumps({
            "status": "success",
            "response": raw_response,
            "code_blocks": [{"language": lang or "text", "code": code.strip()} for lang, code in code_blocks],
            "metadata": {
                "execution_time": execution_time,
                "directory": directory,
                "format": "code"
            }
        }, indent=2)

    else:
        return raw_response


async def _process_single_query(
    client: OpenRouterClient,
    query: str,
    timeout: int,
    index: int
) -> dict:
    """Process a single query in batch mode."""
    query_start = time.time()

    try:
        processed_query = _format_prompt_for_json(query)
        raw_response = await client.query_with_json_format(query, timeout)
        execution_time = time.time() - query_start

        # Try to extract JSON from response
        extracted_json = _extract_json_from_response(raw_response)

        return {
            "status": "success",
            "index": index,
            "query": query[:100] + "..." if len(query) > 100 else query,
            "response": extracted_json if extracted_json else raw_response,
            "metadata": {
                "execution_time": execution_time,
                "timeout": timeout
            }
        }
    except TimeoutError:
        return {
            "status": "error",
            "index": index,
            "query": query[:100] + "..." if len(query) > 100 else query,
            "error": f"Query timed out after {timeout} seconds",
            "metadata": {"timeout": timeout}
        }
    except Exception as e:
        return {
            "status": "error",
            "index": index,
            "query": query[:100] + "..." if len(query) > 100 else query,
            "error": f"Error executing query: {str(e)}",
            "metadata": {}
        }


@mcp.tool()
async def consult_openrouter(
    query: str,
    directory: str,
    format: str = "json",
    timeout: Optional[int] = None
) -> str:
    """
    Consult OpenRouter API in non-interactive mode with structured output.

    Processes prompt and returns formatted response.
    Supports text, JSON, and code extraction formats.

    Args:
        query: The prompt to send to OpenRouter
        directory: Working directory (required) - for context only
        format: Output format - "text", "json", or "code" (default: "json")
        timeout: Optional timeout in seconds (overrides env var, recommended: 60-120)

    Returns:
        Formatted response based on format parameter
    """
    start_time = time.time()

    # Validate directory
    if not os.path.isdir(directory):
        error_response = f"Error: Directory does not exist: {directory}"
        if format == "json":
            return json.dumps({"status": "error", "error": error_response}, indent=2)
        return error_response

    # Validate format
    if format not in ["text", "json", "code"]:
        error_response = f"Error: Invalid format '{format}'. Must be 'text', 'json', or 'code'"
        return json.dumps({"status": "error", "error": error_response}, indent=2)

    try:
        # Initialize client and make query
        client = OpenRouterClient()

        if format == "json":
            raw_response = await client.query_with_json_format(query, timeout)
        else:
            raw_response = await client.query(query, timeout)

        execution_time = time.time() - start_time
        return _format_response(raw_response, format, execution_time, directory)

    except ValueError as e:
        # Missing API key
        error_response = str(e)
        if format == "json":
            return json.dumps({"status": "error", "error": error_response}, indent=2)
        return error_response
    except TimeoutError as e:
        execution_time = time.time() - start_time
        error_msg = str(e)
        if format == "json":
            return json.dumps({
                "status": "error",
                "error": error_msg,
                "metadata": {
                    "timeout": timeout or _get_timeout(),
                    "directory": directory,
                    "execution_time": execution_time
                }
            }, indent=2)
        return error_msg
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Error querying OpenRouter API: {str(e)}"
        if format == "json":
            return json.dumps({
                "status": "error",
                "error": error_msg,
                "metadata": {
                    "directory": directory,
                    "execution_time": execution_time,
                    "exception_type": type(e).__name__
                }
            }, indent=2)
        return error_msg


@mcp.tool()
async def consult_openrouter_with_stdin(
    stdin_content: str,
    prompt: str,
    directory: str,
    format: str = "json",
    timeout: Optional[int] = None
) -> str:
    """
    Consult OpenRouter with stdin content piped to prompt.

    Similar to 'echo "content" | open-bridge "prompt"' - combines stdin with prompt.
    Perfect for CI/CD workflows where you pipe file contents to the AI.

    Args:
        stdin_content: Content to pipe as stdin (e.g., file contents, diff, logs)
        prompt: The prompt to process the stdin content
        directory: Working directory (required)
        format: Output format - "text", "json", or "code" (default: "json")
        timeout: Optional timeout in seconds (overrides env var, recommended: 60-120)

    Returns:
        Formatted response based on format parameter
    """
    start_time = time.time()

    # Validate directory
    if not os.path.isdir(directory):
        error_response = f"Error: Directory does not exist: {directory}"
        if format == "json":
            return json.dumps({"status": "error", "error": error_response}, indent=2)
        return error_response

    # Validate format
    if format not in ["text", "json", "code"]:
        error_response = f"Error: Invalid format '{format}'. Must be 'text', 'json', or 'code'"
        return json.dumps({"status": "error", "error": error_response}, indent=2)

    # Combine stdin content with prompt
    combined_input = f"{stdin_content}\n\n{prompt}"

    try:
        client = OpenRouterClient()

        if format == "json":
            raw_response = await client.query_with_json_format(combined_input, timeout)
        else:
            raw_response = await client.query(combined_input, timeout)

        execution_time = time.time() - start_time
        return _format_response(raw_response, format, execution_time, directory)

    except ValueError as e:
        error_response = str(e)
        if format == "json":
            return json.dumps({"status": "error", "error": error_response}, indent=2)
        return error_response
    except TimeoutError as e:
        execution_time = time.time() - start_time
        error_msg = str(e)
        if format == "json":
            return json.dumps({
                "status": "error",
                "error": error_msg,
                "metadata": {
                    "timeout": timeout or _get_timeout(),
                    "directory": directory,
                    "execution_time": execution_time
                }
            }, indent=2)
        return error_msg
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Error querying OpenRouter API: {str(e)}"
        if format == "json":
            return json.dumps({
                "status": "error",
                "error": error_msg,
                "metadata": {
                    "directory": directory,
                    "execution_time": execution_time,
                    "exception_type": type(e).__name__
                }
            }, indent=2)
        return error_msg


@mcp.tool()
async def consult_openrouter_batch(
    queries: list[dict[str, Any]],
    directory: str,
    format: str = "json"
) -> str:
    """
    Consult multiple OpenRouter queries in batch - perfect for CI/CD automation.

    Processes multiple prompts concurrently and returns consolidated JSON output.
    Each query can have individual timeout and format preferences.

    Args:
        queries: List of query dictionaries with keys: 'query' (required), 'timeout' (optional)
        directory: Working directory (required)
        format: Output format - currently only "json" supported for batch

    Returns:
        JSON array with all results
    """
    start_time = time.time()

    # Validate directory
    if not os.path.isdir(directory):
        return json.dumps({
            "status": "error",
            "error": f"Directory does not exist: {directory}"
        }, indent=2)

    # Validate queries
    if not queries or not isinstance(queries, list):
        return json.dumps({
            "status": "error",
            "error": "Queries must be a non-empty list"
        }, indent=2)

    # Force JSON format for batch processing
    format = "json"

    try:
        client = OpenRouterClient()

        # Process all queries concurrently
        tasks = []
        for i, query_item in enumerate(queries):
            if not isinstance(query_item, dict) or 'query' not in query_item:
                tasks.append(asyncio.sleep(0))  # Dummy task
                continue

            query = str(query_item.get('query', ''))
            query_timeout = query_item.get('timeout', _get_timeout())

            # Create async task for each query
            task = _process_single_query(client, query, query_timeout, i)
            tasks.append(task)

        # Execute all queries concurrently
        query_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        results = []
        for i, result in enumerate(query_results):
            if isinstance(result, Exception):
                results.append({
                    "status": "error",
                    "error": str(result),
                    "index": i
                })
            elif isinstance(result, dict):
                results.append(result)

        execution_time = time.time() - start_time

        # Return consolidated results
        return json.dumps({
            "status": "completed",
            "total_queries": len(queries),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "results": results,
            "metadata": {
                "directory": directory,
                "format": format,
                "execution_time": execution_time
            }
        }, indent=2)

    except ValueError as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Batch processing failed: {str(e)}"
        }, indent=2)


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
