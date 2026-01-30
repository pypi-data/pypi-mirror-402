"""Agents service MCP catalog overrides.

This file defines the minimal configuration needed to expose agents API
endpoints as MCP tools. Only specify overrides - everything else is
derived from the OpenAPI spec.

Priority: x-mcp-* extensions in spec > these overrides > safe defaults

NAMING CONVENTION:
- Endpoint names match the OpenAPI operationId from the upstream service
- Pattern: {method}_{resource}_{action} e.g., get_agent_list, post_conversation_list

Tier Guidelines (Workflow-Based):
- DIRECT: Tools for common AI assistant workflows (16 total):
  * Core Chat Flow: list/get agents, conversations, messages, send/stream
  * Prompt SDK: sdk_resolve, sdk_render
  * Background Monitoring: get_running, list/get runs
  * Browse Prompts: list/get prompts
- GATEWAY (default): Admin/CRUD operations via agents_api_call gateway
  * Agent/Conversation management (create, update, delete, stats)
  * Background agent management (list, create, update, trigger)
  * Prompt/Version management (create, update, delete, promote)
  * Folders and Tags (all operations)
- EXCLUDE: Never expose via MCP (health checks, internal endpoints)

Risk Level (for observability and rate limiting):
- low: Read-only operations
- medium (default): Operations that modify non-critical data
- high: Destructive or security-sensitive operations
"""

from yirifi_mcp.catalog.base import Tier

# =============================================================================
# TIER OVERRIDES - Workflow-focused DIRECT tools
# Default: GATEWAY (admin operations via agents_api_call)
# DIRECT: 16 tools for common AI assistant workflows
# =============================================================================

DIRECT_ENDPOINTS: list[str] = [
    # Core Chat Flow - "Chat with an agent" workflow
    # list_agents → get_agent → create_conversation → send_message → get_messages
    "list_agents",
    "get_agent",
    "create_conversation",
    "list_conversations",
    "get_conversation",
    "get_messages",
    "send_message",
    "stream_message",
    # Prompt SDK - "Use a prompt template" workflow
    # sdk_resolve → sdk_render
    "sdk_resolve",
    "sdk_render",
    # Background Monitoring - "Check background jobs" workflow
    # get_running → list_runs → get_run
    "get_running",
    "list_runs",
    "get_run",
    # Browse Prompts - Discovery
    "list_prompts",
    "get_prompt",
]

# Endpoints to exclude entirely (health checks, docs)
EXCLUDE_PATTERNS: list[str] = [
    r"^/health/.*",
    r"^/api/v1/docs.*",
    r"^/swagger.*",
]

# =============================================================================
# RISK OVERRIDES - For observability and rate limiting
# Default: "medium"
# Only specify non-medium risk levels
# =============================================================================

RISK_OVERRIDES: dict[str, str] = {
    # High risk - destructive operations
    "delete_agent": "high",
    "archive_conversation": "high",
    "disable_background_agent": "high",
    "delete_prompt": "high",
    "delete_folder": "high",
    "delete_tag": "high",
    # Low risk - read-only operations
    "list_agents": "low",
    "get_agent": "low",
    "agent_stats": "low",
    "search_agents": "low",
    "list_conversations": "low",
    "get_conversation": "low",
    "get_messages": "low",
    "conversation_stats": "low",
    "list_background_agents": "low",
    "get_background_agent": "low",
    "background_agent_stats": "low",
    "list_runs": "low",
    "get_run": "low",
    "get_running": "low",
    "list_prompts": "low",
    "get_prompt": "low",
    "search_prompts": "low",
    "prompt_stats": "low",
    "list_versions": "low",
    "get_version": "low",
    "get_active_version": "low",
    "get_deployment_status": "low",
    "get_prompt_usage": "low",
    "list_folders": "low",
    "get_folder": "low",
    "get_folder_tree": "low",
    "get_folder_children": "low",
    "list_tags": "low",
    "get_tag": "low",
    "search_tags": "low",
    "sdk_resolve": "low",
}

# =============================================================================
# OPTIONAL: Name/Description/Idempotent overrides
# Use when OpenAPI names/descriptions are not ideal for LLM context
# =============================================================================

NAME_OVERRIDES: dict[str, str] = {
    # Example: "list_agents": "get_all_agents",
}

DESCRIPTION_OVERRIDES: dict[str, str] = {
    # Example: "list_agents": "List all chat agents with pagination",
}

IDEMPOTENT_OVERRIDES: dict[str, bool] = {
    # Example: "update_agent": True,
}


def get_tier_overrides() -> dict[str, Tier]:
    """Build tier overrides dict from DIRECT_ENDPOINTS list.

    Returns:
        Dict mapping operationId to Tier.DIRECT
    """
    return {ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS}
