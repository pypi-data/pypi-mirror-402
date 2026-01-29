"""
InfluxDB Integration for Time Series Database
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.query_api import QueryApi
from influxdb_client.client.exceptions import InfluxDBError


class InfluxDBIntegration:
    """
    Complete integration with InfluxDB for time series data operations
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize InfluxDB client

        Args:
            config: Configuration dictionary with keys:
                - url: InfluxDB URL
                - token: Authentication token
                - org: Organization name
                - bucket: Default bucket name
                - timeout: Connection timeout (optional)
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.client: Optional[InfluxDBClient] = None
        self.write_api = None
        self.query_api: Optional[QueryApi] = None
        self.bucket = config.get('bucket', 'default')

        self._connect()

    def _connect(self):
        """Establish connection to InfluxDB"""
        try:
            self.client = InfluxDBClient(
                url=self.config['url'],
                token=self.config['token'],
                org=self.config['org'],
                timeout=self.config.get('timeout', 10000)
            )

            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()

            # Test connection
            self.client.health()

            self.logger.info("Successfully connected to InfluxDB")

        except Exception as e:
            self.logger.error(f"Failed to connect to InfluxDB: {e}")
            raise

    async def write_data(self, measurement: str, tags: Dict[str, str],
                        fields: Dict[str, Union[float, int, str, bool]],
                        timestamp: datetime) -> bool:
        """
        Write time series data point to InfluxDB

        Args:
            measurement: Measurement name
            tags: Tag key-value pairs
            fields: Field key-value pairs
            timestamp: Data timestamp

        Returns:
            True if successful, False otherwise
        """
        try:
            point = Point(measurement)

            # Add tags
            for tag_key, tag_value in tags.items():
                point = point.tag(tag_key, tag_value)

            # Add fields
            for field_key, field_value in fields.items():
                point = point.field(field_key, field_value)

            # Set timestamp
            point = point.time(timestamp, WritePrecision.NS)

            # Write synchronously
            self.write_api.write(bucket=self.bucket, record=point)

            return True

        except InfluxDBError as e:
            self.logger.error(f"InfluxDB write error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error writing to InfluxDB: {e}")
            return False

    async def write_batch(self, points: List[Dict[str, Any]]) -> bool:
        """
        Write multiple data points in batch

        Args:
            points: List of point dictionaries with measurement, tags, fields, timestamp

        Returns:
            True if successful, False otherwise
        """
        try:
            records = []
            for point_data in points:
                point = Point(point_data['measurement'])

                # Add tags
                for tag_key, tag_value in point_data.get('tags', {}).items():
                    point = point.tag(tag_key, tag_value)

                # Add fields
                for field_key, field_value in point_data.get('fields', {}).items():
                    point = point.field(field_key, field_value)

                # Set timestamp
                timestamp = point_data.get('timestamp', datetime.utcnow())
                point = point.time(timestamp, WritePrecision.NS)

                records.append(point)

            # Write batch
            self.write_api.write(bucket=self.bucket, record=records)

            return True

        except InfluxDBError as e:
            self.logger.error(f"InfluxDB batch write error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in batch write: {e}")
            return False

    async def query_data(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute Flux query and return results

        Args:
            query: Flux query string

        Returns:
            List of result records
        """
        try:
            result = self.query_api.query(query)

            records = []
            for table in result:
                for record in table.records:
                    records.append({
                        'measurement': record.get_measurement(),
                        'tags': dict(record.values.get('tags', {})),
                        'fields': dict(record.values.get('fields', {})),
                        'timestamp': record.get_time(),
                        'value': record.get_value()
                    })

            return records

        except InfluxDBError as e:
            self.logger.error(f"InfluxDB query error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error querying InfluxDB: {e}")
            return []

    async def get_measurements(self) -> List[str]:
        """
        Get list of all measurements in the bucket

        Returns:
            List of measurement names
        """
        query = f'''
        import "influxdata/influxdb/schema"

        schema.measurements(bucket: "{self.bucket}")
        '''

        try:
            result = self.query_api.query(query)
            measurements = []

            for table in result:
                for record in table.records:
                    measurements.append(record.get_value())

            return list(set(measurements))  # Remove duplicates

        except Exception as e:
            self.logger.error(f"Error getting measurements: {e}")
            return []

    async def get_tag_keys(self, measurement: str) -> List[str]:
        """
        Get tag keys for a measurement

        Args:
            measurement: Measurement name

        Returns:
            List of tag keys
        """
        query = f'''
        import "influxdata/influxdb/schema"

        schema.tagKeys(bucket: "{self.bucket}", predicate: (r) => r._measurement == "{measurement}")
        '''

        try:
            result = self.query_api.query(query)
            tag_keys = []

            for table in result:
                for record in table.records:
                    tag_keys.append(record.get_value())

            return tag_keys

        except Exception as e:
            self.logger.error(f"Error getting tag keys: {e}")
            return []

    async def get_field_keys(self, measurement: str) -> List[str]:
        """
        Get field keys for a measurement

        Args:
            measurement: Measurement name

        Returns:
            List of field keys
        """
        query = f'''
        import "influxdata/influxdb/schema"

        schema.fieldKeys(bucket: "{self.bucket}", predicate: (r) => r._measurement == "{measurement}")
        '''

        try:
            result = self.query_api.query(query)
            field_keys = []

            for table in result:
                for record in table.records:
                    field_keys.append(record.get_value())

            return field_keys

        except Exception as e:
            self.logger.error(f"Error getting field keys: {e}")
            return []

    async def delete_data(self, measurement: str, start_time: datetime,
                         end_time: datetime) -> bool:
        """
        Delete data from measurement within time range

        Args:
            measurement: Measurement name
            start_time: Start of time range
            end_time: End of time range

        Returns:
            True if successful, False otherwise
        """
        try:
            delete_api = self.client.delete_api()

            # Convert to RFC3339 format
            start_str = start_time.isoformat() + 'Z'
            stop_str = end_time.isoformat() + 'Z'

            delete_api.delete(
                start=start_str,
                stop=stop_str,
                predicate=f'_measurement="{measurement}"',
                bucket=self.bucket,
                org=self.config['org']
            )

            return True

        except InfluxDBError as e:
            self.logger.error(f"InfluxDB delete error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error deleting data: {e}")
            return False

    async def create_bucket(self, bucket_name: str, retention_period: Optional[str] = None) -> bool:
        """
        Create a new bucket

        Args:
            bucket_name: Name of the bucket
            retention_period: Retention period (e.g., "30d", "1w")

        Returns:
            True if successful, False otherwise
        """
        try:
            buckets_api = self.client.buckets_api()

            from influxdb_client.client.bucket import Bucket

            bucket = Bucket(
                name=bucket_name,
                retention_rules=[] if retention_period is None else [{
                    "type": "expire",
                    "everySeconds": self._parse_retention_period(retention_period)
                }],
                org_id=self.client.org
            )

            buckets_api.create_bucket(bucket)
            return True

        except InfluxDBError as e:
            self.logger.error(f"Error creating bucket: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error creating bucket: {e}")
            return False

    def _parse_retention_period(self, period: str) -> int:
        """
        Parse retention period string to seconds

        Args:
            period: Period string (e.g., "30d", "1w", "1h")

        Returns:
            Seconds
        """
        unit_multipliers = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800
        }

        if period[-1] not in unit_multipliers:
            raise ValueError(f"Invalid retention period unit: {period}")

        value = int(period[:-1])
        unit = period[-1]

        return value * unit_multipliers[unit]

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of InfluxDB connection

        Returns:
            Health status dictionary
        """
        try:
            health = self.client.health()

            return {
                "healthy": health.status == "pass",
                "status": health.status,
                "message": health.message if hasattr(health, 'message') else None,
                "version": health.version if hasattr(health, 'version') else None
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def close(self):
        """
        Close InfluxDB client connection
        """
        if self.client:
            self.client.close()
            self.logger.info("InfluxDB connection closed")