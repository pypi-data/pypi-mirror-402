"""UI Control Tools - Python @tool decorated functions for frontend interaction.

These tools return special response formats that the chat_bridge interprets
to trigger frontend UI actions (like opening modals with pre-filled parameters).

These tools are ONLY for use by the RAG Memory web app's internal agent.
They should NOT be exposed via MCP to external consumers.
"""

import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
async def open_file_upload_dialog(
    tab: str = "file",
    collection_name: str = None,
    topic: str = None,
    mode: str = "ingest",
    reviewed_by_human: bool = False,
) -> dict:
    """
    Open the file/directory upload dialog in the UI with pre-filled parameters.

    This tool is specifically for local file/directory uploads from the user's computer.
    Due to browser security restrictions, you cannot pre-select the actual file or directory -
    the user must select it themselves. However, you CAN pre-fill all other parameters
    to streamline the upload process.

    IMPORTANT: This tool does NOT perform the upload. It opens the upload dialog with
    your recommended settings pre-filled. The user will:
    1. See the dialog with your parameters already filled in
    2. Select their file(s) or directory
    3. Click "Ingest" to start the upload
    4. Close the dialog when done and return to chat

    Args:
        tab: Which upload tab to open. Options:
             - "file" (default): For uploading individual files
             - "directory": For uploading entire directories
        collection_name: Target collection name (will pre-select in dropdown).
                        If None, user selects from available collections.
        topic: Topic for relevance scoring (e.g., "React hooks", "API authentication").
               If provided, ingested content will be scored for relevance to this topic.
        mode: Ingestion mode. Options:
              - "ingest" (default): New content, errors if already exists
              - "reingest": Update existing content, deletes old first
        reviewed_by_human: Whether to mark content as human-reviewed.
                          Default False. Only set True if user explicitly confirms
                          they've reviewed the content.

    Returns:
        A special response that triggers the frontend to open the upload modal:
        {
            "action": "open_modal",
            "modal": "ingestion",
            "tab": str,
            "params": {
                "collection_name": str | None,
                "topic": str | None,
                "mode": str,
                "reviewed_by_human": bool
            },
            "message": str
        }

    Example usage in conversation:
        User: "I want to upload some React documentation"
        Agent: "I'll help you upload files. What collection should I add them to?"
        User: "Put them in react-docs with topic 'React hooks'"
        Agent: [Proposes open_file_upload_dialog with params]
        User: [Approves]
        Agent: "I've opened the upload dialog with your settings. Please select
               your files and click Ingest. Let me know when you're done!"

    Note: This is a FREE operation (no API calls, just opens UI dialog).
    """
    logger.info(f"open_file_upload_dialog called: tab={tab}, collection={collection_name}, topic={topic}")

    # Validate tab parameter
    valid_tabs = ["file", "directory"]
    if tab not in valid_tabs:
        return {
            "action": "error",
            "error": f"Invalid tab '{tab}'. Must be one of: {valid_tabs}",
        }

    # Validate mode parameter
    valid_modes = ["ingest", "reingest"]
    if mode not in valid_modes:
        return {
            "action": "error",
            "error": f"Invalid mode '{mode}'. Must be one of: {valid_modes}",
        }

    # Build the response that tells the frontend to open the modal
    tab_label = "files" if tab == "file" else "a directory"

    return {
        "action": "open_modal",
        "modal": "ingestion",
        "tab": tab,
        "params": {
            "collection_name": collection_name,
            "topic": topic,
            "mode": mode,
            "reviewed_by_human": reviewed_by_human,
        },
        "message": f"Opening the upload dialog for {tab_label}. Please select your {tab_label} and click 'Ingest' when ready. Let me know when you're done!",
    }
