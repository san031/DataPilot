from database.schema_tool import get_schema
from database.sql_tool import execute_sql

def schema_tool():
    return get_schema()

def sql_tool(query: str):
    return execute_sql(query)

TOOLS = {
    "get_schema": schema_tool,
    "execute_sql": sql_tool
}