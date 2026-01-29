"""
QuestDB Integration for Time Series Database
"""

import logging
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from urllib.parse import urlencode
import json


class QuestDBIntegration:
    """
    Complete integration with QuestDB for time series data operations
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize QuestDB client

        Args:
            config: Configuration dictionary with keys:
                - host: QuestDB host (default: localhost)
                - port: QuestDB port (default: 9000)
                - username: Username (optional)
                - password: Password (optional)
                - database: Database name (optional)
                - timeout: Connection timeout in seconds (default: 30)
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 9000)
        self.username = config.get('username')
        self.password = config.get('password')
        self.database = config.get('database', 'qdb')
        self.timeout = config.get('timeout', 30)

        self.base_url = f"http://{self.host}:{self.port}"
        self.session: Optional[aiohttp.ClientSession] = None

        # Start session
        asyncio.create_task(self._create_session())

    async def _create_session(self):
        """Create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )

    async def _ensure_session(self):
        """Ensure session is available"""
        if self.session is None or self.session.closed:
            await self._create_session()

    async def _execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute SQL query via HTTP API

        Args:
            query: SQL query string

        Returns:
            Query result dictionary
        """
        await self._ensure_session()

        url = f"{self.base_url}/exec"
        params = {'query': query}

        if self.username and self.password:
            auth = aiohttp.BasicAuth(self.username, self.password)
        else:
            auth = None

        try:
            async with self.session.get(url, params=params, auth=auth) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Query failed with status {response.status}: {error_text}")

        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            raise

    async def write_data(self, measurement: str, tags: Dict[str, str],
                        fields: Dict[str, Union[float, int, str, bool]],
                        timestamp: datetime) -> bool:
        """
        Write time series data point to QuestDB

        Args:
            measurement: Table name
            tags: Tag key-value pairs (stored as symbols)
            fields: Field key-value pairs
            timestamp: Data timestamp

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare ILP (InfluxDB Line Protocol) format for QuestDB
            tags_str = ','.join([f"{k}={v}" for k, v in tags.items()])
            fields_str = ','.join([f"{k}={self._format_field_value(v)}" for k, v in fields.items()])

            # Convert timestamp to nanoseconds since epoch
            timestamp_ns = int(timestamp.timestamp() * 1_000_000_000)

            ilp_line = f"{measurement},{tags_str} {fields_str} {timestamp_ns}"

            await self._ensure_session()

            url = f"{self.base_url}/write"
            headers = {'Content-Type': 'text/plain'}

            if self.username and self.password:
                auth = aiohttp.BasicAuth(self.username, self.password)
            else:
                auth = None

            async with self.session.post(url, data=ilp_line, headers=headers, auth=auth) as response:
                if response.status == 204:  # QuestDB returns 204 for successful writes
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Write failed: {error_text}")
                    return False

        except Exception as e:
            self.logger.error(f"Error writing to QuestDB: {e}")
            return False

    def _format_field_value(self, value: Union[float, int, str, bool]) -> str:
        """
        Format field value for ILP

        Args:
            value: Field value

        Returns:
            Formatted string
        """
        if isinstance(value, str):
            # Escape quotes and wrap in quotes
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        else:
            return str(value)

    async def write_batch(self, points: List[Dict[str, Any]]) -> bool:
        """
        Write multiple data points in batch

        Args:
            points: List of point dictionaries

        Returns:
            True if successful, False otherwise
        """
        try:
            ilp_lines = []

            for point_data in points:
                measurement = point_data['measurement']
                tags = point_data.get('tags', {})
                fields = point_data.get('fields', {})
                timestamp = point_data.get('timestamp', datetime.utcnow())

                tags_str = ','.join([f"{k}={v}" for k, v in tags.items()])
                fields_str = ','.join([f"{k}={self._format_field_value(v)}" for k, v in fields.items()])
                timestamp_ns = int(timestamp.timestamp() * 1_000_000_000)

                ilp_line = f"{measurement},{tags_str} {fields_str} {timestamp_ns}"
                ilp_lines.append(ilp_line)

            # Join all lines
            batch_data = '\n'.join(ilp_lines)

            await self._ensure_session()

            url = f"{self.base_url}/write"
            headers = {'Content-Type': 'text/plain'}

            if self.username and self.password:
                auth = aiohttp.BasicAuth(self.username, self.password)
            else:
                auth = None

            async with self.session.post(url, data=batch_data, headers=headers, auth=auth) as response:
                if response.status == 204:
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Batch write failed: {error_text}")
                    return False

        except Exception as e:
            self.logger.error(f"Error in batch write: {e}")
            return False

    async def query_data(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results

        Args:
            query: SQL query string

        Returns:
            List of result records
        """
        try:
            result = await self._execute_query(query)

            if 'dataset' not in result:
                return []

            records = []
            columns = result.get('columns', [])
            dataset = result['dataset']

            for row in dataset:
                record = {}
                for i, col in enumerate(columns):
                    record[col['name']] = row[i]
                records.append(record)

            return records

        except Exception as e:
            self.logger.error(f"Query error: {e}")
            return []

    async def get_measurements(self) -> List[str]:
        """
        Get list of all tables (measurements)

        Returns:
            List of table names
        """
        query = """
        SELECT name
        FROM tables()
        WHERE name NOT LIKE 'telemetry%'
        """

        try:
            result = await self.query_data(query)
            return [row['name'] for row in result]

        except Exception as e:
            self.logger.error(f"Error getting measurements: {e}")
            return []

    async def get_columns(self, table: str) -> List[Dict[str, Any]]:
        """
        Get column information for a table

        Args:
            table: Table name

        Returns:
            List of column dictionaries
        """
        query = f"""
        SELECT column, type
        FROM table_columns('{table}')
        """

        try:
            return await self.query_data(query)

        except Exception as e:
            self.logger.error(f"Error getting columns for {table}: {e}")
            return []

    async def create_table(self, table: str, columns: Dict[str, str]) -> bool:
        """
        Create a new table with specified columns

        Args:
            table: Table name
            columns: Dictionary of column_name -> type

        Returns:
            True if successful, False otherwise
        """
        try:
            # QuestDB uses SYMBOL for tags, DOUBLE/INT for fields
            column_defs = []
            for col_name, col_type in columns.items():
                if col_name == 'timestamp':
                    continue  # timestamp is automatic
                column_defs.append(f"{col_name} {col_type.upper()}")

            columns_str = ", ".join(column_defs)

            query = f"CREATE TABLE {table} ({columns_str}) TIMESTAMP(timestamp)"

            await self._execute_query(query)
            return True

        except Exception as e:
            self.logger.error(f"Error creating table {table}: {e}")
            return False

    async def delete_data(self, table: str, start_time: datetime,
                         end_time: datetime) -> bool:
        """
        Delete data from table within time range

        Args:
            table: Table name
            start_time: Start of time range
            end_time: End of time range

        Returns:
            True if successful, False otherwise
        """
        try:
            start_str = start_time.isoformat()
            end_str = end_time.isoformat()

            query = f"""
            DELETE FROM {table}
            WHERE timestamp BETWEEN '{start_str}' AND '{end_str}'
            """

            await self._execute_query(query)
            return True

        except Exception as e:
            self.logger.error(f"Error deleting data from {table}: {e}")
            return False

    async def get_table_size(self, table: str) -> Optional[int]:
        """
        Get approximate row count for table

        Args:
            table: Table name

        Returns:
            Row count or None if error
        """
        query = f"SELECT count() FROM {table}"

        try:
            result = await self.query_data(query)
            if result:
                return result[0]['count']
            return 0

        except Exception as e:
            self.logger.error(f"Error getting table size for {table}: {e}")
            return None

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of QuestDB connection

        Returns:
            Health status dictionary
        """
        try:
            # Simple health check query
            result = await self._execute_query("SELECT 1")

            return {
                "healthy": True,
                "status": "ok",
                "version": "unknown"  # QuestDB doesn't expose version easily via HTTP
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def close(self):
        """
        Close HTTP session
        """
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("QuestDB session closed")