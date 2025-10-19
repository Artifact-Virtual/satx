#!/usr/bin/env python3
"""
Enhanced comprehensive test runner for SATx system
Generates extensive technical and system status reports
"""

import unittest
import sys
import os
import json
import time
import platform
import psutil
import subprocess
from pathlib import Path
from datetime import datetime
import argparse
import logging
from collections import defaultdict
import traceback
import socket
import getpass

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedTestResult(unittest.TextTestResult):
    """Enhanced test result class with detailed tracking"""

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_details = []
        self.start_times = {}
        self.end_times = {}

    def startTest(self, test):
        super().startTest(test)
        self.start_times[test] = time.time()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.end_times[test] = time.time()
        self._record_test_result(test, 'PASSED', None)

    def addError(self, test, err):
        super().addError(test, err)
        self.end_times[test] = time.time()
        self._record_test_result(test, 'ERROR', err)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.end_times[test] = time.time()
        self._record_test_result(test, 'FAILED', err)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.end_times[test] = time.time()
        self._record_test_result(test, 'SKIPPED', reason)

    def _record_test_result(self, test, status, error_info):
        """Record detailed test result information"""
        start_time = self.start_times.get(test, time.time())
        end_time = self.end_times.get(test, time.time())
        duration = end_time - start_time

        test_info = {
            'name': str(test),
            'class': test.__class__.__name__,
            'module': test.__class__.__module__,
            'status': status,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'error_info': self._format_error_info(error_info) if error_info else None
        }

        self.test_details.append(test_info)

    def _format_error_info(self, error_info):
        """Format error information for reporting"""
        if isinstance(error_info, tuple) and len(error_info) >= 2:
            exc_type, exc_value, exc_traceback = error_info
            return {
                'type': str(exc_type.__name__),
                'message': str(exc_value),
                'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            }
        elif isinstance(error_info, str):
            return {'message': error_info}
        else:
            return {'message': str(error_info)}

class SystemAnalyzer:
    """Comprehensive system analysis for reports"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent

    def get_system_info(self):
        """Get comprehensive system information"""
        return {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'hostname': socket.gethostname(),
                'user': getpass.getuser()
            },
            'hardware': self._get_hardware_info(),
            'software': self._get_software_info(),
            'project': self._get_project_info()
        }

    def _get_hardware_info(self):
        """Get hardware information"""
        try:
            return {
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'memory_percent': psutil.virtual_memory().percent,
                'disk_total': psutil.disk_usage('/').total if os.name == 'posix' else psutil.disk_usage('C:').total,
                'disk_free': psutil.disk_usage('/').free if os.name == 'posix' else psutil.disk_usage('C:').free,
                'disk_percent': psutil.disk_usage('/').percent if os.name == 'posix' else psutil.disk_usage('C:').percent
            }
        except Exception as e:
            return {'error': str(e)}

    def _get_software_info(self):
        """Get software and dependency information"""
        software_info = {
            'python_packages': self._get_python_packages(),
            'system_tools': self._check_system_tools(),
            'environment_variables': self._get_relevant_env_vars()
        }
        return software_info

    def _get_python_packages(self):
        """Get installed Python packages"""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                return {pkg['name']: pkg['version'] for pkg in packages}
            else:
                return {'error': 'Failed to get package list'}
        except Exception as e:
            return {'error': str(e)}

    def _check_system_tools(self):
        """Check for required system tools"""
        tools = ['docker', 'docker-compose', 'git', 'python', 'pip']
        tool_status = {}

        for tool in tools:
            try:
                result = subprocess.run([tool, '--version'],
                                      capture_output=True, text=True, timeout=10)
                tool_status[tool] = {
                    'installed': result.returncode == 0,
                    'version': result.stdout.strip() if result.returncode == 0 else None
                }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                tool_status[tool] = {'installed': False, 'version': None}

        return tool_status

    def _get_relevant_env_vars(self):
        """Get relevant environment variables"""
        relevant_vars = ['PATH', 'PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV']
        env_vars = {}

        for var in relevant_vars:
            env_vars[var] = os.environ.get(var, 'Not set')

        return env_vars

    def _get_project_info(self):
        """Get project-specific information"""
        project_info = {
            'root_path': str(self.project_root),
            'git_info': self._get_git_info(),
            'file_counts': self._count_project_files(),
            'config_status': self._check_config_files()
        }
        return project_info

    def _get_git_info(self):
        """Get Git repository information"""
        try:
            # Get current commit
            result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                  cwd=self.project_root, capture_output=True, text=True)
            commit = result.stdout.strip() if result.returncode == 0 else None

            # Get branch
            result = subprocess.run(['git', 'branch', '--show-current'],
                                  cwd=self.project_root, capture_output=True, text=True)
            branch = result.stdout.strip() if result.returncode == 0 else None

            # Get status
            result = subprocess.run(['git', 'status', '--porcelain'],
                                  cwd=self.project_root, capture_output=True, text=True)
            has_changes = len(result.stdout.strip()) > 0 if result.returncode == 0 else False

            return {
                'commit': commit,
                'branch': branch,
                'has_uncommitted_changes': has_changes
            }
        except Exception as e:
            return {'error': str(e)}

    def _count_project_files(self):
        """Count files by type in the project"""
        file_counts = defaultdict(int)

        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                extension = file_path.suffix.lower()
                file_counts[extension] += 1
                file_counts['total'] += 1

        return dict(file_counts)

    def _check_config_files(self):
        """Check status of configuration files"""
        config_files = [
            'configs/station.ini',
            'requirements.txt',
            'docker-compose.yml',
            'setup.sh'
        ]

        config_status = {}
        for config_file in config_files:
            file_path = self.project_root / config_file
            config_status[config_file] = {
                'exists': file_path.exists(),
                'size': file_path.stat().st_size if file_path.exists() else 0
            }

        return config_status

class ComprehensiveTestReporter:
    """Generate comprehensive technical and system status reports"""

    def __init__(self, reports_dir):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_comprehensive_report(self, test_result, test_paths, system_info):
        """Generate comprehensive report with all details"""

        # Create timestamp for report files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Generate different report formats
        self._generate_json_report(test_result, test_paths, system_info, timestamp)
        self._generate_html_report(test_result, test_paths, system_info, timestamp)
        self._generate_summary_report(test_result, test_paths, system_info, timestamp)
        self._generate_detailed_log(test_result, test_paths, system_info, timestamp)

        return {
            'json_report': self.reports_dir / f'comprehensive_report_{timestamp}.json',
            'html_report': self.reports_dir / f'system_status_{timestamp}.html',
            'summary_report': self.reports_dir / f'test_summary_{timestamp}.txt',
            'detailed_log': self.reports_dir / f'detailed_log_{timestamp}.log'
        }

    def _generate_json_report(self, test_result, test_paths, system_info, timestamp):
        """Generate detailed JSON report"""
        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'report_type': 'comprehensive_system_test',
                'version': '2.0'
            },
            'system_info': system_info,
            'test_summary': {
                'total_tests': test_result.testsRun,
                'passed': test_result.testsRun - len(test_result.failures) - len(test_result.errors),
                'failed': len(test_result.failures),
                'errors': len(test_result.errors),
                'skipped': len(getattr(test_result, 'skipped', [])),
                'success_rate': self._calculate_success_rate(test_result)
            },
            'test_details': test_result.test_details,
            'test_files': [str(p) for p in test_paths],
            'performance_metrics': self._calculate_performance_metrics(test_result),
            'recommendations': self._generate_recommendations(test_result, system_info)
        }

        json_file = self.reports_dir / f'comprehensive_report_{timestamp}.json'
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

    def _generate_html_report(self, test_result, test_paths, system_info, timestamp):
        """Generate HTML status report"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SATx System Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .section {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #e8f4f8; border-radius: 5px; text-align: center; }}
        .metric.success {{ background: #d4edda; color: #155724; }}
        .metric.warning {{ background: #fff3cd; color: #856404; }}
        .metric.error {{ background: #f8d7da; color: #721c24; }}
        .test-detail {{ margin: 10px 0; padding: 10px; border-left: 4px solid #007bff; background: #f8f9fa; }}
        .test-passed {{ border-left-color: #28a745; }}
        .test-failed {{ border-left-color: #dc3545; }}
        .test-error {{ border-left-color: #ffc107; }}
        .system-info {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
        .info-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
        .progress-bar {{ width: 100%; height: 20px; background-color: #f0f0f0; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 SATx Satellite Detection System - Status Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Report ID: {timestamp}</p>
    </div>

    <div class="section">
        <h2>📊 Test Summary</h2>
        <div class="metric success">Total Tests: {test_result.testsRun}</div>
        <div class="metric success">Passed: {test_result.testsRun - len(test_result.failures) - len(test_result.errors)}</div>
        <div class="metric {'error' if len(test_result.failures) > 0 else 'success'}">Failed: {len(test_result.failures)}</div>
        <div class="metric {'error' if len(test_result.errors) > 0 else 'success'}">Errors: {len(test_result.errors)}</div>
        <div class="metric {'warning' if len(getattr(test_result, 'skipped', [])) > 0 else 'success'}">Skipped: {len(getattr(test_result, 'skipped', []))}</div>
        <div style="margin: 20px 0;">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {self._calculate_success_rate(test_result)}%; background-color: {'#28a745' if self._calculate_success_rate(test_result) >= 90 else '#ffc107' if self._calculate_success_rate(test_result) >= 75 else '#dc3545'};"></div>
            </div>
            <p style="text-align: center; margin-top: 5px;">Success Rate: {self._calculate_success_rate(test_result):.1f}%</p>
        </div>
    </div>

    <div class="section">
        <h2>🖥️ System Information</h2>
        <div class="system-info">
            <div class="info-card">
                <h3>Platform</h3>
                <p><strong>OS:</strong> {system_info['platform']['system']} {system_info['platform']['release']}</p>
                <p><strong>Python:</strong> {system_info['platform']['python_version']}</p>
                <p><strong>Host:</strong> {system_info['platform']['hostname']}</p>
            </div>
            <div class="info-card">
                <h3>Hardware</h3>
                <p><strong>CPU:</strong> {system_info['hardware'].get('cpu_count', 'N/A')} cores ({system_info['hardware'].get('cpu_percent', 'N/A'):.1f}% used)</p>
                <p><strong>Memory:</strong> {system_info['hardware'].get('memory_percent', 'N/A'):.1f}% used</p>
                <p><strong>Disk:</strong> {system_info['hardware'].get('disk_percent', 'N/A'):.1f}% used</p>
            </div>
            <div class="info-card">
                <h3>Project</h3>
                <p><strong>Files:</strong> {system_info['project']['file_counts'].get('total', 0)}</p>
                <p><strong>Python files:</strong> {system_info['project']['file_counts'].get('.py', 0)}</p>
                <p><strong>Git branch:</strong> {system_info['project']['git_info'].get('branch', 'N/A')}</p>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>🔧 Dependencies Status</h2>
        <table>
            <tr><th>Tool</th><th>Status</th><th>Version</th></tr>
"""

        for tool, info in system_info['software']['system_tools'].items():
            status = "✅ Installed" if info['installed'] else "❌ Missing"
            version = info['version'] or "N/A"
            html_content += f"<tr><td>{tool}</td><td>{status}</td><td>{version}</td></tr>"

        html_content += """
        </table>
    </div>

    <div class="section">
        <h2>🧪 Test Details</h2>
"""

        for test_detail in test_result.test_details[:50]:  # Show first 50 tests
            css_class = f"test-detail test-{'passed' if test_detail['status'] == 'PASSED' else 'failed' if test_detail['status'] == 'FAILED' else 'error'}"
            status_icon = "✅" if test_detail['status'] == 'PASSED' else "❌" if test_detail['status'] == 'FAILED' else "⚠️"
            html_content += f"""
        <div class="{css_class}">
            <strong>{status_icon} {test_detail['name']}</strong>
            <br><small>Duration: {test_detail['duration']:.3f}s | Module: {test_detail['module']}</small>
"""

            if test_detail['error_info']:
                html_content += f"<br><pre style='color: #721c24;'>{test_detail['error_info']['message'][:200]}...</pre>"

            html_content += "</div>"

        html_content += """
    </div>

    <div class="section">
        <h2>📋 Recommendations</h2>
        <ul>
"""

        recommendations = self._generate_recommendations(test_result, system_info)
        for rec in recommendations:
            html_content += f"<li>{rec}</li>"

        html_content += """
        </ul>
    </div>
</body>
</html>
"""

        html_file = self.reports_dir / f'system_status_{timestamp}.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_summary_report(self, test_result, test_paths, system_info, timestamp):
        """Generate human-readable summary report"""
        success_rate = self._calculate_success_rate(test_result)

        summary = f"""
{'='*80}
SATx COMPREHENSIVE SYSTEM STATUS REPORT
{'='*80}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Report ID: {timestamp}

SYSTEM OVERVIEW
{'-'*50}
Platform: {system_info['platform']['system']} {system_info['platform']['release']}
Python: {system_info['platform']['python_version']}
Host: {system_info['platform']['hostname']}
CPU Cores: {system_info['hardware'].get('cpu_count', 'N/A')}
Memory Usage: {system_info['hardware'].get('memory_percent', 'N/A'):.1f}%
Disk Usage: {system_info['hardware'].get('disk_percent', 'N/A'):.1f}%

TEST RESULTS SUMMARY
{'-'*50}
Total Tests: {test_result.testsRun}
Passed: {test_result.testsRun - len(test_result.failures) - len(test_result.errors)}
Failed: {len(test_result.failures)}
Errors: {len(test_result.errors)}
Skipped: {len(getattr(test_result, 'skipped', []))}
Success Rate: {success_rate:.1f}%

STATUS ASSESSMENT
{'-'*50}
"""

        if success_rate >= 95:
            summary += "🎉 EXCELLENT: System is fully operational (95%+ success rate)\n"
        elif success_rate >= 90:
            summary += "✅ VERY GOOD: System is highly operational (90%+ success rate)\n"
        elif success_rate >= 80:
            summary += "⚠️ GOOD: System is mostly operational (80%+ success rate)\n"
        elif success_rate >= 70:
            summary += "⚠️ FAIR: System needs some improvements (70%+ success rate)\n"
        elif success_rate >= 50:
            summary += "❌ POOR: System needs significant fixes (50%+ success rate)\n"
        else:
            summary += "🚨 CRITICAL: System requires immediate attention (< 50% success rate)\n"

        summary += f"""
DEPENDENCY STATUS
{'-'*50}
"""
        for tool, info in system_info['software']['system_tools'].items():
            status = "INSTALLED" if info['installed'] else "MISSING"
            version = f" ({info['version']})" if info['version'] else ""
            summary += f"{tool.upper():12}: {status}{version}\n"

        summary += f"""
PROJECT METRICS
{'-'*50}
Total Files: {system_info['project']['file_counts'].get('total', 0)}
Python Files: {system_info['project']['file_counts'].get('.py', 0)}
Git Branch: {system_info['project']['git_info'].get('branch', 'N/A')}
Uncommitted Changes: {'Yes' if system_info['project']['git_info'].get('has_uncommitted_changes') else 'No'}

RECOMMENDATIONS
{'-'*50}
"""
        recommendations = self._generate_recommendations(test_result, system_info)
        for i, rec in enumerate(recommendations, 1):
            summary += f"{i}. {rec}\n"

        summary += f"\n{'='*80}\n"

        summary_file = self.reports_dir / f'test_summary_{timestamp}.txt'
        with open(summary_file, 'w') as f:
            f.write(summary)

    def _generate_detailed_log(self, test_result, test_paths, system_info, timestamp):
        """Generate detailed log file"""
        log_content = f"""SATx Detailed Test Log - {datetime.now().isoformat()}
{'='*80}

SYSTEM INFORMATION:
{json.dumps(system_info, indent=2, default=str)}

TEST FILE LIST:
{chr(10).join(f'  - {str(p)}' for p in test_paths)}

DETAILED TEST RESULTS:
{'='*80}
"""

        for test_detail in test_result.test_details:
            log_content += f"""
Test: {test_detail['name']}
Status: {test_detail['status']}
Duration: {test_detail['duration']:.3f}s
Module: {test_detail['module']}
Timestamp: {test_detail['timestamp']}
"""

            if test_detail['error_info']:
                log_content += f"Error Info: {json.dumps(test_detail['error_info'], indent=2)}\n"

        log_file = self.reports_dir / f'detailed_log_{timestamp}.log'
        with open(log_file, 'w') as f:
            f.write(log_content)

    def _calculate_success_rate(self, test_result):
        """Calculate test success rate"""
        total_tests = test_result.testsRun
        if total_tests == 0:
            return 0.0
        successful_tests = total_tests - len(test_result.failures) - len(test_result.errors)
        return (successful_tests / total_tests) * 100

    def _calculate_performance_metrics(self, test_result):
        """Calculate performance metrics from test results"""
        if not test_result.test_details:
            return {}

        durations = [t['duration'] for t in test_result.test_details]
        return {
            'total_duration': sum(durations),
            'average_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'tests_per_second': len(test_result.test_details) / sum(durations) if sum(durations) > 0 else 0
        }

    def _generate_recommendations(self, test_result, system_info):
        """Generate system improvement recommendations"""
        recommendations = []

        success_rate = self._calculate_success_rate(test_result)

        # Success rate recommendations
        if success_rate < 90:
            recommendations.append(f"Improve test success rate (currently {success_rate:.1f}%) to reach 90%+ operational status")

        if len(test_result.failures) > 0:
            recommendations.append(f"Fix {len(test_result.failures)} failing tests to improve system reliability")

        if len(test_result.errors) > 0:
            recommendations.append(f"Resolve {len(test_result.errors)} test errors, likely indicating missing dependencies or configuration issues")

        # System tool recommendations
        missing_tools = []
        for tool, info in system_info['software']['system_tools'].items():
            if not info['installed']:
                missing_tools.append(tool)

        if missing_tools:
            recommendations.append(f"Install missing system tools: {', '.join(missing_tools)}")

        # Hardware recommendations
        if system_info['hardware'].get('memory_percent', 0) > 90:
            recommendations.append("High memory usage detected - consider increasing system RAM")

        if system_info['hardware'].get('disk_percent', 0) > 95:
            recommendations.append("Low disk space detected - free up disk space for optimal performance")

        # Project recommendations
        if system_info['project']['git_info'].get('has_uncommitted_changes'):
            recommendations.append("Commit or stash uncommitted changes to maintain clean repository state")

        # Dependency recommendations
        python_packages = system_info['software']['python_packages']
        critical_packages = ['torch', 'tensorflow', 'numpy', 'scipy', 'skyfield']
        missing_packages = []

        for package in critical_packages:
            if package not in python_packages and 'error' not in python_packages:
                missing_packages.append(package)

        if missing_packages:
            recommendations.append(f"Install missing Python packages: {', '.join(missing_packages)}")

        if not recommendations:
            recommendations.append("System is in excellent condition - no immediate recommendations")

        return recommendations

def discover_tests(test_directory):
    """Discover all test files in the given directory"""
    test_files = []
    if test_directory.exists():
        for file_path in test_directory.rglob('test_*.py'):
            if file_path.is_file():
                test_files.append(file_path)
    return test_files

def run_test_suite(test_paths, verbosity=2):
    """Run test suite and return results"""
    loader = unittest.TestLoader()

    # Load all test suites
    suite = unittest.TestSuite()
    for test_path in test_paths:
        try:
            # Convert path to module name relative to project root
            relative_path = test_path.relative_to(project_root)
            module_name = str(relative_path).replace('/', '.').replace('\\', '.').replace('.py', '')

            # Import and load tests
            __import__(module_name)
            module = sys.modules[module_name]
            suite.addTests(loader.loadTestsFromModule(module))

        except Exception as e:
            logger.error(f"Failed to load tests from {test_path}: {e}")
            continue

    # Run tests with enhanced result tracking
    runner = unittest.TextTestRunner(
        resultclass=EnhancedTestResult,
        verbosity=verbosity,
        stream=sys.stdout
    )
    result = runner.run(suite)

    return result

def main():
    parser = argparse.ArgumentParser(description='SATx Enhanced Comprehensive Test Runner')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--e2e', action='store_true', help='Run only end-to-end tests')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    parser.add_argument('--reports-dir', type=str, default='tests/reports',
                       help='Directory to save reports (default: tests/reports)')
    parser.add_argument('--verbose', '-v', action='count', default=1, help='Increase verbosity')
    parser.add_argument('--no-reports', action='store_true', help='Skip report generation')

    args = parser.parse_args()

    # Determine which tests to run
    test_paths = []

    if args.unit or args.all or (not args.unit and not args.integration and not args.e2e):
        test_paths.extend(discover_tests(project_root / 'tests' / 'unit'))

    if args.integration or args.all or (not args.unit and not args.integration and not args.e2e):
        test_paths.extend(discover_tests(project_root / 'tests' / 'integration'))

    if args.e2e or args.all or (not args.unit and not args.integration and not args.e2e):
        test_paths.extend(discover_tests(project_root / 'tests' / 'e2e'))

    if not test_paths:
        logger.error("No test files found!")
        return 1

    logger.info(f"Found {len(test_paths)} test files:")
    for path in test_paths:
        logger.info(f"  - {path}")

    logger.info(f"\nRunning tests with verbosity level {args.verbose}...")

    start_time = time.time()
    result = run_test_suite(test_paths, verbosity=args.verbose)
    end_time = time.time()

    # Get system information
    analyzer = SystemAnalyzer()
    system_info = analyzer.get_system_info()

    # Generate comprehensive reports
    if not args.no_reports:
        logger.info("\nGenerating comprehensive reports...")
        reporter = ComprehensiveTestReporter(args.reports_dir)
        report_files = reporter.generate_comprehensive_report(result, test_paths, system_info)

        logger.info("Reports generated:")
        for report_type, report_path in report_files.items():
            logger.info(f"  - {report_type}: {report_path}")

    # Calculate final metrics
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100 if result.testsRun > 0 else 0
    total_duration = end_time - start_time

    # Print final summary
    print(f"\n{'='*80}")
    print("SATx COMPREHENSIVE TEST EXECUTION COMPLETE")
    print(f"{'='*80}")
    print(f"Execution Time: {total_duration:.2f} seconds")
    print(f"Tests Run: {result.testsRun}")
    print(f"Success Rate: {success_rate:.1f}%")
    print("Target: 90%+ operational status")

    if success_rate >= 90:
        print("🎉 SUCCESS: System achieved 90%+ operational status!")
        print("✅ All requirements met - system is production-ready.")
        return 0
    elif success_rate >= 80:
        print("⚠️ NEAR SUCCESS: System is 80%+ operational but needs improvements.")
        print("🔧 Address remaining issues to reach 90%+ status.")
        return 1
    else:
        print("❌ FAILURE: System operational status is below 80%.")
        print("🔧 Critical fixes required before production deployment.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
