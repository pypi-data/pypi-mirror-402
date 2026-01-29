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
                                description=f"Data from table {table_name}",
                                mimeType="text/csv"
                            ))
                        else:
                            resources.append(Resource(
                                uri=AnyUrl(f"mssql://{table_name}/data"),
                                name=f"View: {table_name}",
                                description=f"Data from view {table_name}",
                                mimeType="text/csv"
                            ))
                    
                    return resources
            except Exception as e:
                logger.error(f"Error listing resources: {e}")
                return []

        @self.server.read_resource()
        async def read_resource(uri: AnyUrl) -> str:
            """Read data from a table or view."""
            try:
                table_name = uri.path.split('/')[-2]
                
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM [{table_name}]")
                    
                    rows = cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    
                    # Convert to CSV format
                    import csv
                    import io
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(columns)
                    writer.writerows(rows)
                    
                    return output.getvalue()
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                raise

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
                                "description": "SELECT query to execute"
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
                                "description": "INSERT, UPDATE, or DELETE query to execute"
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
                                "description": "CREATE TABLE query to execute"
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
                                "description": "CREATE PROCEDURE script to execute"
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
                                "description": "ALTER PROCEDURE script to execute"
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
                                "description": "Name of the procedure to delete"
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
                                "description": "Name of the procedure to describe"
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
                                "description": "Name of the procedure to execute"
                            },
                            "parameters": {
                                "type": "array",
                                "description": "Array of parameters to pass to the procedure",
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
                                "description": "Name of the procedure"
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
                                "description": "CREATE VIEW script to execute"
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
                                "description": "ALTER VIEW script to execute"
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
                                "description": "Optional: name of table to filter indexes"
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
                                "description": "Name of the index"
                            },
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table"
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
                                "description": "CREATE INDEX script to execute"
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
                                "description": "Name of the index"
                            },
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table"
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
                                "description": "Optional: name of schema to filter objects"
                            }
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    if name == "read_query":
                        query = arguments.get("query")
                        cursor.execute(query)
                        rows = cursor.fetchall()
                        columns = [column[0] for column in cursor.description]
                        
                        result = []
                        for row in rows:
                            row_dict = {}
                            for i, col in enumerate(columns):
                                row_dict[col] = str(row[i]) if row[i] is not None else None
                            result.append(row_dict)
                        
                        return [TextContent(
                            type="text",
                            text=f"Query executed successfully. Results: {len(result)} rows\n{result}"
                        )]
                    
                    elif name == "write_query":
                        query = arguments.get("query")
                        cursor.execute(query)
                        conn.commit()
                        
                        return [TextContent(
                            type="text",
                            text=f"Query executed successfully. Rows affected: {cursor.rowcount}"
                        )]
                    
                    elif name == "list_tables":
                        cursor.execute("""
                            SELECT TABLE_NAME 
                            FROM INFORMATION_SCHEMA.TABLES 
                            WHERE TABLE_TYPE = 'BASE TABLE'
                            ORDER BY TABLE_NAME
                        """)
                        tables = [row[0] for row in cursor.fetchall()]
                        
                        return [TextContent(
                            type="text",
                            text=f"Tables: {', '.join(tables)}"
                        )]
                    
                    elif name == "describe_table":
                        table_name = arguments.get("table_name")
                        cursor.execute(f"""
                            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                            FROM INFORMATION_SCHEMA.COLUMNS
                            WHERE TABLE_NAME = '{table_name}'
                            ORDER BY ORDINAL_POSITION
                        """)
                        columns = cursor.fetchall()
                        
                        result = []
                        for col in columns:
                            result.append({
                                "name": col[0],
                                "type": col[1],
                                "nullable": col[2],
                                "default": col[3]
                            })
                        
                        return [TextContent(
                            type="text",
                            text=f"Table schema: {result}"
                        )]
                    
                    elif name == "create_table":
                        query = arguments.get("query")
                        cursor.execute(query)
                        conn.commit()
                        
                        return [TextContent(
                            type="text",
                            text="Table created successfully"
                        )]
                    
                    elif name == "create_procedure":
                        procedure_script = arguments.get("procedure_script")
                        cursor.execute(procedure_script)
                        conn.commit()
                        
                        return [TextContent(
                            type="text",
                            text="Stored procedure created successfully"
                        )]
                    
                    elif name == "modify_procedure":
                        procedure_script = arguments.get("procedure_script")
                        cursor.execute(procedure_script)
                        conn.commit()
                        
                        return [TextContent(
                            type="text",
                            text="Stored procedure modified successfully"
                        )]
                    
                    elif name == "delete_procedure":
                        procedure_name = arguments.get("procedure_name")
                        cursor.execute(f"DROP PROCEDURE [{procedure_name}]")
                        conn.commit()
                        
                        return [TextContent(
                            type="text",
                            text=f"Stored procedure '{procedure_name}' deleted successfully"
                        )]
                    
                    elif name == "list_procedures":
                        cursor.execute("""
                            SELECT ROUTINE_NAME, ROUTINE_TYPE
                            FROM INFORMATION_SCHEMA.ROUTINES
                            WHERE ROUTINE_TYPE = 'PROCEDURE'
                            ORDER BY ROUTINE_NAME
                        """)
                        procedures = cursor.fetchall()
                        
                        result = []
                        for proc in procedures:
                            result.append({
                                "name": proc[0],
                                "type": proc[1]
                            })
                        
                        return [TextContent(
                            type="text",
                            text=f"Stored procedures: {result}"
                        )]
                    
                    elif name == "describe_procedure":
                        procedure_name = arguments.get("procedure_name")
                        cursor.execute(f"""
                            SELECT ROUTINE_DEFINITION
                            FROM INFORMATION_SCHEMA.ROUTINES
                            WHERE ROUTINE_NAME = '{procedure_name}'
                            AND ROUTINE_TYPE = 'PROCEDURE'
                        """)
                        result = cursor.fetchone()
                        
                        if result:
                            definition = result[0]
                            return [TextContent(
                                type="text",
                                text=f"Procedure definition:\n{definition}"
                            )]
                        else:
                            return [TextContent(
                                type="text",
                                text=f"Procedure '{procedure_name}' not found"
                            )]
                    
                    elif name == "execute_procedure":
                        procedure_name = arguments.get("procedure_name")
                        parameters = arguments.get("parameters", [])
                        
                        param_placeholders = ", ".join(["?" for _ in parameters])
                        query = f"EXEC [{procedure_name}] {param_placeholders}"
                        
                        cursor.execute(query, parameters)
                        rows = cursor.fetchall()
                        
                        if rows:
                            columns = [column[0] for column in cursor.description]
                            result = []
                            for row in rows:
                                row_dict = {}
                                for i, col in enumerate(columns):
                                    row_dict[col] = str(row[i]) if row[i] is not None else None
                                result.append(row_dict)
                            
                            return [TextContent(
                                type="text",
                                text=f"Procedure executed successfully. Results: {result}"
                            )]
                        else:
                            return [TextContent(
                                type="text",
                                text="Procedure executed successfully. No results returned."
                            )]
                    
                    elif name == "get_procedure_parameters":
                        procedure_name = arguments.get("procedure_name")
                        cursor.execute(f"""
                            SELECT PARAMETER_NAME, DATA_TYPE, PARAMETER_MODE
                            FROM INFORMATION_SCHEMA.PARAMETERS
                            WHERE SPECIFIC_NAME = '{procedure_name}'
                            ORDER BY ORDINAL_POSITION
                        """)
                        parameters = cursor.fetchall()
                        
                        result = []
                        for param in parameters:
                            result.append({
                                "name": param[0],
                                "type": param[1],
                                "mode": param[2]
                            })
                        
                        return [TextContent(
                            type="text",
                            text=f"Procedure parameters: {result}"
                        )]
                    
                    elif name == "list_views":
                        cursor.execute("""
                            SELECT TABLE_NAME
                            FROM INFORMATION_SCHEMA.VIEWS
                            ORDER BY TABLE_NAME
                        """)
                        views = [row[0] for row in cursor.fetchall()]
                        
                        return [TextContent(
                            type="text",
                            text=f"Views: {', '.join(views)}"
                        )]
                    
                    elif name == "describe_view":
                        view_name = arguments.get("view_name")
                        cursor.execute(f"""
                            SELECT VIEW_DEFINITION
                            FROM INFORMATION_SCHEMA.VIEWS
                            WHERE TABLE_NAME = '{view_name}'
                        """)
                        result = cursor.fetchone()
                        
                        if result:
                            definition = result[0]
                            return [TextContent(
                                type="text",
                                text=f"View definition:\n{definition}"
                            )]
                        else:
                            return [TextContent(
                                type="text",
                                text=f"View '{view_name}' not found"
                            )]
                    
                    elif name == "create_view":
                        view_script = arguments.get("view_script")
                        cursor.execute(view_script)
                        conn.commit()
                        
                        return [TextContent(
                            type="text",
                            text="View created successfully"
                        )]
                    
                    elif name == "modify_view":
                        view_script = arguments.get("view_script")
                        cursor.execute(view_script)
                        conn.commit()
                        
                        return [TextContent(
                            type="text",
                            text="View modified successfully"
                        )]
                    
                    elif name == "delete_view":
                        view_name = arguments.get("view_name")
                        cursor.execute(f"DROP VIEW [{view_name}]")
                        conn.commit()
                        
                        return [TextContent(
                            type="text",
                            text=f"View '{view_name}' deleted successfully"
                        )]
                    
                    elif name == "list_indexes":
                        table_name = arguments.get("table_name")
                        if table_name:
                            cursor.execute(f"""
                                SELECT i.name AS index_name, i.type_desc, i.is_unique
                                FROM sys.indexes i
                                INNER JOIN sys.tables t ON i.object_id = t.object_id
                                WHERE t.name = '{table_name}'
                                AND i.name IS NOT NULL
                                ORDER BY i.name
                            """)
                        else:
                            cursor.execute("""
                                SELECT i.name AS index_name, t.name AS table_name, i.type_desc, i.is_unique
                                FROM sys.indexes i
                                INNER JOIN sys.tables t ON i.object_id = t.object_id
                                WHERE i.name IS NOT NULL
                                ORDER BY t.name, i.name
                            """)
                        
                        indexes = cursor.fetchall()
                        columns = [column[0] for column in cursor.description]
                        
                        result = []
                        for idx in indexes:
                            row_dict = {}
                            for i, col in enumerate(columns):
                                row_dict[col] = idx[i]
                            result.append(row_dict)
                        
                        return [TextContent(
                            type="text",
                            text=f"Indexes: {result}"
                        )]
                    
                    elif name == "describe_index":
                        index_name = arguments.get("index_name")
                        table_name = arguments.get("table_name")
                        cursor.execute(f"""
                            SELECT i.name AS index_name, i.type_desc, i.is_unique, i.is_primary_key
                            FROM sys.indexes i
                            INNER JOIN sys.tables t ON i.object_id = t.object_id
                            WHERE i.name = '{index_name}'
                            AND t.name = '{table_name}'
                        """)
                        result = cursor.fetchone()
                        
                        if result:
                            return [TextContent(
                                type="text",
                                text=f"Index info: {result}"
                            )]
                        else:
                            return [TextContent(
                                type="text",
                                text=f"Index '{index_name}' not found on table '{table_name}'"
                            )]
                    
                    elif name == "create_index":
                        index_script = arguments.get("index_script")
                        cursor.execute(index_script)
                        conn.commit()
                        
                        return [TextContent(
                            type="text",
                            text="Index created successfully"
                        )]
                    
                    elif name == "delete_index":
                        index_name = arguments.get("index_name")
                        table_name = arguments.get("table_name")
                        cursor.execute(f"DROP INDEX [{index_name}] ON [{table_name}]")
                        conn.commit()
                        
                        return [TextContent(
                            type="text",
                            text=f"Index '{index_name}' deleted successfully"
                        )]
                    
                    elif name == "list_schemas":
                        cursor.execute("""
                            SELECT schema_name
                            FROM information_schema.schemata
                            WHERE schema_name NOT IN ('sys', 'INFORMATION_SCHEMA')
                            ORDER BY schema_name
                        """)
                        schemas = [row[0] for row in cursor.fetchall()]
                        
                        return [TextContent(
                            type="text",
                            text=f"Schemas: {', '.join(schemas)}"
                        )]
                    
                    elif name == "list_all_objects":
                        schema_name = arguments.get("schema_name")
                        
                        if schema_name:
                            cursor.execute(f"""
                                SELECT 'Table' AS object_type, TABLE_NAME AS object_name
                                FROM INFORMATION_SCHEMA.TABLES
                                WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_TYPE = 'BASE TABLE'
                                UNION ALL
                                SELECT 'View' AS object_type, TABLE_NAME AS object_name
                                FROM INFORMATION_SCHEMA.VIEWS
                                WHERE TABLE_SCHEMA = '{schema_name}'
                                UNION ALL
                                SELECT 'Procedure' AS object_type, ROUTINE_NAME AS object_name
                                FROM INFORMATION_SCHEMA.ROUTINES
                                WHERE ROUTINE_SCHEMA = '{schema_name}' AND ROUTINE_TYPE = 'PROCEDURE'
                                ORDER BY object_type, object_name
                            """)
                        else:
                            cursor.execute("""
                                SELECT 'Table' AS object_type, TABLE_SCHEMA, TABLE_NAME AS object_name
                                FROM INFORMATION_SCHEMA.TABLES
                                WHERE TABLE_TYPE = 'BASE TABLE'
                                UNION ALL
                                SELECT 'View' AS object_type, TABLE_SCHEMA, TABLE_NAME AS object_name
                                FROM INFORMATION_SCHEMA.VIEWS
                                UNION ALL
                                SELECT 'Procedure' AS object_type, ROUTINE_SCHEMA, ROUTINE_NAME AS object_name
                                FROM INFORMATION_SCHEMA.ROUTINES
                                WHERE ROUTINE_TYPE = 'PROCEDURE'
                                ORDER BY object_type, TABLE_SCHEMA, object_name
                            """)
                        
                        objects = cursor.fetchall()
                        
                        return [TextContent(
                            type="text",
                            text=f"Database objects: {objects}"
                        )]
                    
                    else:
                        return [TextContent(
                            type="text",
                            text=f"Unknown tool: {name}"
                        )]
                        
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]

    async def run(self):
        """Run the server."""
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
                        experimental_capabilities={}
                    )
                )
            )


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

def main_sync():
    """Synchronous entry point for console_scripts."""
    asyncio.run(main())

if __name__ == "__main__":
    main_sync()