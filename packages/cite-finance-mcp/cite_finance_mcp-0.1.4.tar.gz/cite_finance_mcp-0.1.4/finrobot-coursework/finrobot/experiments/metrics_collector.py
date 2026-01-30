"""
Comprehensive metrics collection for experiment evaluation.

Tracks: latency, cost, reasoning depth, verifiability, output quality.
All measurements are designed for robust comparison between FinRobot and RAG systems.
"""

import time
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
import re

from finrobot.logging import get_logger, record_metric

logger = get_logger(__name__)


@dataclass
class MetricSnapshot:
    """Captures a single measurement point during an experiment."""

    # Identification
    experiment_id: str
    system_name: str  # "agent" or "rag"
    ticker: str
    task_name: str
    model_name: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Timing metrics (seconds)
    latency_seconds: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    # Cost metrics (USD)
    total_cost: float = 0.0
    completion_tokens: int = 0
    prompt_tokens: int = 0

    # Reasoning metrics
    tool_calls_count: int = 0
    reasoning_steps: int = 0
    response_length: int = 0

    # Quality metrics
    response_text: str = ""
    error_occurred: bool = False
    error_message: Optional[str] = None

    # Verifiability metrics
    claims_extracted: List[str] = field(default_factory=list)
    sources_cited: List[str] = field(default_factory=list)
    fact_check_score: Optional[float] = None  # 0-1, filled later by fact checker

    def start_timer(self):
        """Start timing this metric."""
        self.start_time = time.time()

    def end_timer(self):
        """End timing and calculate latency."""
        if self.start_time is None:
            logger.warning("Timer ended without starting")
            return
        self.end_time = time.time()
        self.latency_seconds = self.end_time - self.start_time

    def add_tool_call(self):
        """Record a tool call."""
        self.tool_calls_count += 1

    def add_reasoning_step(self):
        """Record a reasoning step in the chain of thought."""
        self.reasoning_steps += 1

    def set_response(self, text: str):
        """Store response and calculate metrics."""
        self.response_text = text
        self.response_length = len(text)
        # Auto-extract potential claims
        self._extract_claims()

    def _extract_claims(self):
        """
        Extract quantitative claims from response.
        Looks for patterns like "X% change", "price target $Y", "predicts Z".
        """
        patterns = [
            r"(\d+(?:\.\d+)?)\s*%\s*(?:up|down|increase|decrease|change)",
            r"(?:target|price|predict)\s*\$?\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:dollars?|dol\.)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, self.response_text, re.IGNORECASE)
            if matches:
                self.claims_extracted.extend([f"{pattern}: {m}" for m in matches])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        d = asdict(self)
        # Format lists as JSON strings for CSV compatibility
        d["claims_extracted"] = json.dumps(self.claims_extracted)
        d["sources_cited"] = json.dumps(self.sources_cited)
        return d

    def record_to_logger(self):
        """Record this metric to the structured logger."""
        record_metric(
            "experiment_run",
            {
                "system": self.system_name,
                "ticker": self.ticker,
                "task": self.task_name,
                "latency": self.latency_seconds,
                "cost": self.total_cost,
                "tools": self.tool_calls_count,
                "reasoning_steps": self.reasoning_steps,
            },
            tags={"experiment_id": self.experiment_id},
        )


class MetricsCollector:
    """
    Central collector for all experiment metrics.
    
    Handles:
    - Multiple experiments in parallel
    - CSV export for analysis
    - Real-time metric tracking
    - Statistical aggregation
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize metrics collector.
        
        Args:
            output_dir: Directory to save metrics (default: ./experiment_results)
        """
        self.output_dir = Path(output_dir or "./experiment_results")
        self.output_dir.mkdir(exist_ok=True)
        self.metrics: List[MetricSnapshot] = []
        self.current_metric: Optional[MetricSnapshot] = None
        logger.info(f"MetricsCollector initialized with output dir: {self.output_dir}")

    def start_measurement(
        self, experiment_id: str, system_name: str, ticker: str, task_name: str
    ) -> MetricSnapshot:
        """
        Start a new measurement.
        
        Args:
            experiment_id: Unique experiment identifier
            system_name: "agent" or "rag"
            ticker: Stock ticker symbol
            task_name: Description of analysis task
            
        Returns:
            MetricSnapshot object to fill during execution
        """
        self.current_metric = MetricSnapshot(
            experiment_id=experiment_id,
            system_name=system_name,
            ticker=ticker,
            task_name=task_name,
        )
        self.current_metric.start_timer()
        logger.debug(
            f"Started measurement: {system_name} on {ticker} ({task_name})"
        )
        return self.current_metric

    def end_measurement(self, metric: Optional[MetricSnapshot] = None) -> MetricSnapshot:
        """
        End current measurement and store it.
        
        Args:
            metric: Specific metric to end (or current_metric if None)
            
        Returns:
            Completed MetricSnapshot
        """
        m = metric or self.current_metric
        if m is None:
            logger.error("No active measurement to end")
            raise ValueError("No active measurement")

        m.end_timer()
        self.metrics.append(m)
        metric.record_to_logger()
        logger.debug(f"Completed measurement in {m.latency_seconds:.2f}s")
        return m

    def set_cost(self, prompt_tokens: int, completion_tokens: int, model: str = "gpt-4"):
        """
        Calculate API cost based on tokens.
        
        Current pricing (as of Nov 2024):
        - GPT-4: $0.03/1K prompt, $0.06/1K completion
        - GPT-3.5: $0.0005/1K prompt, $0.0015/1K completion
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            model: Model name
        """
        if self.current_metric is None:
            logger.warning("No active metric for cost tracking")
            return

        # Pricing dictionary (can be updated)
        pricing = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        }

        rates = pricing.get(model, pricing["gpt-4"])
        prompt_cost = (prompt_tokens / 1000) * rates["prompt"]
        completion_cost = (completion_tokens / 1000) * rates["completion"]
        total_cost = prompt_cost + completion_cost

        self.current_metric.prompt_tokens = prompt_tokens
        self.current_metric.completion_tokens = completion_tokens
        self.current_metric.total_cost = total_cost
        logger.debug(f"Cost tracked: ${total_cost:.4f} ({prompt_tokens}+{completion_tokens} tokens)")

    def get_statistics(self, system_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate aggregate statistics across metrics.
        
        Args:
            system_filter: Filter to "agent" or "rag" (None = all)
            
        Returns:
            Dictionary with mean/std/min/max for all metrics
        """
        metrics = self.metrics
        if system_filter:
            metrics = [m for m in metrics if m.system_name == system_filter]

        if not metrics:
            logger.warning(f"No metrics found for filter: {system_filter}")
            return {}

        latencies = [m.latency_seconds for m in metrics if not m.error_occurred]
        costs = [m.total_cost for m in metrics if not m.error_occurred]
        tool_calls = [m.tool_calls_count for m in metrics]
        reasoning_steps = [m.reasoning_steps for m in metrics]

        def safe_avg(lst):
            return sum(lst) / len(lst) if lst else 0

        def safe_std(lst):
            if len(lst) < 2:
                return 0
            avg = safe_avg(lst)
            variance = sum((x - avg) ** 2 for x in lst) / len(lst)
            return variance ** 0.5

        stats = {
            "count": len(metrics),
            "errors": sum(1 for m in metrics if m.error_occurred),
            "latency": {
                "mean": safe_avg(latencies),
                "std": safe_std(latencies),
                "min": min(latencies) if latencies else 0,
                "max": max(latencies) if latencies else 0,
            },
            "cost": {
                "mean": safe_avg(costs),
                "std": safe_std(costs),
                "min": min(costs) if costs else 0,
                "max": max(costs) if costs else 0,
                "total": sum(costs),
            },
            "reasoning": {
                "avg_tool_calls": safe_avg(tool_calls),
                "avg_reasoning_steps": safe_avg(reasoning_steps),
            },
        }
        return stats

    def export_csv(self, filename: Optional[str] = None) -> Path:
        """
        Export all metrics to CSV for analysis.
        
        Args:
            filename: Output filename (default: metrics_TIMESTAMP.csv)
            
        Returns:
            Path to exported file
        """
        if not self.metrics:
            logger.warning("No metrics to export")
            return Path()

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.csv"

        output_path = self.output_dir / filename
        
        import csv
        
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.metrics[0].to_dict().keys())
            writer.writeheader()
            for metric in self.metrics:
                writer.writerow(metric.to_dict())

        logger.info(f"Exported {len(self.metrics)} metrics to {output_path}")
        return output_path

    def export_json(self, filename: Optional[str] = None) -> Path:
        """
        Export metrics to JSON format.
        
        Args:
            filename: Output filename (default: metrics_TIMESTAMP.json)
            
        Returns:
            Path to exported file
        """
        if not self.metrics:
            logger.warning("No metrics to export")
            return Path()

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.json"

        output_path = self.output_dir / filename
        data = [m.to_dict() for m in self.metrics]
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(self.metrics)} metrics to {output_path}")
        return output_path

    def print_summary(self):
        """Print human-readable summary of all metrics."""
        print("\n" + "=" * 80)
        print("EXPERIMENT METRICS SUMMARY")
        print("=" * 80)

        # Overall stats
        overall = self.get_statistics()
        print(f"\nTotal Runs: {overall.get('count', 0)}")
        print(f"Errors: {overall.get('errors', 0)}")

        # Per-system stats
        for system in ["agent", "rag"]:
            stats = self.get_statistics(system_filter=system)
            if stats.get("count", 0) == 0:
                continue

            print(f"\n{system.upper()} System:")
            print(f"  Runs: {stats['count']}")
            print(f"  Latency: {stats['latency']['mean']:.2f}s ± {stats['latency']['std']:.2f}s")
            print(f"  Cost: ${stats['cost']['mean']:.4f} ± ${stats['cost']['std']:.4f}")
            print(f"  Avg Tool Calls: {stats['reasoning']['avg_tool_calls']:.1f}")
            print(f"  Total Cost: ${stats['cost']['total']:.2f}")

        print("\n" + "=" * 80)
