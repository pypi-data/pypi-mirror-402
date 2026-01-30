"""FastMCP server with MCP tool wrappers."""

import logging
import uuid

from fastmcp import FastMCP

from quantum_code.schemas.chat import ChatRequest
from quantum_code.schemas.codereview import CodeReviewRequest
from quantum_code.schemas.compare import CompareRequest
from quantum_code.schemas.debate import DebateRequest
from quantum_code.settings import settings
from quantum_code.tools.chat import chat_impl
from quantum_code.tools.codereview import codereview_impl
from quantum_code.tools.compare import compare_impl
from quantum_code.tools.debate import debate_impl
from quantum_code.tools.models import models_impl
from quantum_code.utils.helpers import get_version
from quantum_code.utils.mcp_decorator import mcp_monitor
from quantum_code.utils.mcp_factory import create_mcp_wrapper
from quantum_code.utils.paths import LOGS_DIR, ensure_logs_dir

logger = logging.getLogger(__name__)

mcp = FastMCP(settings.server_name)

@mcp.tool()
@mcp_monitor
async def codereview(
    content: str,
    models: list[str] | None = None,
    thread_id: str | None = None,
    relevant_files: list[str] | None = None,
    issues_found: list[dict] | None = None,
) -> dict:
    """Systematic code review using external models.
    Covers quality, security, performance, and architecture."""
    args = {
        "content": content,
        "models": models,
        "thread_id": thread_id,
        "relevant_files": relevant_files,
        "issues_found": issues_found,
    }
    args = {k: v for k, v in args.items() if v is not None}

    if "thread_id" not in args or args.get("thread_id") is None:
        args["thread_id"] = str(uuid.uuid4())

    try:
        model = CodeReviewRequest(**args)
        return await codereview_impl(**model.model_dump())
    except Exception as e:
        logger.exception(f"Error in codereview: {e}")
        return {
            "status": "error",
            "thread_id": args.get("thread_id", "unknown"),
            "content": f"**Tool execution error**\n\nAn error occurred: {str(e)[:200]}",
        }

@mcp.tool()
@mcp_monitor
async def chat(
    content: str,
    models: list[str] | None = None,
    thread_id: str | None = None,
    relevant_files: list[str] | None = None,
) -> dict:
    """General chat with AI assistant.
    Supports multi-turn conversations with project context and file inclusion."""
    args = {
        "content": content,
        "models": models,
        "thread_id": thread_id,
        "relevant_files": relevant_files,
    }
    args = {k: v for k, v in args.items() if v is not None}

    if "thread_id" not in args or args.get("thread_id") is None:
        args["thread_id"] = str(uuid.uuid4())

    try:
        model = ChatRequest(**args)
        return await chat_impl(**model.model_dump())
    except Exception as e:
        logger.exception(f"Error in chat: {e}")
        return {
            "status": "error",
            "thread_id": args.get("thread_id", "unknown"),
            "content": f"**Tool execution error**\n\nAn error occurred: {str(e)[:200]}",
        }

@mcp.tool()
@mcp_monitor
async def compare(
    content: str,
    models: list[str] | None = None,
    thread_id: str | None = None,
    relevant_files: list[str] | None = None,
) -> dict:
    """Compare responses from multiple AI models.
    Runs the same content against all specified models in parallel.
    Supports multi-turn conversations with project context and file inclusion."""
    args = {
        "content": content,
        "models": models,
        "thread_id": thread_id,
        "relevant_files": relevant_files,
    }
    args = {k: v for k, v in args.items() if v is not None}

    if "thread_id" not in args or args.get("thread_id") is None:
        args["thread_id"] = str(uuid.uuid4())

    try:
        model = CompareRequest(**args)
        return await compare_impl(**model.model_dump())
    except Exception as e:
        logger.exception(f"Error in compare: {e}")
        return {
            "status": "error",
            "thread_id": args.get("thread_id", "unknown"),
            "content": f"**Tool execution error**\n\nAn error occurred: {str(e)[:200]}",
        }


@mcp.tool()
@mcp_monitor
async def debate(
    content: str,
    models: list[str] | None = None,
    thread_id: str | None = None,
    relevant_files: list[str] | None = None,
) -> dict:
    """Multi-model debate: Step 1 (independent answers) + Step 2 (debate/critique).
    Each model provides independent answer, then reviews all responses and votes."""
    args = {
        "content": content,
        "models": models,
        "thread_id": thread_id,
        "relevant_files": relevant_files,
    }
    args = {k: v for k, v in args.items() if v is not None}

    if "thread_id" not in args or args.get("thread_id") is None:
        args["thread_id"] = str(uuid.uuid4())

    try:
        model = DebateRequest(**args)
        return await debate_impl(**model.model_dump())
    except Exception as e:
        logger.exception(f"Error in debate: {e}")
        return {
            "status": "error",
            "thread_id": args.get("thread_id", "unknown"),
            "content": f"**Tool execution error**\n\nAn error occurred: {str(e)[:200]}",
        }


@mcp.tool()
@mcp_monitor
async def version() -> dict:
    """
    Get server version, configuration details, and list of available tools.
    """
    tool_names: list[str] = []
    if hasattr(mcp, "_tools"):
        tools_dict = mcp._tools  # type: ignore[attr-defined]
        tool_names = [tool.name for tool in tools_dict.values()]

    return {
        "name": settings.server_name,
        "version": get_version(),
        "tools": sorted(tool_names) if tool_names else ["chat", "codereview", "compare", "debate", "models", "version"],
    }


@mcp.tool()
@mcp_monitor
async def models() -> dict:
    """
    List available AI models.
    Returns model names, aliases, provider, and configuration.
    """
    return await models_impl()


@mcp.prompt(name="codereview")
async def codereview_prompt() -> str:
    """Perform systematic code review"""
    return "Use the codereview tool to analyze code for quality, security, performance, and architecture issues."


@mcp.prompt(name="chat")
async def chat_prompt() -> str:
    """Chat with AI assistant"""
    return "Use the chat tool for general conversation, questions, and assistance."


@mcp.prompt(name="compare")
async def compare_prompt() -> str:
    """Compare responses from multiple AI models"""
    return "Use the compare tool to run the same query against multiple models in parallel."


@mcp.prompt(name="debate")
async def debate_prompt() -> str:
    """Multi-model debate with critique and voting"""
    return "Use the debate tool to run a two-step debate: models answer independently, then critique and vote on best response."


@mcp.prompt(name="models")
async def models_prompt() -> str:
    """List available AI models"""
    return "Use the models tool to see all available AI models, their aliases, and configuration."


@mcp.prompt(name="version")
async def version_prompt() -> str:
    """Get server version and info"""
    return "Use the version tool to see server version, configuration details, and available tools."


def main() -> None:
    """Entry point for quantum-server CLI command."""
    ensure_logs_dir()  # Create logs directory on first use, not on import
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(LOGS_DIR / "server.log")],
    )
    logger.info(f"[SERVER] Starting {settings.server_name} on stdio")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
