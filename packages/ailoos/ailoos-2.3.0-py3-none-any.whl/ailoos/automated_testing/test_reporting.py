"""
Test Reporting
Advanced reporting system for test results with visualizations and analytics.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Optional imports
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


@dataclass
class TestReport:
    report_id: str
    title: str
    timestamp: datetime
    summary: Dict[str, Any]
    detailed_results: List[Dict[str, Any]]
    charts: List[str]  # File paths to generated charts
    recommendations: List[str]


class TestReporting:
    """
    Advanced test reporting system with analytics and visualizations.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.reports_dir = Path(config.get('reports_dir', 'test_reports'))
        self.reports_dir.mkdir(exist_ok=True)

        self.chart_dir = self.reports_dir / 'charts'
        self.chart_dir.mkdir(exist_ok=True)

        self.report_history: List[TestReport] = []

    async def generate_comprehensive_report(self, test_results: List[Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive test report from all test results.

        Args:
            test_results: List of test results from different test types

        Returns:
            Report data dictionary
        """
        self.logger.info("Generating comprehensive test report")

        report_id = f"report_{int(time.time())}"
        timestamp = datetime.now()

        # Analyze results by type
        analysis = self._analyze_test_results(test_results)

        # Generate charts
        charts = await self._generate_charts(test_results, report_id)

        # Generate recommendations
        recommendations = self._generate_recommendations(analysis)

        # Create report
        report = TestReport(
            report_id=report_id,
            title="Automated Testing Comprehensive Report",
            timestamp=timestamp,
            summary=analysis['summary'],
            detailed_results=analysis['detailed_results'],
            charts=charts,
            recommendations=recommendations
        )

        self.report_history.append(report)

        # Save report to file
        report_path = self.reports_dir / f"{report_id}.json"
        await self._save_report(report, report_path)

        # Generate HTML report
        html_path = self.reports_dir / f"{report_id}.html"
        await self._generate_html_report(report, html_path)

        return {
            'report_id': report_id,
            'timestamp': timestamp.isoformat(),
            'summary': analysis['summary'],
            'charts': charts,
            'recommendations': recommendations,
            'files': {
                'json': str(report_path),
                'html': str(html_path)
            }
        }

    def _analyze_test_results(self, test_results: List[Any]) -> Dict[str, Any]:
        """Analyze test results and extract key metrics."""
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if getattr(r, 'success', False))
        failed_tests = total_tests - passed_tests

        success_rate = passed_tests / total_tests if total_tests > 0 else 0

        # Group by test type if available
        test_types = {}
        total_duration = 0

        for result in test_results:
            # Extract test type
            test_type = getattr(result, 'test_type', None)
            if test_type:
                type_name = test_type.value if hasattr(test_type, 'value') else str(test_type)
                if type_name not in test_types:
                    test_types[type_name] = {'total': 0, 'passed': 0, 'failed': 0, 'duration': 0}
                test_types[type_name]['total'] += 1
                if getattr(result, 'success', False):
                    test_types[type_name]['passed'] += 1
                else:
                    test_types[type_name]['failed'] += 1
                test_types[type_name]['duration'] += getattr(result, 'duration', 0)

            total_duration += getattr(result, 'duration', 0)

        # Calculate averages and trends
        avg_duration = total_duration / total_tests if total_tests > 0 else 0

        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'total_duration': total_duration,
            'average_duration': avg_duration,
            'test_types': test_types
        }

        # Detailed results
        detailed_results = []
        for result in test_results:
            detailed_results.append(self._extract_result_details(result))

        return {
            'summary': summary,
            'detailed_results': detailed_results
        }

    def _extract_result_details(self, result: Any) -> Dict[str, Any]:
        """Extract detailed information from a test result."""
        details = {
            'test_name': getattr(result, 'name', 'Unknown'),
            'success': getattr(result, 'success', False),
            'duration': getattr(result, 'duration', 0),
            'errors': getattr(result, 'errors', [])
        }

        # Add type-specific details
        if hasattr(result, 'test_type'):
            details['test_type'] = result.test_type.value if hasattr(result.test_type, 'value') else str(result.test_type)

        # Add performance metrics if available
        if hasattr(result, 'summary'):
            details['metrics'] = result.summary

        # Add load test specifics
        if hasattr(result, 'throughput'):
            details.update({
                'throughput_rps': result.throughput,
                'error_rate': getattr(result, 'error_rate', 0),
                'total_requests': getattr(result, 'total_requests', 0)
            })

        return details

    async def _generate_charts(self, test_results: List[Any], report_id: str) -> List[str]:
        """Generate charts for the test report."""
        charts = []

        try:
            # Success rate pie chart
            success_chart = await self._generate_success_rate_chart(test_results, report_id)
            if success_chart:
                charts.append(success_chart)

            # Duration histogram
            duration_chart = await self._generate_duration_histogram(test_results, report_id)
            if duration_chart:
                charts.append(duration_chart)

            # Performance trends (if applicable)
            perf_chart = await self._generate_performance_chart(test_results, report_id)
            if perf_chart:
                charts.append(perf_chart)

            # Load test throughput chart
            throughput_chart = await self._generate_throughput_chart(test_results, report_id)
            if throughput_chart:
                charts.append(throughput_chart)

        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")

        return charts

    async def _generate_success_rate_chart(self, test_results: List[Any], report_id: str) -> Optional[str]:
        """Generate success rate pie chart."""
        if not HAS_MATPLOTLIB:
            return None

        try:
            passed = sum(1 for r in test_results if getattr(r, 'success', False))
            failed = len(test_results) - passed

            if passed + failed == 0:
                return None

            labels = ['Passed', 'Failed']
            sizes = [passed, failed]
            colors = ['#4CAF50', '#F44336']

            plt.figure(figsize=(8, 6))
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.title('Test Results Summary')
            plt.axis('equal')

            chart_path = self.chart_dir / f"{report_id}_success_rate.png"
            plt.savefig(chart_path)
            plt.close()

            return str(chart_path)

        except Exception as e:
            self.logger.error(f"Error generating success rate chart: {e}")
            return None

    async def _generate_duration_histogram(self, test_results: List[Any], report_id: str) -> Optional[str]:
        """Generate test duration histogram."""
        if not HAS_MATPLOTLIB:
            return None

        try:
            durations = [getattr(r, 'duration', 0) for r in test_results]
            if not durations:
                return None

            plt.figure(figsize=(10, 6))
            plt.hist(durations, bins=20, alpha=0.7, color='#2196F3', edgecolor='black')
            plt.xlabel('Duration (seconds)')
            plt.ylabel('Number of Tests')
            plt.title('Test Duration Distribution')
            plt.grid(True, alpha=0.3)

            chart_path = self.chart_dir / f"{report_id}_duration_histogram.png"
            plt.savefig(chart_path)
            plt.close()

            return str(chart_path)

        except Exception as e:
            self.logger.error(f"Error generating duration histogram: {e}")
            return None

    async def _generate_performance_chart(self, test_results: List[Any], report_id: str) -> Optional[str]:
        """Generate performance metrics chart."""
        if not HAS_MATPLOTLIB or not HAS_PANDAS:
            return None

        try:
            perf_data = []
            for result in test_results:
                if hasattr(result, 'summary') and 'avg_response_time' in result.summary:
                    perf_data.append({
                        'name': getattr(result, 'test_config', {}).get('name', 'Unknown'),
                        'response_time': result.summary['avg_response_time']
                    })

            if not perf_data:
                return None

            df = pd.DataFrame(perf_data)
            plt.figure(figsize=(12, 6))
            plt.bar(df['name'], df['response_time'], color='#FF9800', alpha=0.7)
            plt.xlabel('Test Scenario')
            plt.ylabel('Average Response Time (s)')
            plt.title('Performance Test Results')
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3)

            chart_path = self.chart_dir / f"{report_id}_performance.png"
            plt.savefig(chart_path, bbox_inches='tight')
            plt.close()

            return str(chart_path)

        except Exception as e:
            self.logger.error(f"Error generating performance chart: {e}")
            return None

    async def _generate_throughput_chart(self, test_results: List[Any], report_id: str) -> Optional[str]:
        """Generate load test throughput chart."""
        if not HAS_MATPLOTLIB or not HAS_PANDAS:
            return None

        try:
            throughput_data = []
            for result in test_results:
                if hasattr(result, 'throughput') and result.throughput > 0:
                    throughput_data.append({
                        'name': getattr(result, 'scenario', {}).get('name', 'Unknown'),
                        'throughput': result.throughput
                    })

            if not throughput_data:
                return None

            df = pd.DataFrame(throughput_data)
            plt.figure(figsize=(12, 6))
            plt.bar(df['name'], df['throughput'], color='#9C27B0', alpha=0.7)
            plt.xlabel('Load Test Scenario')
            plt.ylabel('Throughput (requests/second)')
            plt.title('Load Test Throughput Results')
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3)

            chart_path = self.chart_dir / f"{report_id}_throughput.png"
            plt.savefig(chart_path, bbox_inches='tight')
            plt.close()

            return str(chart_path)

        except Exception as e:
            self.logger.error(f"Error generating throughput chart: {e}")
            return None

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test analysis."""
        recommendations = []

        summary = analysis['summary']
        success_rate = summary['success_rate']

        if success_rate < 0.8:
            recommendations.append("Overall test success rate is below 80%. Investigate failing tests and fix issues.")
        elif success_rate < 0.95:
            recommendations.append("Test success rate is acceptable but could be improved. Review intermittent failures.")

        # Check for slow tests
        avg_duration = summary['average_duration']
        if avg_duration > 60:  # More than 1 minute average
            recommendations.append("Average test duration is high. Consider optimizing test execution or parallelizing tests.")

        # Check test type distribution
        test_types = summary.get('test_types', {})
        if not test_types.get('e2e'):
            recommendations.append("No E2E tests found. Consider adding end-to-end test coverage.")
        if not test_types.get('performance'):
            recommendations.append("No performance tests found. Consider adding performance benchmarking.")
        if not test_types.get('load'):
            recommendations.append("No load tests found. Consider adding load testing for capacity planning.")

        # Specific recommendations based on detailed results
        detailed_results = analysis['detailed_results']
        error_patterns = self._analyze_error_patterns(detailed_results)
        if error_patterns:
            recommendations.extend(error_patterns)

        return recommendations

    def _analyze_error_patterns(self, detailed_results: List[Dict[str, Any]]) -> List[str]:
        """Analyze error patterns in test results."""
        patterns = []

        # Check for timeout errors
        timeout_errors = sum(1 for r in detailed_results if 'timeout' in str(r.get('errors', [])).lower())
        if timeout_errors > 0:
            patterns.append(f"Found {timeout_errors} timeout errors. Consider increasing timeouts or optimizing performance.")

        # Check for connection errors
        connection_errors = sum(1 for r in detailed_results if 'connection' in str(r.get('errors', [])).lower())
        if connection_errors > 0:
            patterns.append(f"Found {connection_errors} connection errors. Check network stability and service availability.")

        return patterns

    async def _save_report(self, report: TestReport, file_path: Path) -> None:
        """Save report to JSON file."""
        report_data = {
            'report_id': report.report_id,
            'title': report.title,
            'timestamp': report.timestamp.isoformat(),
            'summary': report.summary,
            'detailed_results': report.detailed_results,
            'charts': report.charts,
            'recommendations': report.recommendations
        }

        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

    async def _generate_html_report(self, report: TestReport, file_path: Path) -> None:
        """Generate HTML report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ background: #e8f5e8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .chart {{ margin: 20px 0; text-align: center; }}
                .recommendations {{ background: #fff3cd; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .error {{ color: #dc3545; }}
                .success {{ color: #28a745; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.title}</h1>
                <p>Report ID: {report.report_id}</p>
                <p>Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="summary">
                <h2>Summary</h2>
                <p>Total Tests: {report.summary['total_tests']}</p>
                <p>Passed: <span class="success">{report.summary['passed_tests']}</span></p>
                <p>Failed: <span class="error">{report.summary['failed_tests']}</span></p>
                <p>Success Rate: {report.summary['success_rate']:.1%}</p>
                <p>Total Duration: {report.summary['total_duration']:.2f}s</p>
            </div>

            {"".join(f'<div class="chart"><img src="{chart}" alt="Chart" style="max-width: 100%;"></div>' for chart in report.charts)}

            <div class="recommendations">
                <h2>Recommendations</h2>
                <ul>
                {"".join(f"<li>{rec}</li>" for rec in report.recommendations)}
                </ul>
            </div>
        </body>
        </html>
        """

        with open(file_path, 'w') as f:
            f.write(html_content)

    async def get_report_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical reports."""
        recent_reports = self.report_history[-limit:]
        return [{
            'report_id': r.report_id,
            'title': r.title,
            'timestamp': r.timestamp.isoformat(),
            'summary': r.summary
        } for r in recent_reports]

    def get_status(self) -> Dict[str, Any]:
        """Get current status of test reporting system."""
        return {
            'reports_dir': str(self.reports_dir),
            'chart_dir': str(self.chart_dir),
            'total_reports': len(self.report_history),
            'latest_report': self.report_history[-1].report_id if self.report_history else None
        }