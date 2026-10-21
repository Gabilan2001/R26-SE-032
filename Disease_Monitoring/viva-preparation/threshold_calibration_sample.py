"""
Standalone Grid Search example for TomatoDoc Component 3 viva preparation.

This file is intentionally separate from the production application.
The dataset below is synthetic and is included only to demonstrate the
threshold-calibration procedure.

Run:
    python viva-preparation/threshold_calibration_sample.py

To use real calibration data:
1. Replace SYNTHETIC_DATASET with affected-area fractions and independently
   verified LOW/HIGH labels.
2. Keep the labels separate from any final evaluation/test dataset.
3. Confirm that each fraction was produced by the intended affected-area
   estimator or supplied from a documented measurement process.
4. Re-run the script and record the results with the dataset provenance.

The demo result must not be reported as a TomatoDoc research result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


# A single calibration sample contains an affected-area fraction in the range
# 0.0 to 1.0 and an independently supplied reference label.
@dataclass(frozen=True)
class CalibrationSample:
    affected_area_fraction: float
    reference_label: str


# This dataset is deliberately synthetic. It is not taken from TomatoDoc,
# does not represent expert annotations, and must not be used as evidence.
SYNTHETIC_DATASET: tuple[CalibrationSample, ...] = (
    CalibrationSample(0.05, "LOW"),
    CalibrationSample(0.08, "LOW"),
    CalibrationSample(0.15, "LOW"),
    CalibrationSample(0.22, "LOW"),
    CalibrationSample(0.18, "HIGH"),
    CalibrationSample(0.28, "HIGH"),
    CalibrationSample(0.33, "HIGH"),
    CalibrationSample(0.38, "HIGH"),
    CalibrationSample(0.45, "HIGH"),
)


# Grid Search tests these candidate thresholds, from 10% through 40%.
CANDIDATE_THRESHOLDS: tuple[float, ...] = tuple(
    percentage / 100 for percentage in range(10, 41, 5)
)


def classify_from_threshold(
    affected_area_fraction: float, threshold: float
) -> str:
    """Classify one sample using the same strict-greater-than rule as production."""
    return "HIGH" if affected_area_fraction > threshold else "LOW"


def calculate_metrics(
    reference_labels: Sequence[str],
    predicted_labels: Sequence[str],
) -> dict[str, float]:
    """Calculate binary classification metrics with HIGH as the positive class."""
    if len(reference_labels) != len(predicted_labels):
        raise ValueError("Reference and predicted label counts must match.")
    if not reference_labels:
        raise ValueError("At least one labelled sample is required.")

    true_positive = sum(
        reference == "HIGH" and predicted == "HIGH"
        for reference, predicted in zip(reference_labels, predicted_labels)
    )
    true_negative = sum(
        reference == "LOW" and predicted == "LOW"
        for reference, predicted in zip(reference_labels, predicted_labels)
    )
    false_positive = sum(
        reference == "LOW" and predicted == "HIGH"
        for reference, predicted in zip(reference_labels, predicted_labels)
    )
    false_negative = sum(
        reference == "HIGH" and predicted == "LOW"
        for reference, predicted in zip(reference_labels, predicted_labels)
    )

    accuracy = (true_positive + true_negative) / len(reference_labels)
    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def evaluate_threshold(
    dataset: Iterable[CalibrationSample],
    threshold: float,
) -> dict[str, float]:
    """Generate predictions and calculate metrics for one candidate threshold."""
    samples = tuple(dataset)
    reference_labels = [sample.reference_label for sample in samples]
    predicted_labels = [
        classify_from_threshold(sample.affected_area_fraction, threshold)
        for sample in samples
    ]
    metrics = calculate_metrics(reference_labels, predicted_labels)
    return {"threshold": threshold, **metrics}


def select_best_threshold(
    results: Sequence[dict[str, float]],
) -> dict[str, float]:
    """Select the threshold with highest F1, then recall, then lower threshold."""
    if not results:
        raise ValueError("At least one threshold result is required.")

    # F1 is the primary selection metric. The other values make ties
    # deterministic and document the calibration decision.
    return max(
        results,
        key=lambda result: (
            result["f1"],
            result["recall"],
            -result["threshold"],
        ),
    )


def print_dataset(dataset: Sequence[CalibrationSample]) -> None:
    """Print the synthetic inputs so the demonstration is transparent."""
    print("Synthetic calibration samples:")
    print("  #   affected area   reference label")
    for index, sample in enumerate(dataset, start=1):
        print(
            f"  {index:>2}      {sample.affected_area_fraction * 100:>5.1f}%"
            f"          {sample.reference_label}"
        )
    print()


def print_comparison_table(results: Sequence[dict[str, float]]) -> None:
    """Print metrics for every candidate threshold."""
    print("Grid Search comparison:")
    print(
        " threshold   accuracy   precision   recall      F1"
    )
    print(
        " ---------   --------   ---------   ------   ------"
    )
    for result in results:
        print(
            f"   {result['threshold'] * 100:>5.1f}%      "
            f"{result['accuracy']:.4f}     "
            f"{result['precision']:.4f}      "
            f"{result['recall']:.4f}   "
            f"{result['f1']:.4f}"
        )
    print()


def print_example_predictions(
    examples: Sequence[float],
    threshold: float,
) -> None:
    """Show how the selected demonstration threshold classifies new examples."""
    print(
        f"Example predictions using the selected demonstration threshold "
        f"({threshold * 100:.1f}%):"
    )
    for fraction in examples:
        prediction = classify_from_threshold(fraction, threshold)
        print(f"  {fraction * 100:>5.1f}% affected area -> {prediction}")
    print()


def main() -> None:
    """Run the synthetic Grid Search demonstration."""
    print("SYNTHETIC DEMONSTRATION ONLY — NOT REAL TOMATODOC RESULTS")
    print("=" * 64)
    print(
        "The selected threshold below is illustrative and must not be "
        "reported as the optimized research threshold."
    )
    print()

    print_dataset(SYNTHETIC_DATASET)

    # Evaluate every candidate threshold against the reference labels.
    results = [
        evaluate_threshold(SYNTHETIC_DATASET, threshold)
        for threshold in CANDIDATE_THRESHOLDS
    ]
    print_comparison_table(results)

    # Select the candidate with the highest F1-score.
    best = select_best_threshold(results)
    print(
        f"Best synthetic demonstration threshold by F1: "
        f"{best['threshold'] * 100:.1f}%"
    )
    print(
        f"Accuracy={best['accuracy']:.4f}, "
        f"Precision={best['precision']:.4f}, "
        f"Recall={best['recall']:.4f}, "
        f"F1={best['f1']:.4f}"
    )
    print()

    # Demonstrate the selected threshold on several example percentages.
    print_example_predictions((0.12, 0.20, 0.30, 0.42), best["threshold"])

    print("Important:")
    print("- These values are synthetic and illustrative only.")
    print("- They are not TomatoDoc accuracy, precision, recall, or F1 results.")
    print("- They do not prove that the existing 30% threshold is optimal.")
    print("- Real calibration requires verified labels and a separate final test set.")


if __name__ == "__main__":
    main()
