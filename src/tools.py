import json
import io
import contextlib
import logging
from difflib import get_close_matches
from typing import Any, List, Tuple
import plotly.express as px
import plotly.graph_objects as go
from langchain.agents import Tool
from src.config import db, logger, llm
from src.schema import DBQueryArgs, DescribeTableArgs, FindSimilarTableArgs


logger = logging.getLogger(__name__)

# Function to execute a SQL query against the database
def db_query_tool(query: str) -> List:
    logger.info(f"[Tool: db_query_tool] Executing query: {query}")
    try:
        return db.run(query)
    except Exception as e:
        logger.exception(f"[Tool: db_query_tool] Error executing query")
        return [[f"⚠️ Error: {e}"]]

def list_tables_tool() -> List[str]:
    logger.info("[Tool: list_tables] Getting the name of the tables")
    return db.get_usable_table_names()

def describe_table_tool(table_name: str) -> List[Tuple[str, str]]:
    logger.info(f"[Tool: describe_table] Describing tables: {table_name}")
    rows = db.run(f"PRAGMA table_info({table_name});")
    logger.info(f"[Tool: describe_table] Raw result: {rows}")
    return rows

def find_similar_table(column_hint: str) -> str:
    logger.info(f"[Tool: find_similar_table] Finding similar tables: {column_hint}")
    tables = db.get_usable_table_names()
    matches = get_close_matches(column_hint.lower(), [t.lower() for t in tables], n=1, cutoff=0.6)
    return matches[0] if matches else ""

def plot_code_with_llm(result: Any) -> str:
    logger.info("[Tool: plot_code] Generating graph")

    if not result:
        return "There is no data to graph."

    if isinstance(result, str):
        table_str = result.strip()
    else:
        # Ensure table_str is always a string, even if data prep fails
        try:
            if isinstance(result, list) and all(isinstance(row, (list, tuple)) for row in result):
                if result and result[0]:
                    headers = [f"col_{i}" for i in range(len(result[0]))]
                    data_preview = "\n".join([",".join(map(str, row)) for row in result[:10]])
                    table_str = ",".join(headers) + "\n" + data_preview
                else:
                    table_str = "Empty tabular data provided."
            else:
                # For other types, just dump a preview as JSON
                table_str = json.dumps(result[:10], indent=2)
        except Exception as e:
            logger.warning(f"[Tool: plot_code] Error preparing data for the LLM: {e}")
            table_str = f"Error preparing data preview: {e}. Original data (first 100 chars): {str(result)[:100]}"

    logger.info(f"[Tool: plot_code] Data passed to LLM for plotting (table_str):\n{table_str}")

    # Prompt al LLM
    plot_prompt = f"""
                  I have this data:
                  {table_str}

                  Analyze the provided data.
                  If the data is a single number or a very simple value where a chart wouldn't add much insight, you can simply state the value or use a Plotly indicator/metric if appropriate.
                  If the data is tabular or more complex and suitable for a chart:
                  Generate a complete, self-contained Python script snippet that uses **Plotly** (ideally plotly.express) to generate a plot.
                  The script snippet MUST include all necessary imports (e.g., `import plotly.express as px`, `import pandas as pd`, `import io`).
                  The script should define the data it needs, for example, by parsing the provided data string (which is a string representation of the data) or by creating lists/dictionaries directly within the script.
                  Create a figure object (e.g., `fig = px.bar(...)`) and then display it using `fig.show()`.
                  The graph should clearly visualize the data.
                  Do not include any explanations or markdown formatting, only the raw Python code.
                  Now, generate the Python code for the data provided at the beginning of this prompt.
                  """

    try:
        response = llm.invoke(plot_prompt)
        plot_code = response.content.strip("```python").strip("```").strip()

        logger.info(f"[Tool: plot_code] LLM graph code:\n{plot_code}")

        # Configure Plotly renderer for better VS Code integration
        import plotly.io as pio
        pio.renderers.default = 'browser'

        with contextlib.redirect_stdout(io.StringIO()) as f:
            exec_globals = {
                  "px": px,
                  "go": go,
                  "pd": __import__("pandas"),
                  "__name__": "__main__"
            }
            exec(plot_code, exec_globals)

        if 'browser' in pio.renderers.default.lower():
            logger.info("[Tool: plot_code] Browser renderer detected. Sleeping for 30 seconds to allow plot viewing...")
            import time
            time.sleep(30)
            logger.info("[Tool: plot_code] Diagnostic sleep finished.")
       
        return "Chart generation attempted. If successful, it should have opened in your browser."

    except Exception as e:
        logger.exception("[Tool: plot_code] Error executing LLM graph code")
        return f"⚠️ Error executing LLM graph code: {e}"


TOOLS = [
    Tool(name="list_tables",
         func=lambda _: list_tables_tool(),
         description="Lists all available tables in the database. Takes no arguments."),
    Tool(name="describe_table",
         func=describe_table_tool,
         description="Describes the schema (columns and their types) of a specific table. Requires a 'table_name' argument.",
         args_schema=DescribeTableArgs),
    Tool(name="find_similar_table",
         func=find_similar_table,
         description="Suggests table names that might contain a column similar to the provided hint. Requires a 'column_hint' argument (e.g., 'customer name', 'order date').",
         args_schema=FindSimilarTableArgs),
    Tool(name="db_query_tool",
         func=db_query_tool,
         description="Executes a given SQL query against the database and returns the results. Requires a 'query' argument containing the SQL string.",
         args_schema=DBQueryArgs),
]

PLOT_TOOL = Tool(name="plot_data", func=plot_code_with_llm, description="Plot query results")
