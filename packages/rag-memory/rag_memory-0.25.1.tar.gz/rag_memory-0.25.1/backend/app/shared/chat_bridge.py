"""
SSE streaming bridge for LangGraph agent execution.

Provides token-by-token streaming from agent to frontend via Server-Sent Events.
Based on Lumentor's chat_bridge.py pattern.
"""

import json
import logging
from typing import AsyncGenerator, Dict

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession

from ..rag.models import Conversation, Message

logger = logging.getLogger(__name__)


def extract_tool_result_data(tool_result):
    """
    Extract actual data from MCP tool result.

    MCP tools via LangChain adapters can return results in different formats:
    1. Plain JSON string: '[{"similarity": 0.85, ...}]'
    2. List of content blocks: [{"type": "text", "text": '[{"similarity": 0.85, ...}]'}]
    3. Already parsed dict/list

    This function normalizes all formats to the actual data.
    """
    logger.debug(f"extract_tool_result_data input type: {type(tool_result).__name__}")

    # If it's a string, try to parse as JSON
    if isinstance(tool_result, str):
        logger.debug(f"Tool result is string, length={len(tool_result)}")
        try:
            parsed = json.loads(tool_result)
            logger.debug(f"Parsed JSON string to {type(parsed).__name__}")
            return parsed
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug(f"Failed to parse as JSON: {e}")
            return tool_result

    # If it's a list, check if it's MCP content blocks
    if isinstance(tool_result, list) and len(tool_result) > 0:
        first_item = tool_result[0]
        logger.debug(f"Tool result is list with {len(tool_result)} items, first item type: {type(first_item).__name__}")

        # Check if this looks like an MCP content block (has 'type' and 'text' keys)
        if isinstance(first_item, dict) and 'type' in first_item and 'text' in first_item:
            logger.info("Detected MCP content blocks format - extracting text")
            # Extract text from all content blocks and concatenate
            text_content = ""
            for block in tool_result:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_content += block.get('text', '')

            # Try to parse the concatenated text as JSON
            if text_content:
                logger.debug(f"Extracted text content, length={len(text_content)}")
                try:
                    parsed = json.loads(text_content)
                    logger.debug(f"Parsed extracted text to {type(parsed).__name__}")
                    return parsed
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse extracted text as JSON: {e}")
                    return text_content
            return tool_result

        # If first item is a dict with expected search result keys, it's already parsed
        if isinstance(first_item, dict):
            sample_keys = list(first_item.keys())[:5]
            logger.debug(f"First item dict keys (sample): {sample_keys}")

    # Otherwise, return as-is (already in usable format)
    logger.debug("Returning tool result as-is")
    return tool_result


def is_tool_error(result_data) -> tuple[bool, str | None]:
    """
    Check if a tool result represents an error.

    MCP tools can return errors in several formats:
    1. String starting with "Error:" or containing exception text
    2. Dict with "error" key: {"error": "message"}
    3. Dict with "status": "error": {"status": "error", "message": "..."}

    Returns:
        Tuple of (is_error: bool, error_message: str | None)
    """
    # String error patterns
    if isinstance(result_data, str):
        lower = result_data.lower()
        if lower.startswith("error:") or "valueerror" in lower or "exception" in lower:
            return True, result_data
        return False, None

    # Dict error patterns
    if isinstance(result_data, dict):
        # Direct error key
        if "error" in result_data:
            return True, str(result_data.get("error") or result_data.get("message", "Unknown error"))

        # Status field indicating error
        if result_data.get("status") == "error":
            return True, str(result_data.get("message") or result_data.get("error", "Unknown error"))

    return False, None


async def stream_chat_response(
    agent,
    user_message: str,
    conversation_id: int,
    db: AsyncSession = None,
) -> AsyncGenerator[str, None]:
    """
    Stream LangGraph agent execution via SSE (token-by-token).

    Args:
        agent: Compiled LangGraph agent (from create_react_agent)
        user_message: User's message to process
        conversation_id: Conversation ID for thread persistence
        db: Optional database session for persisting messages

    Yields:
        SSE-formatted strings with token or metadata events
    """
    from ..database import async_session_maker

    logger.info(f"Starting SSE stream for conversation {conversation_id}")

    # Build thread ID for checkpointer
    thread_id = f"chat_{conversation_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Load current state from AsyncPostgresSaver checkpointer
        logger.debug(f"Loading state for thread {thread_id}")
        current_state = await agent.aget_state(config)

        logger.debug(f"current_state.values exists: {bool(current_state.values)}")
        if current_state.values:
            logger.debug(f"current_state.values keys: {list(current_state.values.keys())}")
            logger.debug(f"current_state messages count: {len(current_state.values.get('messages', []))}")

        # Check if this is first message (no existing state)
        if not current_state.values:
            logger.info("First message - creating initial state")
            # First message - create full initial state
            messages = [HumanMessage(content=user_message)]
            initial_state = {"messages": messages}
        else:
            # Continuing conversation - load messages from state and add new message
            existing_messages = current_state.values.get("messages", [])
            logger.info(f"Continuing conversation - existing messages: {len(existing_messages)}")

            # Add new user message to conversation
            user_msg = HumanMessage(content=user_message)
            updated_messages = existing_messages + [user_msg]
            logger.debug(f"Added user message, total messages now: {len(updated_messages)}")

            # Only update messages - other state fields preserved by checkpointer
            initial_state = {"messages": updated_messages}
            logger.debug("initial_state contains only messages key (checkpointer will merge)")

        # Save user message to database (separate session)
        async with async_session_maker() as db_session:
            user_msg_record = Message(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
            )
            db_session.add(user_msg_record)
            await db_session.commit()
            logger.debug("Saved user message to database")

        # Track assistant response content
        assistant_content = ""

        # Track active tool executions
        active_tools: Dict[str, str] = {}  # tool_id -> tool_name

        # Stream graph execution
        logger.info("Starting agent stream...")
        chunk_count = 0

        async for chunk in agent.astream(initial_state, config):
            chunk_count += 1
            logger.debug(f"Chunk #{chunk_count} keys: {list(chunk.keys())}")

            # Extract actual data from chunk (might be wrapped in node name)
            actual_data = chunk

            # If chunk has single key that's not "messages", extract it
            if len(chunk) == 1 and "messages" not in chunk:
                key = list(chunk.keys())[0]
                logger.debug(f"Chunk is wrapped in node name: '{key}'")
                if isinstance(chunk[key], dict):
                    actual_data = chunk[key]
                    logger.debug(f"Extracted actual_data from '{key}', keys: {list(actual_data.keys())}")

            # Process messages for tool detection and streaming
            if "messages" in actual_data:
                messages_list = actual_data["messages"]
                logger.debug(f"Found messages in chunk, count: {len(messages_list)}")

                if messages_list:
                    last_msg = messages_list[-1]

                    # 1. Handle ToolMessage (tool results) - emit structured events
                    if isinstance(last_msg, ToolMessage):
                        tool_name = last_msg.name
                        tool_id = last_msg.tool_call_id
                        tool_result = last_msg.content

                        logger.info(f"Tool result received: {tool_name} (ID: {tool_id})")

                        # Parse tool result - handles MCP content blocks, JSON strings, etc.
                        result_data = extract_tool_result_data(tool_result)
                        logger.debug(f"Parsed tool result type: {type(result_data).__name__}")

                        # Check for special UI control actions (e.g., open_modal)
                        if isinstance(result_data, dict) and result_data.get('action') == 'open_modal':
                            modal_type = result_data.get('modal', 'unknown')
                            modal_params = result_data.get('params', {})
                            modal_tab = result_data.get('tab', 'file')
                            logger.info(f"Open modal action detected: {modal_type} with tab={modal_tab}")
                            yield f"data: {json.dumps({'type': 'open_modal', 'modal': modal_type, 'tab': modal_tab, 'params': modal_params})}\n\n"

                        # Emit structured events based on tool name
                        if tool_name == 'search_documents':
                            logger.debug("Processing search_documents result")

                            # MCP tools return list[dict], but LangGraph may JSON-stringify each dict
                            # So we might get list[str] where each string is a JSON object
                            search_results = []

                            if isinstance(result_data, list):
                                for item in result_data:
                                    if isinstance(item, str):
                                        # Parse JSON string back to dict
                                        try:
                                            search_results.append(json.loads(item))
                                        except json.JSONDecodeError:
                                            logger.error(f"Failed to parse search result JSON: {item[:100]}")
                                    elif isinstance(item, dict):
                                        # Already a dict, use directly
                                        search_results.append(item)
                            elif isinstance(result_data, dict):
                                # Wrapped in outer dict with 'results' key
                                search_results = result_data.get('results', [result_data])

                            logger.debug(f"Emitting search_results with {len(search_results)} results")
                            yield f"data: {json.dumps({'type': 'search_results', 'results': search_results})}\n\n"

                        elif tool_name == 'web_search':
                            logger.debug("Emitting web_search_results event")
                            yield f"data: {json.dumps({'type': 'web_search_results', 'results': result_data})}\n\n"

                        elif tool_name == 'query_relationships':
                            logger.debug("Emitting knowledge_graph event")
                            yield f"data: {json.dumps({'type': 'knowledge_graph', 'data': result_data})}\n\n"

                        elif tool_name == 'query_temporal':
                            logger.debug("Emitting temporal_data event")
                            yield f"data: {json.dumps({'type': 'temporal_data', 'timeline': result_data})}\n\n"

                        elif tool_name == 'get_document_by_id':
                            logger.debug("Emitting document_selected event")
                            # Extract document_id from result
                            document_id = result_data.get('id') if isinstance(result_data, dict) else None
                            if document_id:
                                yield f"data: {json.dumps({'type': 'document_selected', 'document_id': document_id})}\n\n"
                            else:
                                logger.warning(f"get_document_by_id returned data without 'id' field")

                        # Emit tool_end event with error detection
                        if tool_id in active_tools:
                            tool_errored, error_msg = is_tool_error(result_data)
                            status = 'error' if tool_errored else 'completed'
                            tool_end_event = {'type': 'tool_end', 'tool': {'id': tool_id, 'name': tool_name, 'status': status}}
                            if tool_errored and error_msg:
                                tool_end_event['tool']['error'] = error_msg
                                logger.warning(f"Tool {tool_name} failed: {error_msg}")
                            yield f"data: {json.dumps(tool_end_event)}\n\n"
                            del active_tools[tool_id]

                    # 2. Handle AIMessage objects
                    elif isinstance(last_msg, AIMessage):
                        # Check if this is an intermediate tool-calling step
                        has_tool_calls = hasattr(last_msg, 'tool_calls') and last_msg.tool_calls

                        # 2a. AIMessage with tool_calls - emit tool_start events
                        if has_tool_calls:
                            logger.debug(f"Tool call detected: {len(last_msg.tool_calls)} tools")
                            for tool_call in last_msg.tool_calls:
                                tool_id = tool_call.get('id', 'unknown')
                                tool_name = tool_call.get('name', 'unknown')
                                active_tools[tool_id] = tool_name

                                logger.info(f"Tool call starting: {tool_name} (ID: {tool_id})")
                                yield f"data: {json.dumps({'type': 'tool_start', 'tool': {'id': tool_id, 'name': tool_name}})}\n\n"

                        # 2b. AIMessage without tool_calls - stream final response
                        elif last_msg.content:
                            content = last_msg.content

                            # Check if this is NEW content (not already streamed)
                            is_new_message = content and not content.startswith(assistant_content) and assistant_content not in content

                            if is_new_message or content not in assistant_content:
                                # NEW MESSAGE: Stream entire content, reset assistant_content
                                if is_new_message:
                                    logger.debug(f"New message detected - streaming {len(content)} chars")
                                    new_content = content
                                    assistant_content = ""  # Reset for new message
                                else:
                                    # CONTINUATION: Stream only new portion
                                    new_content = content[len(assistant_content):]
                                    logger.debug(f"Continuation - streaming {len(new_content)} new chars")

                                # Stream in reasonable chunks (not individual characters)
                                CHUNK_SIZE = 75  # Visible progress without excessive events
                                try:
                                    for i in range(0, len(new_content), CHUNK_SIZE):
                                        chunk = new_content[i:i+CHUNK_SIZE]
                                        assistant_content += chunk
                                        yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                                except Exception as e:
                                    # If chunking fails, send whole content
                                    logger.warning(f"Error streaming chunks: {e}, sending whole content")
                                    yield f"data: {json.dumps({'type': 'token', 'content': new_content})}\n\n"
                                    assistant_content += new_content

        logger.info(f"Graph execution complete - {chunk_count} chunks, {len(assistant_content)} chars")

        # Check if we hit an interrupt (paused before tool execution)
        state = await agent.aget_state(config)

        if state.next:  # Non-empty tuple like ("tools",) means paused at interrupt
            logger.info(f"Graph paused at interrupt - next nodes: {state.next}")

            # Get the last message which should contain pending tool calls
            messages = state.values.get('messages', [])
            if messages:
                last_msg = messages[-1]

                # Check for pending tool calls
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    pending_tools = []
                    for tc in last_msg.tool_calls:
                        pending_tools.append({
                            'id': tc.get('id', 'unknown'),
                            'name': tc.get('name', 'unknown'),
                            'args': tc.get('args', {})
                        })

                    logger.info(f"Tool proposal: {len(pending_tools)} tools pending approval")

                    # Save any assistant content generated so far
                    if assistant_content:
                        async with async_session_maker() as db_session:
                            assistant_msg = Message(
                                conversation_id=conversation_id,
                                role="assistant",
                                content=assistant_content,
                            )
                            db_session.add(assistant_msg)
                            await db_session.commit()
                            logger.info(f"Saved assistant preamble ({len(assistant_content)} chars)")

                    # Send tool_proposal event - frontend will show approval UI
                    yield f"data: {json.dumps({'type': 'tool_proposal', 'tools': pending_tools, 'conversation_id': conversation_id})}\n\n"

                    # Do NOT send 'done' - we're waiting for user approval
                    logger.info("SSE stream paused - awaiting tool approval")
                    return

        # No interrupt - save assistant message and complete normally
        if assistant_content:
            async with async_session_maker() as db_session:
                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=assistant_content,
                )
                db_session.add(assistant_msg)
                await db_session.commit()
                logger.info(f"Saved assistant response ({len(assistant_content)} chars)")

        # Send completion event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        logger.info("SSE stream completed successfully")

    except Exception as e:
        logger.error(f"Error in SSE stream: {e}", exc_info=True)
        # Send error event to client
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


async def resume_after_approval(
    agent,
    conversation_id: int,
) -> AsyncGenerator[str, None]:
    """
    Resume agent execution after user approves pending tool calls.

    The agent is paused at an interrupt before tool execution.
    This function resumes execution by passing None to astream().

    Args:
        agent: Compiled LangGraph agent (same instance with checkpointer)
        conversation_id: Conversation ID to resume

    Yields:
        SSE-formatted strings with token or metadata events
    """
    from ..database import async_session_maker

    logger.info(f"Resuming agent after approval for conversation {conversation_id}")

    thread_id = f"chat_{conversation_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Track assistant response content
        assistant_content = ""
        active_tools: Dict[str, str] = {}
        chunk_count = 0

        # Resume from interrupt by passing None (uses existing state)
        async for chunk in agent.astream(None, config):
            chunk_count += 1
            logger.debug(f"Resume chunk #{chunk_count} keys: {list(chunk.keys())}")

            # Extract actual data from chunk
            actual_data = chunk
            if len(chunk) == 1 and "messages" not in chunk:
                key = list(chunk.keys())[0]
                if isinstance(chunk[key], dict):
                    actual_data = chunk[key]

            # Process messages (same logic as stream_chat_response)
            if "messages" in actual_data:
                messages_list = actual_data["messages"]

                if messages_list:
                    last_msg = messages_list[-1]

                    # Handle ToolMessage (tool results)
                    if isinstance(last_msg, ToolMessage):
                        tool_name = last_msg.name
                        tool_id = last_msg.tool_call_id
                        tool_result = last_msg.content

                        logger.info(f"Tool result: {tool_name}")

                        # Parse tool result - handles MCP content blocks, JSON strings, etc.
                        result_data = extract_tool_result_data(tool_result)
                        logger.debug(f"Parsed tool result type: {type(result_data).__name__}")

                        # Check for special UI control actions (e.g., open_modal)
                        if isinstance(result_data, dict) and result_data.get('action') == 'open_modal':
                            modal_type = result_data.get('modal', 'unknown')
                            modal_params = result_data.get('params', {})
                            modal_tab = result_data.get('tab', 'file')
                            logger.info(f"Open modal action detected: {modal_type} with tab={modal_tab}")
                            yield f"data: {json.dumps({'type': 'open_modal', 'modal': modal_type, 'tab': modal_tab, 'params': modal_params})}\n\n"

                        # Emit structured events based on tool name
                        if tool_name == 'search_documents':
                            search_results = []
                            if isinstance(result_data, list):
                                for item in result_data:
                                    if isinstance(item, str):
                                        try:
                                            search_results.append(json.loads(item))
                                        except json.JSONDecodeError:
                                            logger.error(f"Failed to parse search result JSON: {item[:100]}")
                                    elif isinstance(item, dict):
                                        search_results.append(item)
                            elif isinstance(result_data, dict):
                                search_results = result_data.get('results', [result_data])
                            logger.debug(f"Emitting search_results with {len(search_results)} results")
                            yield f"data: {json.dumps({'type': 'search_results', 'results': search_results})}\n\n"

                        elif tool_name == 'web_search':
                            yield f"data: {json.dumps({'type': 'web_search_results', 'results': result_data})}\n\n"

                        elif tool_name == 'query_relationships':
                            yield f"data: {json.dumps({'type': 'knowledge_graph', 'data': result_data})}\n\n"

                        elif tool_name == 'query_temporal':
                            yield f"data: {json.dumps({'type': 'temporal_data', 'timeline': result_data})}\n\n"

                        elif tool_name == 'get_document_by_id':
                            document_id = result_data.get('id') if isinstance(result_data, dict) else None
                            if document_id:
                                yield f"data: {json.dumps({'type': 'document_selected', 'document_id': document_id})}\n\n"

                        # Emit tool_end event with error detection
                        if tool_id in active_tools:
                            tool_errored, error_msg = is_tool_error(result_data)
                            status = 'error' if tool_errored else 'completed'
                            tool_end_event = {'type': 'tool_end', 'tool': {'id': tool_id, 'name': tool_name, 'status': status}}
                            if tool_errored and error_msg:
                                tool_end_event['tool']['error'] = error_msg
                                logger.warning(f"Tool {tool_name} failed: {error_msg}")
                            yield f"data: {json.dumps(tool_end_event)}\n\n"
                            del active_tools[tool_id]

                    # Handle AIMessage
                    elif isinstance(last_msg, AIMessage):
                        has_tool_calls = hasattr(last_msg, 'tool_calls') and last_msg.tool_calls

                        if has_tool_calls:
                            for tool_call in last_msg.tool_calls:
                                tool_id = tool_call.get('id', 'unknown')
                                tool_name = tool_call.get('name', 'unknown')
                                active_tools[tool_id] = tool_name
                                yield f"data: {json.dumps({'type': 'tool_start', 'tool': {'id': tool_id, 'name': tool_name}})}\n\n"

                        elif last_msg.content:
                            content = last_msg.content
                            is_new_message = content and not content.startswith(assistant_content) and assistant_content not in content

                            if is_new_message or content not in assistant_content:
                                if is_new_message:
                                    new_content = content
                                    assistant_content = ""
                                else:
                                    new_content = content[len(assistant_content):]

                                CHUNK_SIZE = 75
                                for i in range(0, len(new_content), CHUNK_SIZE):
                                    chunk_text = new_content[i:i+CHUNK_SIZE]
                                    assistant_content += chunk_text
                                    yield f"data: {json.dumps({'type': 'token', 'content': chunk_text})}\n\n"

        logger.info(f"Resume complete - {chunk_count} chunks, {len(assistant_content)} chars")

        # Check for another interrupt (agent might want to call more tools)
        state = await agent.aget_state(config)

        if state.next:
            logger.info(f"Hit another interrupt after resume - next: {state.next}")
            messages = state.values.get('messages', [])
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    pending_tools = []
                    for tc in last_msg.tool_calls:
                        pending_tools.append({
                            'id': tc.get('id', 'unknown'),
                            'name': tc.get('name', 'unknown'),
                            'args': tc.get('args', {})
                        })

                    if assistant_content:
                        async with async_session_maker() as db_session:
                            assistant_msg = Message(
                                conversation_id=conversation_id,
                                role="assistant",
                                content=assistant_content,
                            )
                            db_session.add(assistant_msg)
                            await db_session.commit()

                    yield f"data: {json.dumps({'type': 'tool_proposal', 'tools': pending_tools, 'conversation_id': conversation_id})}\n\n"
                    return

        # Save final assistant message
        if assistant_content:
            async with async_session_maker() as db_session:
                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=assistant_content,
                )
                db_session.add(assistant_msg)
                await db_session.commit()
                logger.info(f"Saved assistant response ({len(assistant_content)} chars)")

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        logger.info("Resume stream completed")

    except Exception as e:
        logger.error(f"Error resuming after approval: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


async def reject_tool_proposal(
    agent,
    conversation_id: int,
    rejection_reason: str = None,
) -> AsyncGenerator[str, None]:
    """
    Reject pending tool calls and tell the agent not to execute them.

    Injects a user message telling the agent their proposal was rejected,
    then lets the agent respond appropriately.

    Args:
        agent: Compiled LangGraph agent
        conversation_id: Conversation ID
        rejection_reason: Optional reason for rejection

    Yields:
        SSE-formatted strings with agent's response
    """
    from ..database import async_session_maker

    logger.info(f"Rejecting tool proposal for conversation {conversation_id}")

    thread_id = f"chat_{conversation_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Get current state to find what tools were proposed
        state = await agent.aget_state(config)
        messages = state.values.get('messages', [])

        # Find the proposed tools for context
        proposed_tools = []
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                proposed_tools = [tc.get('name', 'unknown') for tc in last_msg.tool_calls]

        # Create rejection message
        reason_text = f": {rejection_reason}" if rejection_reason else ""
        rejection_msg = f"I've rejected the proposed tool call(s) ({', '.join(proposed_tools)}){reason_text}. Please acknowledge this and let me know what else you can help with."

        # Save rejection message to database
        async with async_session_maker() as db_session:
            user_msg_record = Message(
                conversation_id=conversation_id,
                role="user",
                content=rejection_msg,
            )
            db_session.add(user_msg_record)
            await db_session.commit()

        # Add rejection as user message and resume
        # We need to update state to skip the pending tools
        # By adding a HumanMessage, the agent will re-evaluate
        updated_messages = messages + [HumanMessage(content=rejection_msg)]

        # Track response
        assistant_content = ""
        chunk_count = 0

        async for chunk in agent.astream({"messages": updated_messages}, config):
            chunk_count += 1

            actual_data = chunk
            if len(chunk) == 1 and "messages" not in chunk:
                key = list(chunk.keys())[0]
                if isinstance(chunk[key], dict):
                    actual_data = chunk[key]

            if "messages" in actual_data:
                messages_list = actual_data["messages"]
                if messages_list:
                    last_msg = messages_list[-1]

                    if isinstance(last_msg, AIMessage) and last_msg.content:
                        has_tool_calls = hasattr(last_msg, 'tool_calls') and last_msg.tool_calls
                        if not has_tool_calls:
                            content = last_msg.content
                            is_new = content and not content.startswith(assistant_content)

                            if is_new or content not in assistant_content:
                                new_content = content if is_new else content[len(assistant_content):]
                                if is_new:
                                    assistant_content = ""

                                CHUNK_SIZE = 75
                                for i in range(0, len(new_content), CHUNK_SIZE):
                                    chunk_text = new_content[i:i+CHUNK_SIZE]
                                    assistant_content += chunk_text
                                    yield f"data: {json.dumps({'type': 'token', 'content': chunk_text})}\n\n"

        # Check for new interrupt
        state = await agent.aget_state(config)
        if state.next:
            messages = state.values.get('messages', [])
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    pending_tools = []
                    for tc in last_msg.tool_calls:
                        pending_tools.append({
                            'id': tc.get('id', 'unknown'),
                            'name': tc.get('name', 'unknown'),
                            'args': tc.get('args', {})
                        })

                    if assistant_content:
                        async with async_session_maker() as db_session:
                            assistant_msg = Message(
                                conversation_id=conversation_id,
                                role="assistant",
                                content=assistant_content,
                            )
                            db_session.add(assistant_msg)
                            await db_session.commit()

                    yield f"data: {json.dumps({'type': 'tool_proposal', 'tools': pending_tools, 'conversation_id': conversation_id})}\n\n"
                    return

        # Save response
        if assistant_content:
            async with async_session_maker() as db_session:
                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=assistant_content,
                )
                db_session.add(assistant_msg)
                await db_session.commit()

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        logger.error(f"Error rejecting tool proposal: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


async def revise_and_resume(
    agent,
    conversation_id: int,
    revised_tools: list,
) -> AsyncGenerator[str, None]:
    """
    Revise tool call arguments and resume execution.

    Updates the pending tool calls with revised arguments,
    then resumes the agent from the tools node.

    Args:
        agent: Compiled LangGraph agent
        conversation_id: Conversation ID
        revised_tools: List of revised tool calls with format:
            [{'id': 'tool_id', 'name': 'tool_name', 'args': {...}}]

    Yields:
        SSE-formatted strings with execution results
    """
    from ..database import async_session_maker

    logger.info(f"Revising and resuming tools for conversation {conversation_id}")

    thread_id = f"chat_{conversation_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Get current state
        state = await agent.aget_state(config)
        messages = state.values.get('messages', [])

        if not messages:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No messages in state'})}\n\n"
            return

        # Get the last AIMessage with tool_calls
        last_msg = messages[-1]
        if not (hasattr(last_msg, 'tool_calls') and last_msg.tool_calls):
            yield f"data: {json.dumps({'type': 'error', 'message': 'No pending tool calls to revise'})}\n\n"
            return

        # Create revised tool calls
        revised_tool_calls = []
        for revised in revised_tools:
            revised_tool_calls.append({
                'id': revised['id'],
                'name': revised['name'],
                'args': revised['args'],
            })

        # Create new AIMessage with revised tool calls
        # Preserve original content if any
        revised_ai_message = AIMessage(
            content=last_msg.content if last_msg.content else "",
            tool_calls=revised_tool_calls
        )

        # Update state with revised message - use as_node to replace at tools node
        await agent.update_state(
            config,
            {"messages": [revised_ai_message]},
            as_node="agent"  # Replace the agent's output
        )

        logger.info(f"Updated state with {len(revised_tool_calls)} revised tool calls")

        # Now resume execution - the tools will run with revised args
        async for event in resume_after_approval(agent, conversation_id):
            yield event

    except Exception as e:
        logger.error(f"Error revising tools: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
