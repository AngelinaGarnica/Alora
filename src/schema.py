from typing import Any, Optional
from pydantic import BaseModel

class DBQueryArgs(BaseModel):
    query: str

class DescribeTableArgs(BaseModel):
    table_name: str
    
class FindSimilarTableArgs(BaseModel):
    column_hint: str

class AgentState(BaseModel):
    raw_query: str
    query: str = ""
    result: Any = None
    approved: bool = False
    plot_confirm: bool = False
    next: Optional[str] = None