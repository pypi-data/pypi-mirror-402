#!/usr/bin/env python3
"""
Tests for MSSQL MCP Server
"""

import os
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from src.server import MSSQLServer


class TestMSSQLServer:
    """Test cases for MSSQLServer class."""

    def test_build_connection_string_with_credentials(self):
        """Test connection string building with username/password."""
        with patch.dict(os.environ, {
            'MSSQL_SERVER': 'testserver',
            'MSSQL_DATABASE': 'testdb',
            'MSSQL_USER': 'testuser',
            'MSSQL_PASSWORD': 'testpass',
            'MSSQL_PORT': '1433',
            'MSSQL_DRIVER': '{ODBC Driver 17 for SQL Server}'
        }):
            server = MSSQLServer()
            conn_str = server.connection_string
            
            assert 'SERVER=testserver,1433' in conn_str
            assert 'DATABASE=testdb' in conn_str
            assert 'UID=testuser' in conn_str
            assert 'PWD=testpass' in conn_str
            assert 'DRIVER={ODBC Driver 17 for SQL Server}' in conn_str

    def test_build_connection_string_missing_required(self):
        """Test connection string building with missing required variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="MSSQL_SERVER and MSSQL_DATABASE must be set"):
                MSSQLServer()

    @patch('src.server.pyodbc.connect')
    def test_get_connection_success(self, mock_connect):
        """Test successful database connection."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        with patch.dict(os.environ, {
            'MSSQL_SERVER': 'testserver',
            'MSSQL_DATABASE': 'testdb'
        }):
            server = MSSQLServer()
            connection = server._get_connection()
            
            assert connection == mock_connection
            mock_connect.assert_called_once()

    @patch('src.server.pyodbc.connect')
    def test_get_connection_failure(self, mock_connect):
        """Test database connection failure."""
        mock_connect.side_effect = Exception("Connection failed")
        
        with patch.dict(os.environ, {
            'MSSQL_SERVER': 'testserver',
            'MSSQL_DATABASE': 'testdb'
        }):
            server = MSSQLServer()
            
            with pytest.raises(Exception, match="Connection failed"):
                server._get_connection()

    @pytest.mark.asyncio
    async def test_execute_read_query_valid(self):
        """Test executing a valid SELECT query."""
        with patch.dict(os.environ, {
            'MSSQL_SERVER': 'testserver',
            'MSSQL_DATABASE': 'testdb'
        }):
            server = MSSQLServer()
            
            # Mock database connection and cursor
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [('John', 25), ('Jane', 30)]
            mock_cursor.description = [('name',), ('age',)]
            
            with patch.object(server, '_get_connection', return_value=mock_connection):
                result = await server._execute_read_query("SELECT name, age FROM users")
                
                assert len(result) == 1
                assert "name,age" in result[0].text
                assert "John,25" in result[0].text
                assert "Jane,30" in result[0].text

    @pytest.mark.asyncio
    async def test_execute_read_query_invalid(self):
        """Test executing an invalid query (not SELECT)."""
        with patch.dict(os.environ, {
            'MSSQL_SERVER': 'testserver',
            'MSSQL_DATABASE': 'testdb'
        }):
            server = MSSQLServer()
            
            with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
                await server._execute_read_query("DELETE FROM users")

    @pytest.mark.asyncio
    async def test_execute_write_query_valid(self):
        """Test executing a valid INSERT query."""
        with patch.dict(os.environ, {
            'MSSQL_SERVER': 'testserver',
            'MSSQL_DATABASE': 'testdb'
        }):
            server = MSSQLServer()
            
            # Mock database connection and cursor
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.rowcount = 1
            
            with patch.object(server, '_get_connection', return_value=mock_connection):
                result = await server._execute_write_query("INSERT INTO users (name) VALUES ('Test')")
                
                assert len(result) == 1
                assert "1 rows affected" in result[0].text
                mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tables(self):
        """Test listing database tables."""
        with patch.dict(os.environ, {
            'MSSQL_SERVER': 'testserver',
            'MSSQL_DATABASE': 'testdb'
        }):
            server = MSSQLServer()
            
            # Mock database connection and cursor
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [('users', 'BASE TABLE'), ('orders', 'BASE TABLE')]
            
            with patch.object(server, '_get_connection', return_value=mock_connection):
                result = await server._list_tables()
                
                assert len(result) == 1
                assert "users (BASE TABLE)" in result[0].text
                assert "orders (BASE TABLE)" in result[0].text

    @pytest.mark.asyncio
    async def test_describe_table(self):
        """Test describing a table schema."""
        with patch.dict(os.environ, {
            'MSSQL_SERVER': 'testserver',
            'MSSQL_DATABASE': 'testdb'
        }):
            server = MSSQLServer()
            
            # Mock database connection and cursor
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                ('id', 'int', 'NO', None, None),
                ('name', 'varchar', 'YES', None, 255)
            ]
            
            with patch.object(server, '_get_connection', return_value=mock_connection):
                result = await server._describe_table('users')
                
                assert len(result) == 1
                assert "Schema for table 'users'" in result[0].text
                assert "id | int | NO" in result[0].text
                assert "name | varchar | YES" in result[0].text


if __name__ == "__main__":
    pytest.main([__file__]) 