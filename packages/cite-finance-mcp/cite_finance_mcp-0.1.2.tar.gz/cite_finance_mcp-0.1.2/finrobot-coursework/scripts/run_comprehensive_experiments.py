"""
Master script to run comprehensive multi-model experiments.

This script addresses all major criticisms:
1. Ground truth validation - tracks and validates predictions
2. Statistical significance - rigorous t-tests, p-values, effect sizes
3. Multi-model evaluation - tests across GPT-4, Claude, LLaMA
4. Real-world data - 30+ real stocks across sectors
5. Large-scale experiments - 800+ total experiments

Usage:
    # Quick test (16 experiments, ~5 minutes)
    python scripts/run_comprehensive_experiments.py --quick

    # Full run (810 experiments, ~6-8 hours)
    python scripts/run_comprehensive_experiments.py --full

    # Resume from cache
    python scripts/run_comprehensive_experiments.py --full --use-cache
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from finrobot.experiments.multi_model_runner import (
    MultiModelExperimentRunner,
    create_comprehensive_plan,
    ModelConfig,
    ExperimentPlan,
)
from finrobot.logging import get_logger

logger = get_logger(__name__)


def main():
    """Run comprehensive experiments."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive multi-model experiments"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test (16 experiments)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full experiment suite (810 experiments)",
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached results to avoid re-running experiments",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results",
    )
    parser.add_argument(
        "--validate-ground-truth",
        action="store_true",
        help="Validate all pending ground truth predictions",
    )

    args = parser.parse_args()

    # Determine mode
    if args.validate_ground_truth:
        validate_predictions(args)
        return

    if not args.quick and not args.full:
        print("Please specify --quick or --full")
        parser.print_help()
        return

    # Create runner
    output_dir = args.output_dir or f"./experiment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    runner = MultiModelExperimentRunner(
        output_dir=output_dir,
        enable_caching=args.use_cache,
    )

    # Create plan
    print("\n" + "="*80)
    print("COMPREHENSIVE EXPERIMENT RUNNER")
    print("="*80)

    plan = create_comprehensive_plan(quick_test=args.quick)

    mode = "QUICK TEST" if args.quick else "FULL RUN"
    print(f"\nMode: {mode}")
    print(f"Total Experiments: {plan.total_experiments()}")
    print(f"Output Directory: {output_dir}")
    print(f"Caching: {'Enabled' if args.use_cache else 'Disabled'}")
    print(f"\nSystems: {plan.systems}")
    print(f"Models: {[m.name for m in plan.models]}")
    print(f"Stocks: {len(plan.tickers)}")
    print(f"Tasks: {len(plan.tasks)}")

    if not args.quick:
        # Estimate time and cost
        avg_time_per_experiment = 30  # seconds
        total_time_hours = (plan.total_experiments() * avg_time_per_experiment) / 3600

        # Rough cost estimate (assuming average of 2K tokens per call)
        avg_cost_per_call = 0.10  # dollars
        total_cost = plan.total_experiments() * avg_cost_per_call

        print(f"\nEstimated Time: {total_time_hours:.1f} hours")
        print(f"Estimated Cost: ${total_cost:.2f}")

        confirm = input("\nProceed? (yes/no): ")
        if confirm.lower() not in ["yes", "y"]:
            print("Aborted.")
            return

    print("\n" + "="*80)
    print("RUNNING EXPERIMENTS...")
    print("="*80 + "\n")

    # Run experiments
    start_time = datetime.now()
    results = runner.run_experiment_plan(plan)
    end_time = datetime.now()

    elapsed = (end_time - start_time).total_seconds()

    print("\n" + "="*80)
    print("EXPERIMENTS COMPLETE")
    print("="*80)
    print(f"Time Elapsed: {elapsed/60:.1f} minutes")
    print(f"Experiments Run: {sum(len(m) for m in results.values())}")

    # Analyze results
    print("\n" + "="*80)
    print("ANALYZING RESULTS...")
    print("="*80 + "\n")

    analysis = runner.analyze_results(results)

    # Print summary
    runner.print_summary(analysis)

    # Export everything
    print("\n" + "="*80)
    print("EXPORTING RESULTS...")
    print("="*80)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Export metrics
    metrics_file = runner.metrics_collector.export_csv(f"metrics_{timestamp}.csv")
    print(f"Metrics: {metrics_file}")

    # Export ground truth
    gt_file = runner.ground_truth_validator.export_report_csv(f"ground_truth_{timestamp}.csv")
    print(f"Ground Truth: {gt_file}")

    # Export statistical analysis
    stats_file = Path(output_dir) / f"statistical_analysis_{timestamp}.json"
    runner.statistical_analyzer.export_report(analysis['statistical_comparison'], stats_file)
    print(f"Statistics: {stats_file}")

    print("\n" + "="*80)
    print("ALL DONE!")
    print("="*80)
    print(f"\nResults saved to: {output_dir}")
    print("\nNext steps:")
    print("1. Wait 7 days for predictions to mature")
    print("2. Run: python scripts/run_comprehensive_experiments.py --validate-ground-truth")
    print("3. Generate visualizations: python scripts/generate_visualizations.py")
    print("4. Write paper: python scripts/generate_paper.py")


def validate_predictions(args):
    """Validate all pending ground truth predictions."""
    print("\n" + "="*80)
    print("GROUND TRUTH VALIDATION")
    print("="*80 + "\n")

    output_dir = args.output_dir or "./experiment_results"
    from finrobot.experiments.ground_truth_validator import GroundTruthValidator

    validator = GroundTruthValidator(storage_dir=f"{output_dir}/ground_truth")

    print(f"Total Predictions: {len(validator.predictions)}")
    validated_before = sum(1 for p in validator.predictions.values() if p.is_validated)
    print(f"Already Validated: {validated_before}")

    # Validate all due
    newly_validated = validator.validate_all_due()

    print(f"\nNewly Validated: {len(newly_validated)}")

    if newly_validated:
        validator.print_summary()

        # Export updated report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = validator.export_report_csv(f"validation_report_{timestamp}.csv")
        print(f"\nValidation report: {report_file}")
    else:
        print("\nNo predictions ready for validation yet.")
        print("Predictions must wait until their timeframe expires.")


if __name__ == "__main__":
    main()
