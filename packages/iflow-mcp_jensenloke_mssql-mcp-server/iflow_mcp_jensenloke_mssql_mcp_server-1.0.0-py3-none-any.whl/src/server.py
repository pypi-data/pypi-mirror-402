#!/usr/bin/env python3
"""
MSSQL MCP Server

A Model Context Protocol server that provides access to Microsoft SQL Server databases.
Enables Language Models to inspect table schemas and execute SQL queries.
"""

import asyncio
import logging
import os
import sys
import traceback
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlparse

import pyodbc
from dotenv import load_dotenv
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import AnyUrl

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mssql-mcp-server")

class MSSQLServer:
    def __init__(self):
        self.connection_string = self._build_connection_string()
        self.server = Server("mssql-mcp-server")
        self._setup_handlers()

    def _build_connection_string(self) -> str:
        """Build MSSQL connection string from environment variables."""
        driver = os.getenv("MSSQL_DRIVER", "{ODBC Driver 17 for SQL Server}")
        server = os.getenv("MSSQL_SERVER", "localhost")
        database = os.getenv("MSSQL_DATABASE", "")
        username = os.getenv("MSSQL_USER", "")
        password = os.getenv("MSSQL_PASSWORD", "")
        port = os.getenv("MSSQL_PORT", "1433")
        trust_cert = os.getenv("TrustServerCertificate", "yes")
        trusted_conn = os.getenv("Trusted_Connection", "no")

        if not all([server, database]):
            raise ValueError("MSSQL_SERVER and MSSQL_DATABASE must be set")

        conn_str = f"DRIVER={driver};SERVER={server},{port};DATABASE={database};"
        
        if username and password:
            conn_str += f"UID={username};PWD={password};"
        
        conn_str += f"TrustServerCertificate={trust_cert};Trusted_Connection={trusted_conn};"
        
        return conn_str

    def _get_connection(self):
        """Get database connection."""
        try:
            return pyodbc.connect(self.connection_string)
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _setup_handlers(self):
        """Set up MCP handlers."""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List all available database tables as resources."""
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT TABLE_NAME, TABLE_TYPE
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_TYPE IN ('BASE TABLE', 'VIEW')
                        ORDER BY TABLE_TYPE, TABLE_NAME
                    """)
                    tables = cursor.fetchall()
                    
                    resources = []
                    for table in tables:
                        table_name = table[0]
                        table_type = table[1]
                        if table_type == 'BASE TABLE':
                            resources.append(Resource(
                                uri=AnyUrl(f"mssql://{table_name}/data"),
                                name=f"Table: {table_name}",
                                description=f"Data from {table_name} table",
                                mimeType="text/csv"
                            ))
                        else:  # VIEW
                            resources.append(Resource(
                                uri=AnyUrl(f"mssql://{table_name}/data"),
                                name=f"View: {table_name}",
                                description=f"Data from {table_name} view",
                                mimeType="text/csv"
                            ))
                    
                    return resources
            except Exception as e:
                logger.error(f"Error listing resources: {e}")
                return []

        @self.server.read_resource()
        async def read_resource(uri: AnyUrl) -> str:
            """Read data from a specific table."""
            try:
                # Parse the URI to get table name
                parsed = urlparse(str(uri))
                if parsed.scheme != "mssql":
                    raise ValueError("Invalid URI scheme")
                
                table_name = parsed.netloc
                if not table_name:
                    raise ValueError("Table name not specified in URI")

                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # Get first 100 rows
                    cursor.execute(f"SELECT TOP 100 * FROM [{table_name}]")
                    rows = cursor.fetchall()
                    
                    if not rows:
                        return "No data found"
                    
                    # Get column names
                    columns = [desc[0] for desc in cursor.description]
                    
                    # Format as CSV
                    csv_data = ",".join(columns) + "\n"
                    for row in rows:
                        csv_data += ",".join(str(cell) if cell is not None else "" for cell in row) + "\n"
                    
                    return csv_data
                    
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return f"Error: {str(e)}"

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="read_query",
                    description="Execute a SELECT query to read data from the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SELECT SQL query to execute"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="write_query",
                    description="Execute an INSERT, UPDATE, or DELETE query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query to execute (INSERT, UPDATE, DELETE)"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="list_tables",
                    description="List all tables in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="describe_table",
                    description="Get schema information for a specific table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table to describe"
                            }
                        },
                        "required": ["table_name"]
                    }
                ),
                Tool(
                    name="create_table",
                    description="Create a new table in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "CREATE TABLE SQL statement"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="create_procedure",
                    description="Create a new stored procedure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedure_script": {
                                "type": "string",
                                "description": "Complete T-SQL script to create the stored procedure (including CREATE PROCEDURE statement)"
                            }
                        },
                        "required": ["procedure_script"]
                    }
                ),
                Tool(
                    name="modify_procedure",
                    description="Modify an existing stored procedure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedure_script": {
                                "type": "string",
                                "description": "Complete T-SQL script to alter the stored procedure (using ALTER PROCEDURE statement)"
                            }
                        },
                        "required": ["procedure_script"]
                    }
                ),
                Tool(
                    name="delete_procedure",
                    description="Delete a stored procedure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedure_name": {
                                "type": "string",
                                "description": "Name of the stored procedure to delete"
                            }
                        },
                        "required": ["procedure_name"]
                    }
                ),
                Tool(
                    name="list_procedures",
                    description="List all stored procedures in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="describe_procedure",
                    description="Get detailed information about a stored procedure including its definition",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedure_name": {
                                "type": "string",
                                "description": "Name of the stored procedure to describe"
                            }
                        },
                        "required": ["procedure_name"]
                    }
                ),
                Tool(
                    name="execute_procedure",
                    description="Execute a stored procedure with optional parameters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedure_name": {
                                "type": "string",
                                "description": "Name of the stored procedure to execute"
                            },
                            "parameters": {
                                "type": "array",
                                "description": "Optional array of parameter values",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "required": ["procedure_name"]
                    }
                ),
                Tool(
                    name="get_procedure_parameters",
                    description="Get parameter information for a stored procedure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedure_name": {
                                "type": "string",
                                "description": "Name of the stored procedure to get parameters for"
                            }
                        },
                        "required": ["procedure_name"]
                    }
                ),
                Tool(
                    name="list_views",
                    description="List all views in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="describe_view",
                    description="Get detailed information about a view including its definition",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "view_name": {
                                "type": "string",
                                "description": "Name of the view to describe"
                            }
                        },
                        "required": ["view_name"]
                    }
                ),
                Tool(
                    name="create_view",
                    description="Create a new view",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "view_script": {
                                "type": "string",
                                "description": "Complete T-SQL script to create the view (including CREATE VIEW statement)"
                            }
                        },
                        "required": ["view_script"]
                    }
                ),
                Tool(
                    name="modify_view",
                    description="Modify an existing view",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "view_script": {
                                "type": "string",
                                "description": "Complete T-SQL script to alter the view (using ALTER VIEW statement)"
                            }
                        },
                        "required": ["view_script"]
                    }
                ),
                Tool(
                    name="delete_view",
                    description="Delete a view",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "view_name": {
                                "type": "string",
                                "description": "Name of the view to delete"
                            }
                        },
                        "required": ["view_name"]
                    }
                ),
                Tool(
                    name="list_indexes",
                    description="List all indexes in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Optional table name to filter indexes for a specific table"
                            }
                        }
                    }
                ),
                Tool(
                    name="describe_index",
                    description="Get detailed information about an index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "index_name": {
                                "type": "string",
                                "description": "Name of the index to describe"
                            },
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table the index belongs to"
                            }
                        },
                        "required": ["index_name", "table_name"]
                    }
                ),
                Tool(
                    name="create_index",
                    description="Create a new index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "index_script": {
                                "type": "string",
                                "description": "Complete T-SQL script to create the index (including CREATE INDEX statement)"
                            }
                        },
                        "required": ["index_script"]
                    }
                ),
                Tool(
                    name="delete_index",
                    description="Delete an index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "index_name": {
                                "type": "string",
                                "description": "Name of the index to delete"
                            },
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table the index belongs to"
                            }
                        },
                        "required": ["index_name", "table_name"]
                    }
                ),
                Tool(
                    name="list_schemas",
                    description="List all schemas in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="list_all_objects",
                    description="List all database objects (tables, views, procedures, indexes) organized by schema",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "schema_name": {
                                "type": "string",
                                "description": "Optional schema name to filter objects for a specific schema"
                            }
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute tool calls."""
            try:
                if name == "read_query":
                    return await self._execute_read_query(arguments["query"])
                elif name == "write_query":
                    return await self._execute_write_query(arguments["query"])
                elif name == "list_tables":
                    return await self._list_tables()
                elif name == "describe_table":
                    return await self._describe_table(arguments["table_name"])
                elif name == "create_table":
                    return await self._create_table(arguments["query"])
                elif name == "create_procedure":
                    return await self._create_procedure(arguments["procedure_script"])
                elif name == "modify_procedure":
                    return await self._modify_procedure(arguments["procedure_script"])
                elif name == "delete_procedure":
                    return await self._delete_procedure(arguments["procedure_name"])
                elif name == "list_procedures":
                    return await self._list_procedures()
                elif name == "describe_procedure":
                    return await self._describe_procedure(arguments["procedure_name"])
                elif name == "execute_procedure":
                    return await self._execute_procedure(arguments["procedure_name"], arguments.get("parameters"))
                elif name == "get_procedure_parameters":
                    return await self._get_procedure_parameters(arguments["procedure_name"])
                elif name == "list_views":
                    return await self._list_views()
                elif name == "describe_view":
                    return await self._describe_view(arguments["view_name"])
                elif name == "create_view":
                    return await self._create_view(arguments["view_script"])
                elif name == "modify_view":
                    return await self._modify_view(arguments["view_script"])
                elif name == "delete_view":
                    return await self._delete_view(arguments["view_name"])
                elif name == "list_indexes":
                    return await self._list_indexes(arguments.get("table_name"))
                elif name == "describe_index":
                    return await self._describe_index(arguments["index_name"], arguments["table_name"])
                elif name == "create_index":
                    return await self._create_index(arguments["index_script"])
                elif name == "delete_index":
                    return await self._delete_index(arguments["index_name"], arguments["table_name"])
                elif name == "list_schemas":
                    return await self._list_schemas()
                elif name == "list_all_objects":
                    return await self._list_all_objects(arguments.get("schema_name"))
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _execute_read_query(self, query: str) -> List[TextContent]:
        """Execute a SELECT query."""
        if not query.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed for read_query")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                return [TextContent(type="text", text="No results found")]
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Format as CSV
            csv_data = ",".join(columns) + "\n"
            for row in rows:
                csv_data += ",".join(str(cell) if cell is not None else "" for cell in row) + "\n"
            
            return [TextContent(type="text", text=csv_data)]

    async def _execute_write_query(self, query: str) -> List[TextContent]:
        """Execute an INSERT, UPDATE, DELETE, or stored procedure operation query."""
        query_upper = query.strip().upper()
        allowed_commands = ["INSERT", "UPDATE", "DELETE", "CREATE PROCEDURE", "ALTER PROCEDURE", "DROP PROCEDURE", "EXEC", "EXECUTE", "CREATE VIEW", "ALTER VIEW", "DROP VIEW", "CREATE INDEX", "DROP INDEX"]
        
        if not any(query_upper.startswith(cmd) for cmd in allowed_commands):
            raise ValueError("Only INSERT, UPDATE, DELETE, CREATE/ALTER/DROP PROCEDURE, CREATE/ALTER/DROP VIEW, CREATE/DROP INDEX, and EXEC queries are allowed for write_query")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            
            # For DDL operations, rowcount might not be meaningful
            if query_upper.startswith(("CREATE PROCEDURE", "ALTER PROCEDURE", "DROP PROCEDURE")):
                conn.commit()
                return [TextContent(type="text", text="Stored procedure operation executed successfully.")]
            elif query_upper.startswith(("CREATE VIEW", "ALTER VIEW", "DROP VIEW")):
                conn.commit()
                return [TextContent(type="text", text="View operation executed successfully.")]
            elif query_upper.startswith(("CREATE INDEX", "DROP INDEX")):
                conn.commit()
                return [TextContent(type="text", text="Index operation executed successfully.")]
            elif query_upper.startswith(("EXEC", "EXECUTE")):
                conn.commit()
                return [TextContent(type="text", text="Stored procedure executed successfully.")]
            else:
                affected_rows = cursor.rowcount
                conn.commit()
                return [TextContent(type="text", text=f"Query executed successfully. {affected_rows} rows affected.")]

    async def _list_tables(self) -> List[TextContent]:
        """List all tables in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TABLE_NAME, TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            tables = cursor.fetchall()
            
            if not tables:
                return [TextContent(type="text", text="No tables found")]
            
            result = "Tables in database:\n"
            for table in tables:
                result += f"- {table[0]} ({table[1]})\n"
            
            return [TextContent(type="text", text=result)]

    async def _describe_table(self, table_name: str) -> List[TextContent]:
        """Get schema information for a table."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """, table_name)
            columns = cursor.fetchall()
            
            if not columns:
                return [TextContent(type="text", text=f"Table '{table_name}' not found")]
            
            result = f"Schema for table '{table_name}':\n"
            result += "Column Name | Data Type | Nullable | Default | Max Length\n"
            result += "-" * 60 + "\n"
            
            for col in columns:
                max_len = str(col[4]) if col[4] else "N/A"
                result += f"{col[0]} | {col[1]} | {col[2]} | {col[3] or 'NULL'} | {max_len}\n"
            
            return [TextContent(type="text", text=result)]

    async def _create_table(self, query: str) -> List[TextContent]:
        """Create a new table."""
        if not query.strip().upper().startswith("CREATE TABLE"):
            raise ValueError("Only CREATE TABLE statements are allowed")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            
            return [TextContent(type="text", text="Table created successfully")]

    async def _create_procedure(self, procedure_script: str) -> List[TextContent]:
        """Create a new stored procedure."""
        if not procedure_script.strip().upper().startswith("CREATE PROCEDURE"):
            raise ValueError("Only CREATE PROCEDURE statements are allowed")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(procedure_script)
            conn.commit()
            
            return [TextContent(type="text", text="Procedure created successfully")]

    async def _modify_procedure(self, procedure_script: str) -> List[TextContent]:
        """Modify an existing stored procedure."""
        if not procedure_script.strip().upper().startswith("ALTER PROCEDURE"):
            raise ValueError("Only ALTER PROCEDURE statements are allowed")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(procedure_script)
            conn.commit()
            
            return [TextContent(type="text", text="Procedure modified successfully")]

    async def _delete_procedure(self, procedure_name: str) -> List[TextContent]:
        """Delete a stored procedure."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # SQL Server doesn't support IF EXISTS with parameters in this context
            cursor.execute(f"DROP PROCEDURE IF EXISTS [{procedure_name}]")
            conn.commit()
            
            return [TextContent(type="text", text=f"Procedure '{procedure_name}' deleted successfully")]

    async def _list_procedures(self) -> List[TextContent]:
        """List all stored procedures in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    o.name AS ProcedureName,
                    o.create_date AS CreatedDate,
                    o.modify_date AS ModifiedDate,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM sys.parameters p 
                            WHERE p.object_id = o.object_id
                        ) THEN 'Yes' 
                        ELSE 'No' 
                    END AS HasParameters
                FROM sys.objects o
                WHERE o.type = 'P'
                AND o.is_ms_shipped = 0  -- Exclude system procedures
                ORDER BY o.name
            """)
            procedures = cursor.fetchall()
            
            if not procedures:
                return [TextContent(type="text", text="No user-defined stored procedures found")]
            
            result = "Stored procedures in database:\n"
            result += "Name | Created | Modified | Has Parameters\n"
            result += "-" * 60 + "\n"
            
            for proc in procedures:
                created = proc[1].strftime("%Y-%m-%d") if proc[1] else "N/A"
                modified = proc[2].strftime("%Y-%m-%d") if proc[2] else "N/A"
                result += f"{proc[0]} | {created} | {modified} | {proc[3]}\n"
            
            return [TextContent(type="text", text=result)]

    async def _describe_procedure(self, procedure_name: str) -> List[TextContent]:
        """Get detailed information about a stored procedure including its definition."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    OBJECT_DEFINITION(OBJECT_ID(?)) AS ProcedureDefinition
            """, procedure_name)
            row = cursor.fetchone()
            
            if not row or not row[0]:
                return [TextContent(type="text", text=f"Procedure '{procedure_name}' not found")]
            
            definition = row[0]
            result = f"Definition for procedure '{procedure_name}':\n"
            result += "=" * 50 + "\n"
            result += definition
            
            return [TextContent(type="text", text=result)]

    async def _execute_procedure(self, procedure_name: str, parameters: Optional[List[str]] = None) -> List[TextContent]:
        """Execute a stored procedure with optional parameters."""
        if parameters is None:
            parameters = []
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Build the EXEC statement
            if parameters:
                param_placeholders = ', '.join(['?' for _ in parameters])
                exec_statement = f"EXEC [{procedure_name}] {param_placeholders}"
                cursor.execute(exec_statement, *parameters)
            else:
                cursor.execute(f"EXEC [{procedure_name}]")
            
            # Try to fetch results if any
            try:
                rows = cursor.fetchall()
                if rows:
                    # Get column names if available
                    if cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        result = f"Procedure '{procedure_name}' executed successfully.\n\nResults:\n"
                        result += ",".join(columns) + "\n"
                        for row in rows:
                            result += ",".join(str(cell) if cell is not None else "" for cell in row) + "\n"
                        return [TextContent(type="text", text=result)]
                    else:
                        return [TextContent(type="text", text=f"Procedure '{procedure_name}' executed successfully. {len(rows)} rows returned.")]
                else:
                    return [TextContent(type="text", text=f"Procedure '{procedure_name}' executed successfully. No results returned.")]
            except Exception:
                # Some procedures don't return results
                return [TextContent(type="text", text=f"Procedure '{procedure_name}' executed successfully.")]

    async def _get_procedure_parameters(self, procedure_name: str) -> List[TextContent]:
        """Get parameter information for a stored procedure."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.parameter_id,
                    p.name AS parameter_name,
                    TYPE_NAME(p.user_type_id) AS data_type,
                    p.max_length,
                    p.precision,
                    p.scale,
                    p.is_output,
                    p.has_default_value,
                    p.default_value
                FROM sys.parameters p
                INNER JOIN sys.objects o ON p.object_id = o.object_id
                WHERE o.name = ? AND o.type = 'P'
                ORDER BY p.parameter_id
            """, procedure_name)
            parameters = cursor.fetchall()
            
            if not parameters:
                return [TextContent(type="text", text=f"No parameters found for procedure '{procedure_name}' or procedure does not exist")]
            
            result = f"Parameters for procedure '{procedure_name}':\n"
            result += "ID | Name | Data Type | Length | Precision | Scale | Output | Has Default | Default Value\n"
            result += "-" * 90 + "\n"
            
            for param in parameters:
                param_id = param[0]
                name = param[1] or "(return value)"
                data_type = param[2]
                max_length = param[3] if param[3] != -1 else "MAX"
                precision = param[4] if param[4] > 0 else ""
                scale = param[5] if param[5] > 0 else ""
                is_output = "Yes" if param[6] else "No"
                has_default = "Yes" if param[7] else "No"
                default_value = param[8] if param[8] else ""
                
                result += f"{param_id} | {name} | {data_type} | {max_length} | {precision} | {scale} | {is_output} | {has_default} | {default_value}\n"
            
            return [TextContent(type="text", text=result)]

    async def _list_views(self) -> List[TextContent]:
        """List all views in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'VIEW'
                ORDER BY TABLE_NAME
            """)
            views = cursor.fetchall()
            
            if not views:
                return [TextContent(type="text", text="No views found")]
            
            result = "Views in database:\n"
            for view in views:
                result += f"- {view[0]}\n"
            
            return [TextContent(type="text", text=result)]

    async def _describe_view(self, view_name: str) -> List[TextContent]:
        """Get detailed information about a view including its definition."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT OBJECT_DEFINITION(OBJECT_ID(?)) AS ViewDefinition
            """, view_name)
            row = cursor.fetchone()
            
            if not row or not row[0]:
                return [TextContent(type="text", text=f"View '{view_name}' not found")]
            
            definition = row[0]
            result = f"Definition for view '{view_name}':\n"
            result += "=" * 50 + "\n"
            result += definition
            
            return [TextContent(type="text", text=result)]

    async def _create_view(self, view_script: str) -> List[TextContent]:
        """Create a new view."""
        if not view_script.strip().upper().startswith("CREATE VIEW"):
            raise ValueError("Only CREATE VIEW statements are allowed")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(view_script)
            conn.commit()
            
            return [TextContent(type="text", text="View created successfully")]

    async def _modify_view(self, view_script: str) -> List[TextContent]:
        """Modify an existing view."""
        if not view_script.strip().upper().startswith("ALTER VIEW"):
            raise ValueError("Only ALTER VIEW statements are allowed")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(view_script)
            conn.commit()
            
            return [TextContent(type="text", text="View modified successfully")]

    async def _delete_view(self, view_name: str) -> List[TextContent]:
        """Delete a view."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DROP VIEW IF EXISTS [{view_name}]")
            conn.commit()
            
            return [TextContent(type="text", text=f"View '{view_name}' deleted successfully")]

    async def _list_indexes(self, table_name: Optional[str] = None) -> List[TextContent]:
        """List all indexes in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if table_name:
                cursor.execute("""
                    SELECT 
                        i.name AS IndexName,
                        i.type_desc AS IndexType,
                        i.is_unique AS IsUnique,
                        i.is_primary_key AS IsPrimaryKey,
                        i.is_disabled AS IsDisabled
                    FROM sys.indexes i
                    INNER JOIN sys.objects o ON i.object_id = o.object_id
                    WHERE o.name = ? AND i.name IS NOT NULL
                    ORDER BY i.name
                """, table_name)
                
                result = f"Indexes for table '{table_name}':\n"
                result += "Name | Type | Unique | Primary Key | Disabled\n"
                result += "-" * 60 + "\n"
            else:
                cursor.execute("""
                    SELECT 
                        OBJECT_NAME(i.object_id) AS TableName,
                        i.name AS IndexName,
                        i.type_desc AS IndexType,
                        i.is_unique AS IsUnique,
                        i.is_primary_key AS IsPrimaryKey,
                        i.is_disabled AS IsDisabled
                    FROM sys.indexes i
                    INNER JOIN sys.objects o ON i.object_id = o.object_id
                    WHERE o.type = 'U' AND i.name IS NOT NULL
                    ORDER BY OBJECT_NAME(i.object_id), i.name
                """)
                
                result = "Indexes in database:\n"
                result += "Table | Index Name | Type | Unique | Primary Key | Disabled\n"
                result += "-" * 80 + "\n"
                
            indexes = cursor.fetchall()
            
            if not indexes:
                return [TextContent(type="text", text="No indexes found")]
            
            for index in indexes:
                if table_name:
                    result += f"{index[0]} | {index[1]} | {index[2]} | {index[3]} | {index[4]}\n"
                else:
                    result += f"{index[0]} | {index[1]} | {index[2]} | {index[3]} | {index[4]} | {index[5]}\n"
            
            return [TextContent(type="text", text=result)]

    async def _describe_index(self, index_name: str, table_name: str) -> List[TextContent]:
        """Get detailed information about an index."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    i.name AS IndexName,
                    i.type_desc AS IndexType,
                    i.is_unique AS IsUnique,
                    i.is_primary_key AS IsPrimaryKey,
                    i.is_disabled AS IsDisabled
                FROM sys.indexes i
                INNER JOIN sys.objects o ON i.object_id = o.object_id
                WHERE i.name = ? AND o.name = ?
            """, index_name, table_name)
            index = cursor.fetchone()
            
            if not index:
                return [TextContent(type="text", text=f"Index '{index_name}' not found in table '{table_name}'")]
            
            result = f"Index '{index_name}' in table '{table_name}':\n"
            result += "Name | Type | Unique | Primary Key | Disabled\n"
            result += "-" * 60 + "\n"
            result += f"{index[0]} | {index[1]} | {index[2]} | {index[3]} | {index[4]}\n"
            
            return [TextContent(type="text", text=result)]

    async def _create_index(self, index_script: str) -> List[TextContent]:
        """Create a new index."""
        if not index_script.strip().upper().startswith("CREATE INDEX"):
            raise ValueError("Only CREATE INDEX statements are allowed")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(index_script)
            conn.commit()
            
            return [TextContent(type="text", text="Index created successfully")]

    async def _delete_index(self, index_name: str, table_name: str) -> List[TextContent]:
        """Delete an index."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DROP INDEX IF EXISTS [{index_name}] ON [{table_name}]")
            conn.commit()
            
            return [TextContent(type="text", text=f"Index '{index_name}' in table '{table_name}' deleted successfully")]

    async def _list_schemas(self) -> List[TextContent]:
        """List all schemas in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SCHEMA_NAME(schema_id) AS SchemaName
                FROM sys.schemas
                ORDER BY SCHEMA_NAME(schema_id)
            """)
            schemas = cursor.fetchall()
            
            if not schemas:
                return [TextContent(type="text", text="No schemas found")]
            
            result = "Schemas in database:\n"
            for schema in schemas:
                result += f"- {schema[0]}\n"
            
            return [TextContent(type="text", text=result)]

    async def _list_all_objects(self, schema_name: Optional[str] = None) -> List[TextContent]:
        """List all database objects (tables, views, procedures, indexes) organized by schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if schema_name:
                cursor.execute("""
                    SELECT 
                        OBJECT_NAME(object_id) AS ObjectName,
                        type_desc AS ObjectType
                    FROM sys.objects
                    WHERE SCHEMA_NAME(schema_id) = ?
                    ORDER BY OBJECT_NAME(object_id)
                """, schema_name)
            else:
                cursor.execute("""
                    SELECT 
                        SCHEMA_NAME(schema_id) AS SchemaName,
                        OBJECT_NAME(object_id) AS ObjectName,
                        type_desc AS ObjectType
                    FROM sys.objects
                    ORDER BY SCHEMA_NAME(schema_id), OBJECT_NAME(object_id)
                """)
            objects = cursor.fetchall()
            
            if not objects:
                return [TextContent(type="text", text="No objects found")]
            
            result = "Objects in database:\n"
            for obj in objects:
                result += f"- {obj[0]} | {obj[1]} | {obj[2]}\n"
            
            return [TextContent(type="text", text=result)]

    async def run(self):
        """Run the MCP server."""
        try:
            logger.info("Starting MCP server...")
            async with stdio_server() as (read_stream, write_stream):
                logger.info("Server streams established")
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="mssql-mcp-server",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities=None,
                        ),
                    ),
                )
        except Exception as e:
            logger.error(f"Error in server run: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

async def main():
    """Main entry point."""
    try:
        logger.info("Initializing MSSQL MCP Server...")
        server = MSSQLServer()
        logger.info("Server initialized, starting...")
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 