"""
Analytics Dashboard for LRDBench

Provides a unified interface for accessing all analytics data:
- Usage statistics
- Performance metrics
- Error analysis
- Workflow insights
- Report generation
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from .usage_tracker import UsageTracker, get_usage_tracker
from .performance_monitor import PerformanceMonitor, get_performance_monitor
from .error_analyzer import ErrorAnalyzer, get_error_analyzer
from .workflow_analyzer import WorkflowAnalyzer, get_workflow_analyzer


class AnalyticsDashboard:
    """
    Comprehensive analytics dashboard for LRDBench

    Provides easy access to all analytics data and generates
    comprehensive reports and visualizations, including stratified summaries.
    """

    def __init__(self, storage_path: str = "~/.lrdbench/analytics"):
        """Initialize the analytics dashboard"""
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize analytics components
        self.usage_tracker = get_usage_tracker()
        self.performance_monitor = get_performance_monitor()
        self.error_analyzer = get_error_analyzer()
        self.workflow_analyzer = get_workflow_analyzer()

        # Set plotting style
        plt.style.use("default")
        sns.set_palette("husl")

    def get_comprehensive_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive summary of all analytics data

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary containing all analytics summaries
        """
        return {
            "usage_summary": self.usage_tracker.get_usage_summary(days),
            "performance_summary": self.performance_monitor.get_performance_summary(
                days
            ),
            "error_summary": self.error_analyzer.get_error_summary(days),
            "workflow_summary": self.workflow_analyzer.get_workflow_summary(days),
            "generated_at": datetime.now().isoformat(),
            "analysis_period_days": days,
        }

    def generate_usage_report(
        self, days: int = 30, output_path: Optional[str] = None
    ) -> str:
        """Generate comprehensive usage report"""
        summary = self.usage_tracker.get_usage_summary(days)

        report = f"""
# LRDBench Usage Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Period: {days} days

## Overview
- Total Events: {summary.total_events:,}
- Unique Users: {summary.unique_users:,}
- Success Rate: {summary.success_rate:.1%}
- Average Execution Time: {summary.avg_execution_time:.3f}s

## Most Popular Estimators
"""

        for estimator, count in summary.estimator_usage.items():
            report += f"- {estimator}: {count:,} uses\n"

        report += f"""
## Parameter Usage Patterns
"""

        for param, values in summary.parameter_frequency.items():
            report += f"\n### {param}\n"
            for value, count in list(values.items())[:5]:  # Top 5 values
                report += f"- {value}: {count:,} times\n"

        report += f"""
## Data Length Distribution
"""

        for length_range, count in summary.data_length_distribution.items():
            report += f"- {length_range}: {count:,} datasets\n"

        if summary.common_errors:
            report += f"""
## Common Errors
"""
            for error, count in summary.common_errors.items()[:5]:  # Top 5 errors
                report += f"- {error}: {count:,} occurrences\n"

        if output_path:
            with open(output_path, "w") as f:
                f.write(report)

        return report

    def generate_performance_report(
        self, days: int = 30, output_path: Optional[str] = None
    ) -> str:
        """Generate comprehensive performance report"""
        summary = self.performance_monitor.get_performance_summary(days)

        report = f"""
# LRDBench Performance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Period: {days} days

## Performance Overview
- Total Executions: {summary.total_executions:,}
- Average Execution Time: {summary.avg_execution_time:.3f}s
- Execution Time Range: {summary.min_execution_time:.3f}s - {summary.max_execution_time:.3f}s
- Standard Deviation: {summary.std_execution_time:.3f}s
- Performance Trend: {summary.performance_trend}

## Memory Usage
- Average Memory Usage: {summary.avg_memory_usage:.2f} MB
- Memory Efficiency: {summary.memory_efficiency:.3f} MB/s

## Performance Bottlenecks
"""

        if summary.bottleneck_estimators:
            for estimator in summary.bottleneck_estimators:
                report += f"- {estimator}\n"
        else:
            report += "- No significant bottlenecks detected\n"

        if output_path:
            with open(output_path, "w") as f:
                f.write(report)

        return report

    def generate_reliability_report(
        self, days: int = 30, output_path: Optional[str] = None
    ) -> str:
        """Generate comprehensive reliability report"""
        error_summary = self.error_analyzer.get_error_summary(days)
        recommendations = self.error_analyzer.get_improvement_recommendations(days)

        report = f"""
# LRDBench Reliability Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Period: {days} days

## Error Overview
- Total Errors: {error_summary.total_errors:,}
- Unique Errors: {error_summary.unique_errors:,}
- Reliability Score: {error_summary.reliability_score:.1%}

## Error Distribution by Type
"""

        for error_type, count in error_summary.error_by_type.items():
            report += f"- {error_type}: {count:,} errors\n"

        report += f"""
## Error Distribution by Estimator
"""

        for estimator, count in error_summary.error_by_estimator.items():
            report += f"- {estimator}: {count:,} errors\n"

        if error_summary.error_trends:
            report += f"""
## Error Trends
"""
            for trend_key, trend_value in error_summary.error_trends.items():
                report += f"- {trend_key}: {trend_value}\n"

        if recommendations:
            report += f"""
## Improvement Recommendations
"""
            for i, recommendation in enumerate(recommendations, 1):
                report += f"{i}. {recommendation}\n"

        if output_path:
            with open(output_path, "w") as f:
                f.write(report)

        return report

    def generate_workflow_report(
        self, days: int = 30, output_path: Optional[str] = None
    ) -> str:
        """Generate comprehensive workflow report"""
        summary = self.workflow_analyzer.get_workflow_summary(days)
        recommendations = (
            self.workflow_analyzer.get_workflow_optimization_recommendations(days)
        )
        feature_usage = self.workflow_analyzer.get_feature_usage_analysis(days)

        report = f"""
# LRDBench Workflow Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Period: {days} days

## Workflow Overview
- Total Workflows: {summary.total_workflows:,}
- Unique Users: {summary.unique_users:,}
- Average Duration: {summary.avg_workflow_duration:.1f}s
- Average Steps: {summary.avg_steps_per_workflow:.1f}

## Workflow Complexity Distribution
"""

        for complexity, count in summary.workflow_complexity_distribution.items():
            percentage = (
                (count / summary.total_workflows * 100)
                if summary.total_workflows > 0
                else 0
            )
            report += f"- {complexity.replace('_', ' ').title()}: {count:,} ({percentage:.1f}%)\n"

        if summary.common_workflow_patterns:
            report += f"""
## Common Workflow Patterns
"""
            for i, (pattern, count) in enumerate(
                summary.common_workflow_patterns[:5], 1
            ):
                report += f"{i}. {pattern}: {count:,} workflows\n"

        if summary.popular_estimator_sequences:
            report += f"""
## Popular Estimator Sequences
"""
            for i, (sequence, count) in enumerate(
                summary.popular_estimator_sequences[:5], 1
            ):
                report += f"{i}. {' → '.join(sequence)}: {count:,} workflows\n"

        if feature_usage["top_estimators"]:
            report += f"""
## Top Estimators by Usage
"""
            for estimator, count in feature_usage["top_estimators"][:10]:
                report += f"- {estimator}: {count:,} uses\n"

        if recommendations:
            report += f"""
## Optimization Recommendations
"""
            for i, recommendation in enumerate(recommendations, 1):
                report += f"{i}. {recommendation}\n"

        if output_path:
            with open(output_path, "w") as f:
                f.write(report)

        return report

    def generate_comprehensive_report(
        self, days: int = 30, output_dir: Optional[str] = None
    ) -> str:
        """Generate comprehensive analytics report with all sections"""
        if output_dir is None:
            output_dir = self.storage_path / "reports"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate individual reports
        usage_report = self.generate_usage_report(
            days, output_path / f"usage_report_{timestamp}.md"
        )
        performance_report = self.generate_performance_report(
            days, output_path / f"performance_report_{timestamp}.md"
        )
        reliability_report = self.generate_reliability_report(
            days, output_path / f"reliability_report_{timestamp}.md"
        )
        workflow_report = self.generate_workflow_report(
            days, output_path / f"workflow_report_{timestamp}.md"
        )

        # Generate comprehensive report
        comprehensive_report = f"""
# LRDBench Comprehensive Analytics Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Period: {days} days

## Executive Summary
This report provides comprehensive insights into LRDBench usage, performance, reliability, and workflows.

## Quick Statistics
"""

        # Add quick stats from all summaries
        usage_summary = self.usage_tracker.get_usage_summary(days)
        performance_summary = self.performance_monitor.get_performance_summary(days)
        error_summary = self.error_analyzer.get_error_summary(days)
        workflow_summary = self.workflow_analyzer.get_workflow_summary(days)

        comprehensive_report += f"""
- **Total Usage Events**: {usage_summary.total_events:,}
- **Success Rate**: {usage_summary.success_rate:.1%}
- **Average Execution Time**: {performance_summary.avg_execution_time:.3f}s
- **Reliability Score**: {error_summary.reliability_score:.1%}
- **Total Workflows**: {workflow_summary.total_workflows:,}
- **Unique Users**: {usage_summary.unique_users:,}

## Report Sections
1. [Usage Analysis](usage_report_{timestamp}.md)
2. [Performance Analysis](performance_report_{timestamp}.md)
3. [Reliability Analysis](reliability_report_{timestamp}.md)
4. [Workflow Analysis](workflow_report_{timestamp}.md)

## Key Insights
"""

        # Add key insights
        if usage_summary.estimator_usage:
            top_estimator = max(
                usage_summary.estimator_usage.items(), key=lambda x: x[1]
            )
            comprehensive_report += f"- Most popular estimator: {top_estimator[0]} ({top_estimator[1]:,} uses)\n"

        if performance_summary.bottleneck_estimators:
            comprehensive_report += f"- Performance bottleneck: {performance_summary.bottleneck_estimators[0]}\n"

        if error_summary.error_by_type:
            top_error_type = max(
                error_summary.error_by_type.items(), key=lambda x: x[1]
            )
            comprehensive_report += f"- Most common error type: {top_error_type[0]} ({top_error_type[1]:,} errors)\n"

        if workflow_summary.common_workflow_patterns:
            top_pattern = workflow_summary.common_workflow_patterns[0]
            comprehensive_report += f"- Most common workflow pattern: {top_pattern[0]} ({top_pattern[1]:,} workflows)\n"

        comprehensive_report += f"""
## Recommendations
"""

        # Add recommendations from all analyzers
        usage_recommendations = []
        performance_recommendations = []
        error_recommendations = self.error_analyzer.get_improvement_recommendations(
            days
        )
        workflow_recommendations = (
            self.workflow_analyzer.get_workflow_optimization_recommendations(days)
        )

        all_recommendations = (
            usage_recommendations
            + performance_recommendations
            + error_recommendations
            + workflow_recommendations
        )

        if all_recommendations:
            for i, recommendation in enumerate(all_recommendations[:10], 1):  # Top 10
                comprehensive_report += f"{i}. {recommendation}\n"
        else:
            comprehensive_report += "- No specific recommendations at this time.\n"

        # Save comprehensive report
        comprehensive_path = output_path / f"comprehensive_report_{timestamp}.md"
        with open(comprehensive_path, "w") as f:
            f.write(comprehensive_report)

        return comprehensive_report

    def generate_stratified_report(
        self,
        results_path: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate a stratified benchmark report from a saved comprehensive benchmark JSON.
        """
        results_file = Path(results_path).expanduser()
        if not results_file.exists():
            raise FileNotFoundError(f"Benchmark results file not found: {results_file}")

        with open(results_file, "r") as f:
            summary = json.load(f)

        stratified = summary.get("stratified_metrics")

        report_lines: List[str] = [
            "# Stratified Benchmark Report",
            f"Source file: {results_file}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        if not stratified:
            report_lines.append("No stratified metrics were found in this benchmark artefact.")
            report = "\n".join(report_lines)
            if output_path:
                with open(output_path, "w") as f:
                    f.write(report)
            return report

        status = stratified.get("status", "unavailable")
        report_lines.append(f"Status: **{status}**")
        report_lines.append("")

        if status != "ok":
            report_lines.append(stratified.get("reason", "Stratified analysis unavailable."))
            report = "\n".join(report_lines)
            if output_path:
                with open(output_path, "w") as f:
                    f.write(report)
            return report

        report_lines.append(
            f"Total observations analysed: {stratified.get('total_observations', 0)}"
        )
        report_lines.append("")

        def fmt_val(value: Optional[float], precision: int = 4) -> str:
            if value is None:
                return "–"
            return f"{value:.{precision}f}"

        def fmt_rate(value: Optional[float]) -> str:
            if value is None:
                return "–"
            return f"{100.0 * value:.1f}%"

        def append_section(title: str, data: Dict[str, Any]) -> None:
            report_lines.append(f"## {title}")
            if not data:
                report_lines.append("_No data available._")
                report_lines.append("")
                return

            headers = [
                "Band",
                "n",
                "Mean Error",
                "Median Error",
                "Success Rate",
                "Coverage",
                "Mean CI Width",
                "Mean Ĥ",
                "Data Models",
            ]
            report_lines.append("| " + " | ".join(headers) + " |")
            report_lines.append("|" + " --- |" * len(headers))

            sorted_rows = sorted(
                data.items(),
                key=lambda kv: (kv[1].get("mean_error") is None, kv[1].get("mean_error", 0.0)),
            )

            for band, metrics in sorted_rows:
                row = [
                    band,
                    str(metrics.get("n", 0)),
                    fmt_val(metrics.get("mean_error")),
                    fmt_val(metrics.get("median_error")),
                    fmt_rate(metrics.get("success_rate")),
                    fmt_rate(metrics.get("coverage_rate")),
                    fmt_val(metrics.get("mean_ci_width")),
                    fmt_val(metrics.get("mean_estimated_h")),
                    ", ".join(metrics.get("data_models", [])) or "–",
                ]
                report_lines.append("| " + " | ".join(row) + " |")

            report_lines.append("")

        append_section("Hurst Regimes", stratified.get("hurst_bands", {}))
        append_section("Tail Classes", stratified.get("tail_classes", {}))
        append_section("Length Regimes", stratified.get("data_length_bands", {}))
        contamination_data = stratified.get("contamination", {})
        append_section("Contamination Regimes", contamination_data)
        if (
            contamination_data
            and len(contamination_data) == 1
            and "clean" in contamination_data
        ):
            report_lines.append(
                "_No contaminated scenarios were included in this benchmark run._"
            )
            report_lines.append("")

        provenance = summary.get("provenance", {})
        estimator_category_map: Dict[str, str] = {}
        for category, names in provenance.get("estimators_tested", {}).items():
            for name in names:
                estimator_category_map[name] = category

        estimator_stats: Dict[str, Dict[str, Any]] = {}
        results = summary.get("results", {})

        def extract_coverage_flag(est_result: Dict[str, Any]) -> Optional[bool]:
            uncertainty = est_result.get("uncertainty")
            if not isinstance(uncertainty, dict):
                return None
            coverage_data = uncertainty.get("coverage")
            primary = uncertainty.get("primary_interval")
            method = primary.get("method") if isinstance(primary, dict) else None
            if isinstance(coverage_data, dict):
                if method and method in coverage_data:
                    return coverage_data.get(method)
                for value in coverage_data.values():
                    if value is not None:
                        return value
            return None

        for model_data in results.values():
            for est_result in model_data.get("estimator_results", []):
                estimator_name = est_result.get("estimator")
                if estimator_name is None:
                    continue
                entry = estimator_stats.setdefault(
                    estimator_name,
                    {
                        "category": estimator_category_map.get(
                            estimator_name, "unknown"
                        ),
                        "count": 0,
                        "success": 0,
                        "errors": [],
                        "ci_widths": [],
                        "coverage": [],
                    },
                )
                entry["count"] += 1
                if est_result.get("success"):
                    entry["success"] += 1
                error = est_result.get("error")
                if error is not None and np.isfinite(error):
                    entry["errors"].append(float(error))
                ci = est_result.get("confidence_interval")
                if (
                    isinstance(ci, (list, tuple))
                    and len(ci) == 2
                    and ci[0] is not None
                    and ci[1] is not None
                ):
                    try:
                        width = float(ci[1]) - float(ci[0])
                        if np.isfinite(width):
                            entry["ci_widths"].append(width)
                    except (TypeError, ValueError):
                        pass
                coverage_flag = extract_coverage_flag(est_result)
                if coverage_flag is not None:
                    try:
                        entry["coverage"].append(bool(coverage_flag))
                    except Exception:
                        pass

        if estimator_stats:
            report_lines.append("## Estimator Summary")
            headers = [
                "Estimator",
                "Category",
                "n",
                "Mean Error",
                "Median Error",
                "Success Rate",
                "Coverage",
                "Mean CI Width",
            ]
            report_lines.append("| " + " | ".join(headers) + " |")
            report_lines.append("|" + " --- |" * len(headers))
            sorted_estimators = sorted(
                estimator_stats.items(),
                key=lambda item: (
                    np.mean(item[1]["errors"]) if item[1]["errors"] else float("inf"),
                    item[0],
                ),
            )
            for estimator_name, info in sorted_estimators:
                count = info["count"]
                mean_error = np.mean(info["errors"]) if info["errors"] else None
                median_error = (
                    float(np.median(info["errors"])) if info["errors"] else None
                )
                success_rate = info["success"] / count if count else 0.0
                coverage_rate = (
                    float(np.mean(info["coverage"])) if info["coverage"] else None
                )
                mean_ci_width = (
                    float(np.mean(info["ci_widths"])) if info["ci_widths"] else None
                )
                row = [
                    estimator_name,
                    info["category"],
                    str(count),
                    fmt_val(mean_error),
                    fmt_val(median_error),
                    fmt_rate(success_rate),
                    fmt_rate(coverage_rate),
                    fmt_val(mean_ci_width),
                ]
                report_lines.append("| " + " | ".join(row) + " |")
            report_lines.append("")

        category_stats: Dict[str, Dict[str, Any]] = {}
        for estimator_name, info in estimator_stats.items():
            category = info["category"]
            entry = category_stats.setdefault(
                category,
                {
                    "estimators": [],
                    "count": 0,
                    "success": 0,
                    "errors": [],
                    "ci_widths": [],
                    "coverage": [],
                },
            )
            entry["estimators"].append(estimator_name)
            entry["count"] += info["count"]
            entry["success"] += info["success"]
            entry["errors"].extend(info["errors"])
            entry["ci_widths"].extend(info["ci_widths"])
            entry["coverage"].extend(info["coverage"])

        if category_stats:
            report_lines.append("## Category Summary")
            headers = [
                "Category",
                "Estimators",
                "n",
                "Mean Error",
                "Median Error",
                "Success Rate",
                "Coverage",
                "Mean CI Width",
            ]
            report_lines.append("| " + " | ".join(headers) + " |")
            report_lines.append("|" + " --- |" * len(headers))
            sorted_categories = sorted(
                category_stats.items(),
                key=lambda item: (
                    np.mean(item[1]["errors"]) if item[1]["errors"] else float("inf"),
                    item[0],
                ),
            )
            for category, info in sorted_categories:
                count = info["count"]
                mean_error = np.mean(info["errors"]) if info["errors"] else None
                median_error = (
                    float(np.median(info["errors"])) if info["errors"] else None
                )
                success_rate = info["success"] / count if count else 0.0
                coverage_rate = (
                    float(np.mean(info["coverage"])) if info["coverage"] else None
                )
                mean_ci_width = (
                    float(np.mean(info["ci_widths"])) if info["ci_widths"] else None
                )
                row = [
                    category,
                    ", ".join(sorted(info["estimators"])) if info["estimators"] else "–",
                    str(count),
                    fmt_val(mean_error),
                    fmt_val(median_error),
                    fmt_rate(success_rate),
                    fmt_rate(coverage_rate),
                    fmt_val(mean_ci_width),
                ]
                report_lines.append("| " + " | ".join(row) + " |")
            report_lines.append("")

        report = "\n".join(report_lines)
        if output_path:
            with open(output_path, "w") as f:
                f.write(report)

        return report

    def create_advanced_diagnostics_visuals(
        self,
        advanced_results_path: str,
        output_dir: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Create scaling and robustness visualisations from advanced benchmark artefacts.
        """
        results_file = Path(advanced_results_path).expanduser()
        if not results_file.exists():
            raise FileNotFoundError(f"Advanced benchmark file not found: {results_file}")

        with open(results_file, "r") as f:
            advanced_summary = json.load(f)

        scaling_points: List[Tuple[str, float, float]] = []
        robustness_points: List[Tuple[str, float]] = []

        for model_data in advanced_summary.get("results", {}).values():
            if "estimator_results" not in model_data:
                continue
            for est_result in model_data["estimator_results"]:
                name = est_result.get("estimator", "unknown")
                scaling_diag = est_result.get("scaling_diagnostics")
                if (
                    isinstance(scaling_diag, dict)
                    and scaling_diag.get("status") == "ok"
                    and scaling_diag.get("slope") is not None
                ):
                    scaling_points.append(
                        (
                            name,
                            float(scaling_diag["slope"]),
                            float(scaling_diag.get("r_squared") or 0.0),
                        )
                    )
                robustness_panel = est_result.get("robustness_panel")
                if (
                    isinstance(robustness_panel, dict)
                    and robustness_panel.get("summary", {}).get("mean_abs_delta") is not None
                ):
                    robustness_points.append(
                        (
                            name,
                            float(robustness_panel["summary"]["mean_abs_delta"]),
                        )
                    )

        if output_dir is None:
            output_dir = self.storage_path / "visualizations"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        artefacts: Dict[str, str] = {}

        if scaling_points:
            scaling_points.sort(key=lambda item: abs(item[1]), reverse=True)
            labels = [item[0] for item in scaling_points]
            slopes = [item[1] for item in scaling_points]
            r2 = [item[2] for item in scaling_points]

            plt.figure(figsize=(10, 6))
            bars = plt.bar(labels, slopes, color=plt.cm.cividis(np.linspace(0, 1, len(labels))))
            plt.xticks(rotation=45, ha="right")
            plt.ylabel("Log–log slope")
            plt.title("Scaling Slopes by Estimator")
            for bar, r_squared in zip(bars, r2):
                plt.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f"R²={r_squared:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )
            scaling_path = output_dir / "scaling_slopes.png"
            plt.tight_layout()
            plt.savefig(scaling_path, dpi=300, bbox_inches="tight")
            plt.close()
            artefacts["scaling_slopes"] = str(scaling_path)

        if robustness_points:
            robustness_points.sort(key=lambda item: item[1], reverse=True)
            labels = [item[0] for item in robustness_points]
            deltas = [item[1] for item in robustness_points]

            plt.figure(figsize=(10, 6))
            plt.bar(labels, deltas, color=plt.cm.magma(np.linspace(0, 1, len(labels))))
            plt.xticks(rotation=45, ha="right")
            plt.ylabel("Mean |ΔH|")
            plt.title("Robustness Stress Panel Sensitivity")
            robustness_path = output_dir / "robustness_panels.png"
            plt.tight_layout()
            plt.savefig(robustness_path, dpi=300, bbox_inches="tight")
            plt.close()
            artefacts["robustness_panels"] = str(robustness_path)

        return artefacts

    def create_visualizations(
        self, days: int = 30, output_dir: Optional[str] = None
    ) -> Dict[str, str]:
        """Create visualizations for analytics data"""
        if output_dir is None:
            output_dir = self.storage_path / "visualizations"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plots = {}

        # Usage visualization
        usage_summary = self.usage_tracker.get_usage_summary(days)
        if usage_summary.estimator_usage:
            plt.figure(figsize=(12, 6))
            estimators = list(usage_summary.estimator_usage.keys())
            counts = list(usage_summary.estimator_usage.values())

            plt.bar(range(len(estimators)), counts)
            plt.xlabel("Estimators")
            plt.ylabel("Usage Count")
            plt.title(f"Estimator Usage (Last {days} days)")
            plt.xticks(range(len(estimators)), estimators, rotation=45, ha="right")
            plt.tight_layout()

            usage_plot_path = output_path / f"estimator_usage_{timestamp}.png"
            plt.savefig(usage_plot_path, dpi=300, bbox_inches="tight")
            plt.close()
            plots["estimator_usage"] = str(usage_plot_path)

        # Performance visualization
        performance_summary = self.performance_monitor.get_performance_summary(days)
        if performance_summary.total_executions > 0:
            plt.figure(figsize=(10, 6))

            # Create performance metrics bar chart
            metrics = ["Avg Time", "Min Time", "Max Time"]
            values = [
                performance_summary.avg_execution_time,
                performance_summary.min_execution_time,
                performance_summary.max_execution_time,
            ]

            plt.bar(metrics, values, color=["skyblue", "lightgreen", "lightcoral"])
            plt.ylabel("Execution Time (seconds)")
            plt.title(f"Performance Metrics (Last {days} days)")
            plt.tight_layout()

            perf_plot_path = output_path / f"performance_metrics_{timestamp}.png"
            plt.savefig(perf_plot_path, dpi=300, bbox_inches="tight")
            plt.close()
            plots["performance_metrics"] = str(perf_plot_path)

        # Error visualization
        error_summary = self.error_analyzer.get_error_summary(days)
        if error_summary.error_by_type:
            plt.figure(figsize=(10, 6))
            error_types = list(error_summary.error_by_type.keys())
            error_counts = list(error_summary.error_by_type.values())

            plt.pie(error_counts, labels=error_types, autopct="%1.1f%%", startangle=90)
            plt.title(f"Error Distribution by Type (Last {days} days)")
            plt.axis("equal")
            plt.tight_layout()

            error_plot_path = output_path / f"error_distribution_{timestamp}.png"
            plt.savefig(error_plot_path, dpi=300, bbox_inches="tight")
            plt.close()
            plots["error_distribution"] = str(error_plot_path)

        # Workflow visualization
        workflow_summary = self.workflow_analyzer.get_workflow_summary(days)
        if workflow_summary.workflow_complexity_distribution:
            plt.figure(figsize=(10, 6))
            complexities = list(
                workflow_summary.workflow_complexity_distribution.keys()
            )
            counts = list(workflow_summary.workflow_complexity_distribution.values())

            # Clean up complexity labels
            clean_labels = [c.replace("_", " ").title() for c in complexities]

            plt.bar(clean_labels, counts, color="lightblue")
            plt.xlabel("Workflow Complexity")
            plt.ylabel("Number of Workflows")
            plt.title(f"Workflow Complexity Distribution (Last {days} days)")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            workflow_plot_path = output_path / f"workflow_complexity_{timestamp}.png"
            plt.savefig(workflow_plot_path, dpi=300, bbox_inches="tight")
            plt.close()
            plots["workflow_complexity"] = str(workflow_plot_path)

        return plots

    def export_all_data(
        self, output_dir: Optional[str] = None, days: int = 30
    ) -> Dict[str, str]:
        """Export all analytics data to files"""
        if output_dir is None:
            output_dir = self.storage_path / "exports"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exports = {}

        # Export usage data
        usage_path = output_path / f"usage_data_{timestamp}.json"
        self.usage_tracker.export_summary(str(usage_path), days)
        exports["usage_data"] = str(usage_path)

        # Export performance data
        perf_path = output_path / f"performance_data_{timestamp}.json"
        self.performance_monitor.export_metrics(str(perf_path), days)
        exports["performance_data"] = str(perf_path)

        # Export error data
        error_path = output_path / f"error_data_{timestamp}.json"
        self.error_analyzer.export_errors(str(error_path), days)
        exports["error_data"] = str(error_path)

        # Export workflow data
        workflow_path = output_path / f"workflow_data_{timestamp}.json"
        self.workflow_analyzer.export_workflows(str(workflow_path), days)
        exports["workflow_data"] = str(workflow_path)

        return exports


# Global dashboard instance
_global_dashboard: Optional[AnalyticsDashboard] = None


def get_analytics_dashboard() -> AnalyticsDashboard:
    """Get the global analytics dashboard instance"""
    global _global_dashboard
    if _global_dashboard is None:
        _global_dashboard = AnalyticsDashboard()
    return _global_dashboard


def quick_analytics_summary(days: int = 30) -> str:
    """Get a quick summary of analytics data"""
    dashboard = get_analytics_dashboard()
    summary = dashboard.get_comprehensive_summary(days)

    quick_summary = f"""
📊 LRDBench Analytics Summary (Last {days} days)

📈 Usage:
   • Total Events: {summary['usage_summary'].total_events:,}
   • Success Rate: {summary['usage_summary'].success_rate:.1%}
   • Unique Users: {summary['usage_summary'].unique_users:,}

⚡ Performance:
   • Avg Execution Time: {summary['performance_summary'].avg_execution_time:.3f}s
   • Total Executions: {summary['performance_summary'].total_executions:,}
   • Trend: {summary['performance_summary'].performance_trend}

🛡️ Reliability:
   • Reliability Score: {summary['error_summary'].reliability_score:.1%}
   • Total Errors: {summary['error_summary'].total_errors:,}

🔄 Workflows:
   • Total Workflows: {summary['workflow_summary'].total_workflows:,}
   • Avg Duration: {summary['workflow_summary'].avg_workflow_duration:.1f}s
   • Avg Steps: {summary['workflow_summary'].avg_steps_per_workflow:.1f}
"""

    return quick_summary
