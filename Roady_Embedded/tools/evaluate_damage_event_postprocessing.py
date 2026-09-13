"""Evaluate frame-immediate and tracked events against event-level time labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def metrics(events, intervals):
    matches = defaultdict(list)
    false_positives = []
    for event in events:
        found = None
        for index, (start, end) in enumerate(intervals):
            if start <= event <= end:
                found = index
                break
        if found is None:
            false_positives.append(event)
        else:
            matches[found].append(event)
    tp = sum(bool(matches[index]) for index in range(len(intervals)))
    fn = len(intervals) - tp
    duplicates = sum(max(0, len(values) - 1) for values in matches.values())
    fp = len(false_positives)
    return {
        "ground_truth_events": len(intervals),
        "true_positive_events": tp,
        "false_negative_events": fn,
        "false_positive_events": fp,
        "duplicate_events": duplicates,
        "event_recall": tp / len(intervals) if intervals else None,
        "event_precision": tp / (tp + fp + duplicates) if tp + fp + duplicates else None,
        "duplicate_rate_per_true_event": duplicates / len(intervals) if intervals else None,
    }


def main():
    args = parse_args()
    report = json.loads(args.benchmark.read_text(encoding="utf-8"))
    labels = defaultdict(list)
    with args.ground_truth.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            labels[row["video"]].append(
                (float(row["start_sec"]), float(row["end_sec"]))
            )
    results = []
    for video in report["videos"]:
        name = video["video"]
        intervals = labels[name]
        immediate = video["damage_detected_timestamps_sec"]
        tracked = [
            (item["first_seen_sec"] + item["last_seen_sec"]) / 2
            for item in video["tracked_event_details"]
        ]
        results.append(
            {
                "video": name,
                "baseline_immediate": metrics(immediate, intervals),
                "improved_tracking": metrics(tracked, intervals),
            }
        )
    args.output.write_text(
        json.dumps({"videos": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
