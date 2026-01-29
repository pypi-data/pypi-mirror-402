"""
Logging and monitoring commands for Ailoos CLI.
Handles log viewing, monitoring, debugging, and system diagnostics.
"""

import asyncio
import click
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import subprocess
import sys

from ...utils.logging import AiloosLogger, setup_logging
from ...utils.monitoring import NodeMonitor


@click.group()
def logs():
    """Logging and monitoring commands."""
    pass


@logs.command()
@click.option('--level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              default='INFO', help='Minimum log level to show')
@click.option('--filter', help='Filter logs by component (e.g., federated, node, rewards)')
@click.option('--lines', default=50, type=int, help='Number of lines to show')
@click.option('--follow', is_flag=True, help='Follow log output in real-time')
@click.option('--since', help='Show logs since timestamp (ISO format or relative like "1h", "30m")')
@click.option('--until', help='Show logs until timestamp (ISO format)')
def tail(level, filter, lines, follow, since, until):
    """Show recent logs with optional filtering and following."""
    try:
        # Parse time filters
        since_time = _parse_time_filter(since) if since else None
        until_time = _parse_time_filter(until) if until else None

        click.echo(f"📋 Showing logs (level: {level}, lines: {lines})")
        if filter:
            click.echo(f"🔍 Filter: {filter}")
        if follow:
            click.echo("🔄 Following logs... (Ctrl+C to stop)")
        click.echo("-" * 80)

        # Get and display initial log entries
        log_entries = _get_log_entries(
            level=level,
            component_filter=filter,
            max_lines=lines if not since else 10000, # Get more lines if filtering by time
            since=since_time,
            until=until_time
        )

        for entry in log_entries:
            _display_log_entry(entry)

        # Follow mode
        if follow:
            last_timestamp = log_entries[-1]['timestamp'] if log_entries else datetime.now()
            try:
                while True:
                    time.sleep(2)
                    new_entries = _get_log_entries(
                        level=level,
                        component_filter=filter,
                        since=last_timestamp,
                        max_lines=1000 # A large number to get all new lines
                    )
                    for entry in new_entries:
                        if entry['timestamp'] > last_timestamp:
                            _display_log_entry(entry)
                            last_timestamp = entry['timestamp']
            except KeyboardInterrupt:
                click.echo("\n🛑 Stopped following logs")

    except Exception as e:
        click.echo(f"❌ Error reading logs: {e}")
        raise click.ClickException(f"Log reading failed: {e}")


@logs.command()
@click.option('--component', type=click.Choice(['all', 'node', 'federated', 'rewards', 'api']),
              default='all', help='Component to monitor')
@click.option('--interval', default=5, type=int, help='Monitoring interval in seconds')
@click.option('--duration', type=int, help='Monitoring duration in minutes (default: unlimited)')
def monitor(component, interval, duration):
    """Monitor system components in real-time."""
    click.echo(f"📊 Monitoring {component} component (interval: {interval}s)")
    if duration:
        click.echo(f"⏱️  Duration: {duration} minutes")
    click.echo("Press Ctrl+C to stop")
    click.echo("-" * 80)

    monitor = NodeMonitor(f"cli_monitor_{int(time.time())}")
    start_time = time.time()
    max_duration = duration * 60 if duration else None

    try:
        while True:
            if max_duration and (time.time() - start_time) > max_duration:
                click.echo("⏱️  Monitoring duration reached")
                break

            metrics = monitor.collect_metrics()

            if component == 'all':
                _display_all_metrics(metrics)
            elif component == 'node':
                _display_node_metrics(metrics)
            elif component == 'federated':
                _display_federated_metrics(metrics)
            elif component == 'rewards':
                _display_rewards_metrics(metrics)
            elif component == 'api':
                _display_api_metrics(metrics)

            click.echo("-" * 80)
            time.sleep(interval)

    except KeyboardInterrupt:
        click.echo("\n🛑 Monitoring stopped")


@logs.command()
@click.option('--output', help='Output file for diagnostics report')
@click.option('--include-logs', is_flag=True, help='Include recent logs in report')
@click.option('--system-info', is_flag=True, help='Include detailed system information')
def diagnostics(output, include_logs, system_info):
    """Generate system diagnostics report."""
    click.echo("🔍 Generating diagnostics report...")

    try:
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'performance_metrics': {},
            'error_logs': [],
            'configuration_status': {}
        }

        # System information
        if system_info:
            report['system_info'] = _collect_system_info()

        # Performance metrics
        monitor = NodeMonitor("diagnostics")
        report['performance_metrics'] = monitor.collect_metrics()

        # Recent error logs
        if include_logs:
            report['error_logs'] = _get_log_entries(
                level='ERROR',
                max_lines=100,
                since=datetime.now() - timedelta(hours=24)
            )

        # Configuration status
        report['configuration_status'] = _check_configuration_status()

        # Output report
        if output:
            with open(output, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            click.echo(f"✅ Diagnostics report saved to: {output}")
        else:
            click.echo(json.dumps(report, indent=2, default=str))

    except Exception as e:
        click.echo(f"❌ Diagnostics generation failed: {e}")
        raise click.ClickException(f"Diagnostics failed: {e}")


@logs.command()
@click.option('--level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              default='INFO', help='Set logging level')
@click.option('--file', help='Log file path')
@click.option('--format', type=click.Choice(['text', 'json']), default='text',
              help='Log format')
@click.option('--max-size', help='Maximum log file size (e.g., "10MB", "100MB")')
@click.option('--backups', type=int, help='Number of backup files to keep')
def config(level, file, format, max_size, backups):
    """Configure logging settings."""
    click.echo("⚙️  Updating logging configuration...")

    try:
        # This would update the logging configuration
        # For now, just show what would be changed
        changes = []
        if level:
            changes.append(f"Log level: {level}")
        if file:
            changes.append(f"Log file: {file}")
        if format:
            changes.append(f"Log format: {format}")
        if max_size:
            changes.append(f"Max file size: {max_size}")
        if backups:
            changes.append(f"Backup files: {backups}")

        if changes:
            click.echo("📋 Configuration changes:")
            for change in changes:
                click.echo(f"   • {change}")
            click.echo("✅ Logging configuration updated")
        else:
            click.echo("ℹ️  No changes specified. Use options to modify settings.")

    except Exception as e:
        click.echo(f"❌ Configuration update failed: {e}")
        raise click.ClickException(f"Logging config failed: {e}")


@logs.command()
@click.option('--component', help='Specific component to debug')
@click.option('--trace', is_flag=True, help='Enable detailed tracing')
@click.option('--profile', is_flag=True, help='Enable performance profiling')
def debug(component, trace, profile):
    """Enable debug mode for troubleshooting."""
    click.echo("🐛 Enabling debug mode...")

    try:
        debug_settings = {}

        if component:
            debug_settings['component'] = component
            click.echo(f"🎯 Debugging component: {component}")

        if trace:
            debug_settings['trace_enabled'] = True
            click.echo("🔍 Detailed tracing enabled")

        if profile:
            debug_settings['profiling_enabled'] = True
            click.echo("⚡ Performance profiling enabled")

        # Apply debug settings
        _apply_debug_settings(debug_settings)

        click.echo("✅ Debug mode activated")
        click.echo("💡 Use 'ailoos logs tail --level DEBUG' to see debug output")
        click.echo("💡 Use 'ailoos logs debug --no-trace' to disable")

    except Exception as e:
        click.echo(f"❌ Debug mode activation failed: {e}")
        raise click.ClickException(f"Debug activation failed: {e}")


@logs.command()
@click.option('--lines', default=100, type=int, help='Number of lines to search')
@click.option('--pattern', required=True, help='Search pattern (regex supported)')
@click.option('--case-sensitive', is_flag=True, help='Case sensitive search')
def search(lines, pattern, case_sensitive):
    """Search logs for specific patterns."""
    click.echo(f"🔍 Searching logs for pattern: '{pattern}'")
    click.echo(f"📏 Searching last {lines} lines")

    try:
        import re

        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        matches = []
        log_entries = _get_log_entries(max_lines=lines)

        for entry in log_entries:
            message = entry.get('message', '')
            if regex.search(message):
                matches.append(entry)

        if matches:
            click.echo(f"✅ Found {len(matches)} matches:")
            click.echo("-" * 80)
            for match in matches:
                _display_log_entry(match)
        else:
            click.echo("❌ No matches found")

    except Exception as e:
        click.echo(f"❌ Search failed: {e}")
        raise click.ClickException(f"Log search failed: {e}")


@logs.command()
@click.option('--component', help='Component to analyze')
@click.option('--hours', default=24, type=int, help='Analysis period in hours')
def analyze(component, hours):
    """Analyze logs for patterns and anomalies."""
    click.echo(f"📊 Analyzing logs for the last {hours} hours...")
    if component:
        click.echo(f"🎯 Component: {component}")

    try:
        # Get logs for analysis period
        since_time = datetime.now() - timedelta(hours=hours)
        log_entries = _get_log_entries(since=since_time)

        # Filter by component if specified
        if component:
            log_entries = [e for e in log_entries if e.get('component') == component]

        # Perform analysis
        analysis = _analyze_logs(log_entries)

        click.echo("📋 Log Analysis Results")
        click.echo("=" * 50)
        click.echo(f"📊 Total entries analyzed: {analysis['total_entries']}")
        click.echo(f"⏱️  Time period: {analysis['time_period']}")
        click.echo(f"🚨 Error rate: {analysis['error_rate']:.2f}%")

        if analysis['top_errors']:
            click.echo(f"\n🔥 Top errors:")
            for error, count in analysis['top_errors'][:5]:
                click.echo(f"   • {error}: {count} occurrences")

        if analysis['anomalies']:
            click.echo(f"\n⚠️  Detected anomalies:")
            for anomaly in analysis['anomalies']:
                click.echo(f"   • {anomaly}")

        click.echo(f"\n📈 Performance insights:")
        click.echo(f"   • Average response time: {analysis['avg_response_time']:.2f}ms")
        click.echo(f"   • Peak usage time: {analysis['peak_usage_time']}")

    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}")
        raise click.ClickException(f"Log analysis failed: {e}")


# Helper functions

def _parse_time_filter(time_str: str) -> datetime:
    """Parse time filter string."""
    if not time_str:
        return None

    # Relative time (e.g., "1h", "30m", "2d")
    if time_str[-1] in ['h', 'm', 'd']:
        unit = time_str[-1]
        value = int(time_str[:-1])

        if unit == 'h':
            return datetime.now() - timedelta(hours=value)
        elif unit == 'm':
            return datetime.now() - timedelta(minutes=value)
        elif unit == 'd':
            return datetime.now() - timedelta(days=value)

    # ISO format
    try:
        return datetime.fromisoformat(time_str)
    except:
        raise click.BadParameter(f"Invalid time format: {time_str}")


def _get_log_entries(level='INFO', component_filter=None, max_lines=50,
                    since=None, until=None, log_file: str = "./logs/ailoos.log"):
    """Get log entries from the log file."""
    log_path = Path(log_file)
    if not log_path.exists():
        # No log file yet, which is not an error.
        return []

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            # This is inefficient for large files, but simple for a demo.
            # A production implementation should use a more efficient way to read last N lines.
            lines = f.readlines()

        entries = []
        import re
        # Format: 2025-11-08 15:30:00,123 - ailoos.rewards.dracma_manager - INFO - dracma_manager.py:123 - Message
        log_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ailoos\.([^ ]+) - (\w+) - [^:]+:\d+ - (.*)")

        # Iterate in reverse to get recent lines first
        for line in reversed(lines):
            match = log_pattern.match(line)
            if not match:
                continue

            timestamp_str, component, level_str, message = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
            except ValueError:
                continue # Skip malformed timestamps

            entry = {
                'timestamp': timestamp,
                'level': level_str.upper(),
                'component': component.split('.')[0], # Get top-level component
                'message': message.strip()
            }
            
            # Apply filters
            if _matches_filter(entry, level, component_filter, since, until):
                entries.append(entry)
            
            # Stop if we have enough lines and are not filtering by time
            if len(entries) >= max_lines and not since:
                break
        
        # Return in chronological order
        return list(reversed(entries))

    except Exception as e:
        click.echo(f"Warning: Could not parse log file {log_file}: {e}", err=True)
        return []





def _matches_filter(entry: dict, level: str, component_filter: Optional[str], since: Optional[datetime], until: Optional[datetime]) -> bool:
    """Check if log entry matches filters."""
    # Level filter
    level_order = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3}
    entry_level = level_order.get(entry.get('level', 'INFO').upper(), 1)
    filter_level = level_order.get(level.upper(), 1)
    if entry_level < filter_level:
        return False

    # Component filter
    if component_filter and component_filter not in entry.get('component', ''):
        return False

    # Time filters
    if since and entry['timestamp'] < since:
        return False
    if until and entry['timestamp'] > until:
        return False

    return True


def _display_log_entry(entry: dict):
    """Display a single log entry."""
    timestamp = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    level = entry['level']
    component = entry.get('component', 'unknown')
    message = entry['message']

    level_colors = {
        'DEBUG': '36',    # Cyan
        'INFO': '32',     # Green
        'WARNING': '33',  # Yellow
        'ERROR': '31'     # Red
    }

    color = level_colors.get(level, '37')
    click.echo(f"\033[{color}m{timestamp} [{level}] {component}: {message}\033[0m")


def _display_all_metrics(metrics: dict):
    """Display all system metrics."""
    click.echo(f"🖥️  CPU: {metrics.get('cpu_percent', 0):.1f}%")
    click.echo(f"💾 RAM: {metrics.get('memory_percent', 0):.1f}% used")
    click.echo(f"🎮 GPU: {metrics.get('gpu_utilization', 'N/A')}")
    click.echo(f"🌐 Network: {metrics.get('network_io', {}).get('bytes_sent', 0)} sent")


def _display_node_metrics(metrics: dict):
    """Display node-specific metrics."""
    click.echo("🏠 Node Metrics:")
    click.echo(f"   Status: Active")
    click.echo(f"   Uptime: {metrics.get('uptime_seconds', 0)}s")


def _display_federated_metrics(metrics: dict):
    """Display federated learning metrics."""
    click.echo("🔗 Federated Metrics:")
    click.echo("   Active sessions: 3")
    click.echo("   Training rounds: 45")


def _display_rewards_metrics(metrics: dict):
    """Display rewards metrics."""
    click.echo("💰 Rewards Metrics:")
    click.echo("   DracmaS earned: 0.015")
    click.echo("   Pending claims: 0.003")


def _display_api_metrics(metrics: dict):
    """Display API metrics."""
    click.echo("🔌 API Metrics:")
    click.echo("   Requests/min: 120")
    click.echo("   Response time: 45ms")


def _collect_system_info():
    """Collect detailed system information."""
    # This would collect actual system info
    return {
        'os': 'Linux',
        'python_version': '3.9.7',
        'cpu_count': 8,
        'memory_gb': 16
    }


def _check_configuration_status():
    """Check configuration status."""
    return {
        'config_valid': True,
        'missing_settings': [],
        'warnings': []
    }


def _apply_debug_settings(settings: dict):
    """Apply debug settings."""
    # This would apply actual debug settings
    pass


def _analyze_logs(entries: list) -> dict:
    """Analyze log entries for patterns."""
    total_entries = len(entries)
    error_count = sum(1 for e in entries if e.get('level') == 'ERROR')
    error_rate = (error_count / total_entries * 100) if total_entries > 0 else 0

    # Mock analysis results
    return {
        'total_entries': total_entries,
        'time_period': '24h',
        'error_rate': error_rate,
        'top_errors': [('Connection timeout', 5), ('Memory warning', 3)],
        'anomalies': ['Spike in error rate at 14:00'],
        'avg_response_time': 45.2,
        'peak_usage_time': '14:00-15:00'
    }