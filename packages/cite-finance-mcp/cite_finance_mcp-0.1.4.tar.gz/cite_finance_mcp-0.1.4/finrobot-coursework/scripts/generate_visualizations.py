"""
Generate publication-quality visualizations for experiment results.

Creates:
1. Performance comparison charts (latency, cost, accuracy)
2. Statistical significance heatmaps
3. Ground truth accuracy by system/model
4. Effect size visualizations
5. Time-series prediction tracking
6. Confidence interval plots
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from finrobot.experiments.ground_truth_validator import GroundTruthValidator
from finrobot.experiments.statistical_analysis import StatisticalAnalyzer
from finrobot.logging import get_logger

logger = get_logger(__name__)

# Set style
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11


def load_analysis(analysis_file: Path) -> Dict[str, Any]:
    """Load analysis JSON."""
    with open(analysis_file, "r") as f:
        return json.load(f)


def plot_performance_comparison(
    analysis: Dict[str, Any],
    output_dir: Path,
):
    """
    Create performance comparison charts.

    Shows latency, cost, and quality metrics across systems/models.
    """
    logger.info("Generating performance comparison chart...")

    comp = analysis['statistical_comparison']
    systems = comp['systems_compared']

    # Extract metrics for each system
    metrics = ['latency_seconds', 'total_cost', 'reasoning_steps', 'response_length']
    metric_labels = ['Latency (s)', 'Cost ($)', 'Reasoning Depth', 'Response Length']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
        ax = axes[idx]

        # Get data for each system from ttests
        system_means = {}
        system_stds = {}

        for ttest in comp['ttests']:
            if ttest['metric_name'] == metric:
                if ttest['group1_name'] not in system_means:
                    system_means[ttest['group1_name']] = ttest['mean1']
                    system_stds[ttest['group1_name']] = ttest['std1']
                if ttest['group2_name'] not in system_means:
                    system_means[ttest['group2_name']] = ttest['mean2']
                    system_stds[ttest['group2_name']] = ttest['std2']

        if not system_means:
            continue

        systems_list = list(system_means.keys())
        means = [system_means[s] for s in systems_list]
        stds = [system_stds[s] for s in systems_list]

        # Bar plot with error bars
        x = np.arange(len(systems_list))
        bars = ax.bar(x, means, yerr=stds, capsize=5, alpha=0.7)

        # Color bars by winner
        winner = comp['winner_by_metric'].get(metric)
        for i, (bar, system) in enumerate(zip(bars, systems_list)):
            if system == winner:
                bar.set_color('gold')
                bar.set_edgecolor('orange')
                bar.set_linewidth(2)

        ax.set_ylabel(label)
        ax.set_xticks(x)
        ax.set_xticklabels(systems_list, rotation=45, ha='right')
        ax.set_title(f"{label} by System/Model")

    plt.tight_layout()
    output_file = output_dir / "performance_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved: {output_file}")


def plot_statistical_significance(
    analysis: Dict[str, Any],
    output_dir: Path,
):
    """
    Create heatmap of statistical significance between systems.
    """
    logger.info("Generating statistical significance heatmap...")

    comp = analysis['statistical_comparison']
    ttests = comp['ttests']

    # Create significance matrix
    systems = list(set(
        [t['group1_name'] for t in ttests] + [t['group2_name'] for t in ttests]
    ))
    systems.sort()

    n = len(systems)
    sig_matrix = np.zeros((n, n))

    for ttest in ttests:
        i = systems.index(ttest['group1_name'])
        j = systems.index(ttest['group2_name'])

        # Store p-value (log scale for better visualization)
        p_val = ttest['p_value']
        sig_val = -np.log10(p_val + 1e-10)  # Avoid log(0)

        sig_matrix[i, j] = sig_val
        sig_matrix[j, i] = sig_val

    # Plot heatmap
    fig, ax = plt.subplots(figsize=(12, 10))

    sns.heatmap(
        sig_matrix,
        annot=True,
        fmt='.2f',
        cmap='RdYlGn',
        xticklabels=systems,
        yticklabels=systems,
        cbar_kws={'label': '-log10(p-value)'},
        ax=ax,
    )

    ax.set_title("Statistical Significance Heatmap\n(Higher = More Significant Difference)")

    # Add significance threshold lines
    threshold_05 = -np.log10(0.05)
    threshold_01 = -np.log10(0.01)

    plt.tight_layout()
    output_file = output_dir / "statistical_significance.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved: {output_file}")


def plot_ground_truth_accuracy(
    analysis: Dict[str, Any],
    output_dir: Path,
):
    """
    Plot ground truth validation accuracy by system/model.
    """
    logger.info("Generating ground truth accuracy chart...")

    validation_reports = analysis['validation_reports']

    systems = []
    accuracies = []
    directional_accs = []
    errors = []

    for system, report in validation_reports.items():
        if report['validated_predictions'] == 0:
            continue

        systems.append(system)
        accuracies.append(report['overall_accuracy'])
        directional_accs.append(report['directional_accuracy'])
        errors.append(report['mean_magnitude_error'])

    if not systems:
        logger.warning("No validated predictions yet, skipping ground truth plot")
        return

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # Overall accuracy
    ax = axes[0]
    bars = ax.bar(range(len(systems)), accuracies, alpha=0.7)
    ax.set_ylabel('Overall Accuracy (0-1)')
    ax.set_xticks(range(len(systems)))
    ax.set_xticklabels(systems, rotation=45, ha='right')
    ax.set_title('Overall Prediction Accuracy')
    ax.set_ylim(0, 1)

    # Color best performer
    best_idx = np.argmax(accuracies)
    bars[best_idx].set_color('gold')

    # Directional accuracy
    ax = axes[1]
    bars = ax.bar(range(len(systems)), directional_accs, alpha=0.7, color='skyblue')
    ax.set_ylabel('Directional Accuracy (%)')
    ax.set_xticks(range(len(systems)))
    ax.set_xticklabels(systems, rotation=45, ha='right')
    ax.set_title('Directional Prediction Accuracy')
    ax.set_ylim(0, 1)

    best_idx = np.argmax(directional_accs)
    bars[best_idx].set_color('gold')

    # Mean magnitude error
    ax = axes[2]
    bars = ax.bar(range(len(systems)), errors, alpha=0.7, color='salmon')
    ax.set_ylabel('Mean Magnitude Error (%)')
    ax.set_xticks(range(len(systems)))
    ax.set_xticklabels(systems, rotation=45, ha='right')
    ax.set_title('Prediction Error (Lower = Better)')

    # Color best (lowest error)
    best_idx = np.argmin(errors)
    bars[best_idx].set_color('gold')

    plt.tight_layout()
    output_file = output_dir / "ground_truth_accuracy.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved: {output_file}")


def plot_effect_sizes(
    analysis: Dict[str, Any],
    output_dir: Path,
):
    """
    Visualize effect sizes (Cohen's d) for comparisons.
    """
    logger.info("Generating effect size plot...")

    comp = analysis['statistical_comparison']
    ttests = comp['ttests']

    # Extract effect sizes
    comparisons = []
    effect_sizes = []
    p_values = []

    for ttest in ttests:
        comp_name = f"{ttest['group1_name']} vs\n{ttest['group2_name']}\n({ttest['metric_name']})"
        comparisons.append(comp_name)
        effect_sizes.append(ttest['cohens_d'])
        p_values.append(ttest['p_value'])

    # Sort by absolute effect size
    sorted_indices = np.argsort(np.abs(effect_sizes))[::-1][:20]  # Top 20

    fig, ax = plt.subplots(figsize=(12, 10))

    y_pos = np.arange(len(sorted_indices))
    colors = ['red' if p < 0.05 else 'gray' for i, p in enumerate(p_values) if i in sorted_indices]

    ax.barh(
        y_pos,
        [effect_sizes[i] for i in sorted_indices],
        color=colors,
        alpha=0.7,
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels([comparisons[i] for i in sorted_indices], fontsize=8)
    ax.set_xlabel("Cohen's d (Effect Size)")
    ax.set_title("Effect Sizes (Top 20 Comparisons)\nRed = Statistically Significant (p < 0.05)")

    # Add effect size interpretation lines
    ax.axvline(0.2, color='green', linestyle='--', alpha=0.5, label='Small')
    ax.axvline(0.5, color='orange', linestyle='--', alpha=0.5, label='Medium')
    ax.axvline(0.8, color='red', linestyle='--', alpha=0.5, label='Large')
    ax.axvline(-0.2, color='green', linestyle='--', alpha=0.5)
    ax.axvline(-0.5, color='orange', linestyle='--', alpha=0.5)
    ax.axvline(-0.8, color='red', linestyle='--', alpha=0.5)

    ax.legend()

    plt.tight_layout()
    output_file = output_dir / "effect_sizes.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved: {output_file}")


def plot_confidence_intervals(
    analysis: Dict[str, Any],
    output_dir: Path,
):
    """
    Plot confidence intervals for key metrics.
    """
    logger.info("Generating confidence interval plot...")

    comp = analysis['statistical_comparison']

    # Focus on latency and cost
    metrics = ['latency_seconds', 'total_cost']
    metric_labels = ['Latency (seconds)', 'Cost (USD)']

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
        ax = axes[idx]

        # Get all ttests for this metric
        relevant_tests = [t for t in comp['ttests'] if t['metric_name'] == metric]

        if not relevant_tests:
            continue

        # Extract unique systems and their stats
        system_stats = {}
        for test in relevant_tests:
            if test['group1_name'] not in system_stats:
                system_stats[test['group1_name']] = {
                    'mean': test['mean1'],
                    'ci_95': test['ci_95'],
                }
            if test['group2_name'] not in system_stats:
                system_stats[test['group2_name']] = {
                    'mean': test['mean2'],
                    'ci_95': test['ci_95'],
                }

        systems = list(system_stats.keys())
        means = [system_stats[s]['mean'] for s in systems]

        # Plot points with error bars
        y_pos = np.arange(len(systems))
        ax.errorbar(
            means,
            y_pos,
            xerr=[[m - system_stats[s]['ci_95'][0] for s, m in zip(systems, means)],
                  [system_stats[s]['ci_95'][1] - m for s, m in zip(systems, means)]],
            fmt='o',
            markersize=8,
            capsize=5,
            capthick=2,
        )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(systems)
        ax.set_xlabel(label)
        ax.set_title(f"{label} with 95% Confidence Intervals")
        ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    output_file = output_dir / "confidence_intervals.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved: {output_file}")


def main():
    """Generate all visualizations."""
    parser = argparse.ArgumentParser(
        description="Generate visualizations from experiment results"
    )
    parser.add_argument(
        "--analysis-file",
        type=str,
        required=True,
        help="Path to analysis JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./visualizations",
        help="Output directory for plots",
    )

    args = parser.parse_args()

    analysis_file = Path(args.analysis_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    if not analysis_file.exists():
        print(f"Error: Analysis file not found: {analysis_file}")
        return

    print("\n" + "="*80)
    print("VISUALIZATION GENERATOR")
    print("="*80)
    print(f"\nAnalysis File: {analysis_file}")
    print(f"Output Directory: {output_dir}")

    # Load analysis
    analysis = load_analysis(analysis_file)

    # Generate all plots
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS...")
    print("="*80 + "\n")

    plot_performance_comparison(analysis, output_dir)
    plot_statistical_significance(analysis, output_dir)
    plot_ground_truth_accuracy(analysis, output_dir)
    plot_effect_sizes(analysis, output_dir)
    plot_confidence_intervals(analysis, output_dir)

    print("\n" + "="*80)
    print("ALL VISUALIZATIONS GENERATED")
    print("="*80)
    print(f"\nSaved to: {output_dir}")
    print("\nGenerated files:")
    for file in output_dir.glob("*.png"):
        print(f"  - {file.name}")


if __name__ == "__main__":
    main()
