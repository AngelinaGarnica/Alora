import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.prompts import prompt, negative_prompt
from src.config import logger
from src.schema import AgentState
from src.tools import (
    db_query_tool,
    list_tables_tool,
    describe_table_tool,
    find_similar_table,
    PLOT_TOOL)
from src.agent import get_llm_agent

llm_with_tools = get_llm_agent()

MAX_REASONING_ITERATIONS = 5

def reasoning_node(state: AgentState) -> Dict:
    logger.info("[Node: Reasoning] Starting reasoning to generate SQL")
    tables = list_tables_tool()
    history = [HumanMessage(content=prompt.format(raw_query=state.raw_query, tables=", ".join(tables)))]
    iterations =0
    
    while iterations < MAX_REASONING_ITERATIONS:
        iterations += 1
        logger.info(f"[Node: Reasoning] Iteration {iterations}/{MAX_REASONING_ITERATIONS}")
        
        print(f"Iteration {iterations})")
        response = llm_with_tools.invoke(history)
        print(f"LLM Raw Response (Iteration {iterations}):\n{response}")

        finish_reason = None
        if hasattr(response, 'response_metadata') and isinstance(response.response_metadata, dict):
            finish_reason = response.response_metadata.get('finish_reason')
            print(f"DEBUG: response.response_metadata found. finish_reason = '{finish_reason}' (type: {type(finish_reason)})")
            print(f"DEBUG: Is finish_reason == 'MALFORMED_FUNCTION_CALL'? {finish_reason == 'MALFORMED_FUNCTION_CALL'}")
        else:
            print(f"DEBUG: response.response_metadata not found or not a dict. Type: {type(getattr(response, 'response_metadata', None))}")
        
        if finish_reason == 'MALFORMED_FUNCTION_CALL':
            logger.error("[Node: Reasoning] LLM returned MALFORMED_FUNCTION_CALL. The LLM attempted to call a tool incorrectly.")
            state.result = "Error: The AI tried to use a tool in an invalid way. Please try rephrasing your request."
            return state.model_dump() | {'next': 'END'}        
        
        if not isinstance(response, AIMessage):
            logger.warning("[Node: Reasoning] Unexpected response from the LLM")
            return state.model_dump() | {'next': 'Reasoning'}

        logger.info(f"[Node: Reasoning] LLM Response: {response.content}")

        tool_calls = response.tool_calls or []

        if not tool_calls and response.content:
            print("AI:", response.content)
            state.result = response.content

            # Check if the response contains the negative prompt, then End
            if negative_prompt in response.content:
                return state.model_dump() | {'next': 'END'}
            else:
                # Proceed to HumanApproval for confirmation
                return state.model_dump() | {'next': 'HumanApproval'}

        history.append(response)

        for tool_call_item in tool_calls:
            tool_name: str = None
            tool_args: Dict[str, Any] = {}
            tool_id: str = None
            is_error_in_call = False
            error_details = None

            if isinstance(tool_call_item, dict):
                logger.warning(f"[Node: Reasoning] Tool call item is a dictionary: {tool_call_item}. Processing as dict.")
                tool_name = tool_call_item.get("name")
                raw_args = tool_call_item.get("args")
                tool_id = tool_call_item.get("id")

                if isinstance(raw_args, dict):
                    tool_args = raw_args
                elif raw_args is not None:
                    logger.warning(f"Tool call (dict) for '{tool_name}' has non-dict args: {raw_args}. Using as string or empty.")
                    tool_args = {"__raw_args__": str(raw_args)}

            elif hasattr(tool_call_item, 'name') and hasattr(tool_call_item, 'id'):
                tool_name = tool_call_item.name
                raw_args = tool_call_item.args
                tool_id = tool_call_item.id

                if hasattr(tool_call_item, 'error') and tool_call_item.error:
                    is_error_in_call = True
                    error_details = tool_call_item.error
                
                if isinstance(raw_args, dict):
                    tool_args = raw_args
                elif raw_args is not None:
                    logger.warning(f"Tool call object for '{tool_name}' has non-dict args: {raw_args}")
                    tool_args = {"__raw_args__": str(raw_args)}
            else:
                logger.error(f"[Node: Reasoning] Unknown tool call item structure: {tool_call_item}. Skipping.")
                history.append(ToolMessage(tool_call_id="unknown_tool_id", content=f"⚠️ Error: Unknown tool call structure: {tool_call_item}"))
                continue

            if not tool_name or not tool_id:
                logger.error(f"[Node: Reasoning] Parsed tool call item is missing name or id: {tool_call_item}. Skipping.")
                history.append(ToolMessage(tool_call_id=tool_id or "missing_id", content=f"⚠️ Error: Parsed tool call missing name or id: {tool_call_item}"))
                continue

            if is_error_in_call:
                logger.error(f"[Node: Reasoning] Invalid tool call object received: Name: {tool_name}, Args: {raw_args}, Error: {error_details}")
                history.append(ToolMessage(tool_call_id=tool_id, content=f"⚠️ Error: Invalid tool call from LLM - {error_details}"))
                continue

            logger.info(f"[Node: Reasoning] Running tool: '{tool_name}' with args: {tool_args}")

            try:
                if tool_name == "list_tables":
                    output = list_tables_tool()
                elif tool_name == "describe_table":
                    table_name = tool_args.get("table_name")
                    if table_name is None:
                        raise ValueError("Missing 'table_name' argument for describe_table tool.")
                    output = describe_table_tool(table_name)
                elif tool_name == "find_similar_table":
                    column_hint = tool_args.get("column_hint")
                    if column_hint is None: 
                        raise ValueError("Missing 'column_hint' argument for find_similar_table tool.")
                    output = find_similar_table(column_hint)
                elif tool_name == "db_query_tool":
                    query = tool_args.get("query")
                    if query is None:
                        raise ValueError("Missing 'query' argument for db_query_tool tool.")
                    output = db_query_tool(query)
                else:
                    output = f"⚠️ Unknown tool: {tool_name}"

                history.append(ToolMessage(tool_call_id=tool_id, content=json.dumps(output)))

            except Exception as e:
                logger.exception(f"[Node: Reasoning] Error running tool {tool_name}")
                history.append(ToolMessage(tool_call_id=tool_id, content=f"⚠️ Error: {e}"))
        
        if iterations >= MAX_REASONING_ITERATIONS:
            logger.warning(f"[Node: Reasoning] Max reasoning iterations ({MAX_REASONING_ITERATIONS}) reached. Aborting.")
            state.result = f"Error: AI reached maximum thinking steps ({MAX_REASONING_ITERATIONS}) without a conclusion."
            return state.model_dump() | {'next': 'END'}

def human_approval_node(state: AgentState) -> Dict:
    print("Results:", state.result)
    ans = input("Is the data correct? (y/n): ").strip().lower()
    state.approved = ans.startswith('y')
    return state.model_dump() | {'next': 'GraphTools' if state.approved else 'Reasoning'}

def graph_tools_node(state: AgentState) -> Dict:
    ans = input("Would you like to generate a graph? (y/n): ").strip().lower()
    state.plot_confirm = ans.startswith('y')
    if state.plot_confirm:
        PLOT_TOOL.run(state.result)
    return state.model_dump() | {'next': 'END'}