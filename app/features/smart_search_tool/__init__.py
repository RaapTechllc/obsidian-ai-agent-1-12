"""Initialization for smart search tool."""

from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("smart_search_tool_init started")

# Import the tool when this module is imported
try:
    from app.core.agents import vault_agent
    from app.features.smart_search_tool.smart_search_tool_service import execute_vault_smart_search
    logger.info("smart_search_tool_registered", tool="smart_search_tool")    
except ImportError as e:
    logger.error("smart_search_tool_init failed", error=str(e))
    logger.error("smart_search_tool_init_import_error")
