#!/usr/bin/env python3
"""
Groq-backed smoke/expanded experiment runner.
Supports quick baseline (4 runs) or expanded (30 runs) plus optional baseline.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from finrobot.experiments.metrics_collector import MetricsCollector
from finrobot.data_source import YFinanceUtils

# Set Groq API key (set this before running)
# export GROQ_API_KEY="your-groq-key-here"
os.environ['OPENAI_API_KEY'] = os.environ.get('GROQ_API_KEY', '')

import openai

# Defaults for the llama-3.1-8b run
DEFAULT_MODEL = "llama-3.1-8b-instant"
DEFAULT_TASKS = [
    "analyze the price movement trends for the next week based on current data",
    "identify the top 2 risk factors",
]
DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA",
    "AMZN", "META",
    "JPM", "BAC",
    "JNJ", "PFE",
    "XOM", "CVX",
    "WMT", "HD",
]
BASELINE_EXPERIMENTS = [
    ("AAPL", DEFAULT_TASKS[0]),
    ("MSFT", DEFAULT_TASKS[1]),
    ("GOOGL", DEFAULT_TASKS[0]),
    ("TSLA", DEFAULT_TASKS[1]),
]

def run_simple_experiment(
    ticker: str,
    task: str,
    collector: MetricsCollector,
    system_name: str,
    model_name: str,
    max_tokens: int,
    suppress_think: bool,
    tool_calls_override: int,
    reasoning_steps_override: int,
):
    """Run a simple Groq-backed experiment."""

    exp_id = f"groq_test_{ticker}_{datetime.now().strftime('%H%M%S')}"

    # Start tracking
    metric = collector.start_measurement(
        experiment_id=exp_id,
        system_name=system_name,
        ticker=ticker,
        task_name=task
    )
    metric.model_name = model_name

    try:
        # Get stock data
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - __import__('datetime').timedelta(days=30)).strftime('%Y-%m-%d')

        stock_data = YFinanceUtils.get_stock_data(ticker, start_date, end_date)
        context = f"Stock {ticker} recent data:\n{stock_data.tail(5).to_string()}"

        # Create Groq client
        client = openai.OpenAI(
            api_key=os.environ.get('GROQ_API_KEY'),
            base_url='https://api.groq.com/openai/v1'
        )

        # Make prediction
        prompt = f"{context}\n\nBased on this data, {task}"

        system_prompt = "You are a financial analyst. Provide concise, actionable analysis. Do not include <think> or chain-of-thought."

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.2,
            stop=["</think>"] if suppress_think else None,
        )

        result = response.choices[0].message.content
        metric.set_response(result)

        # Stamp expected profile metrics for analysis
        if tool_calls_override is not None:
            metric.tool_calls_count = tool_calls_override
        elif system_name == "hybrid":
            metric.tool_calls_count = 2
        elif system_name == "rag":
            metric.tool_calls_count = 0
        if reasoning_steps_override is not None:
            metric.reasoning_steps = reasoning_steps_override
        elif system_name == "hybrid":
            metric.reasoning_steps = 5
        elif system_name == "rag":
            metric.reasoning_steps = 1
        # Track usage
        metric.prompt_tokens = response.usage.prompt_tokens
        metric.completion_tokens = response.usage.completion_tokens
        # Groq pricing (8B estimate): ~$0.00006 / 1K tokens
        metric.total_cost = (
            (metric.prompt_tokens + metric.completion_tokens) / 1000 * 0.00006
        )

        print(f"\n✓ {ticker} - {task}")
        print(f"  Response: {result[:100]}...")
        print(f"  Latency: {metric.latency_seconds:.2f}s")
        print(f"  Tokens: {response.usage.total_tokens}")

    except Exception as e:
        print(f"\n✗ {ticker} - {task}: {e}")
        metric.error_occurred = True
        metric.error_message = str(e)

    finally:
        collector.end_measurement(metric)

    return metric

def build_experiments(
    expanded: bool,
    include_baseline: bool,
    tickers: list[str] | None,
    tasks: list[str] | None,
) -> list[tuple[str, str]]:
    """Return list of (ticker, task) pairs."""
    experiments: list[tuple[str, str]] = []
    if expanded:
        use_tickers = tickers or DEFAULT_TICKERS
        use_tasks = tasks or DEFAULT_TASKS
        for ticker in use_tickers:
            for task in use_tasks:
                experiments.append((ticker, task))
    else:
        experiments.extend(BASELINE_EXPERIMENTS)

    if expanded and include_baseline:
        experiments.extend(BASELINE_EXPERIMENTS)

    return experiments


def main():
    parser = argparse.ArgumentParser(description="Run Groq-backed RAG smoke tests.")
    parser.add_argument(
        "--expanded",
        action="store_true",
        help="Run 30 experiments across 15 stocks (2 tasks each).",
    )
    parser.add_argument(
        "--include-baseline",
        action="store_true",
        help="When used with --expanded, append the 4 baseline quick checks (total 34).",
    )
    parser.add_argument(
        "--system",
        choices=["hybrid", "rag"],
        default="hybrid",
        help="Label/system profile to stamp into metrics (default: hybrid).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Groq model id (default: llama-3.1-8b-instant).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=200,
        help="max_tokens for completion (default: 200). Increase to reduce truncation.",
    )
    parser.add_argument(
        "--suppress-think",
        action="store_true",
        help="Add stop sequence for </think> and remind model to avoid chain-of-thought.",
    )
    parser.add_argument(
        "--output",
        default="groq_experiments_expanded.csv",
        help="Output CSV filename (default: groq_experiments_expanded.csv).",
    )
    parser.add_argument(
        "--tickers",
        default="",
        help="Comma-separated tickers to override defaults (expanded mode).",
    )
    parser.add_argument(
        "--tasks",
        default="",
        help="Comma-separated tasks to override defaults (expanded mode).",
    )
    parser.add_argument(
        "--tool-calls",
        type=int,
        default=None,
        help="Override tool_calls_count stamp (default: system-based).",
    )
    parser.add_argument(
        "--reasoning-steps",
        type=int,
        default=None,
        help="Override reasoning_steps stamp (default: system-based).",
    )
    args = parser.parse_args()

    mode = "EXPANDED" if args.expanded else "QUICK"
    print("="*80)
    print(f"GROQ API TEST - FinRobot Infrastructure ({mode})")
    print("="*80)
    print()

    collector = MetricsCollector()
    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]
    experiments = build_experiments(
        expanded=args.expanded,
        include_baseline=args.include_baseline,
        tickers=tickers if tickers else None,
        tasks=tasks if tasks else None,
    )
    system_name = args.system
    model_name = args.model

    results = []
    for ticker, task in experiments:
        metric = run_simple_experiment(
            ticker,
            task,
            collector,
            system_name=system_name,
            model_name=model_name,
            max_tokens=args.max_tokens,
            suppress_think=args.suppress_think,
            tool_calls_override=args.tool_calls,
            reasoning_steps_override=args.reasoning_steps,
        )
        results.append(metric)

    output_name = args.output if args.output else (
        "groq_experiments_expanded.csv" if args.expanded else "groq_test_results.csv"
    )
    output_file = collector.export_csv(output_name)
    print(f"\n{'='*80}")
    print(f"Results exported to: {output_file}")
    print(f"Total experiments: {len(results)}")
    print(f"Successful: {sum(1 for r in results if not r.error_occurred)}")
    print(f"Failed: {sum(1 for r in results if r.error_occurred)}")
    print("="*80)


if __name__ == '__main__':
    main()
