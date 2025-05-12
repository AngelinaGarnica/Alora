from src.config import llm
from src.tools import TOOLS

# TOOLS
all_tools = TOOLS

# Bind tools to LLM
llm_with_tools = llm.bind(tools=all_tools)

def get_llm_agent():
    return llm_with_tools