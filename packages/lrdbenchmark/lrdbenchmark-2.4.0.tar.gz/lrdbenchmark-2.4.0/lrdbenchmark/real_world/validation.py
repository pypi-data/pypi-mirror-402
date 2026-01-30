#!/usr/bin/env python3
"""
Deterministic real-world validation workflow for LRDBenchmark.

This module no longer downloads data from external providers.  Instead it uses
lightweight, reproducible surrogate datasets that emulate the qualitative
behaviour of financial, physiological, climate, network, and biophysical
signals.  All randomness is driven through the global RNG manager so that every
run can be reproduced exactly by reusing the same seed.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from lrdbenchmark.analysis.temporal.rs.rs_estimator_unified import RSEstimator
from lrdbenchmark.analysis.temporal.dfa.dfa_estimator_unified import DFAEstimator
from lrdbenchmark.analysis.spectral.whittle.whittle_estimator_unified import (
    WhittleEstimator,
)
from lrdbenchmark.analytics.provenance import ProvenanceTracker
from lrdbenchmark.real_world.datasets import dataset_map
from lrdbenchmark.robustness.adaptive_preprocessor import AdaptiveDataPreprocessor
from lrdbenchmark.random_manager import get_random_manager, initialise_global_rng


@dataclass
class DatasetRecord:
    name: str
    domain: str
    description: str
    seed: int
    values: np.ndarray


class RealWorldDataValidator:
    """Run deterministic validation sweeps across packaged surrogate datasets."""

    def __init__(
        self,
        results_dir: Path | str = "results/real_world_validation",
        seed: Optional[int] = None,
    ) -> None:
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Initialise RNG manager (preserving previously configured seed if None).
        initialise_global_rng(seed)
        self.random_manager = get_random_manager()
        self.datasets = self._prepare_datasets()
        self.estimators = self._initialise_estimators()
        self.provenance_tracker = ProvenanceTracker()
        self.data_preprocessor = AdaptiveDataPreprocessor()
        self.domain_profiles = {
            "physiological_eeg": ("eeg", 256.0),
            "physiological_hrv": ("hrv", 4.0),
        }

    # ------------------------------------------------------------------ helpers
    def _prepare_datasets(self) -> Dict[str, DatasetRecord]:
        records: Dict[str, DatasetRecord] = {}
        for spec in dataset_map().values():
            stream_name = f"dataset:{spec.name}"
            dataset_seed = self.random_manager.spawn_seed(
                stream_name, seed=spec.base_seed
            )
            rng = self.random_manager.spawn_generator(stream_name, seed=dataset_seed)
            values = spec.generator(spec.default_length, rng)
            records[spec.name] = DatasetRecord(
                name=spec.name,
                domain=spec.domain,
                description=spec.description,
                seed=dataset_seed,
                values=values,
            )
        return records

    def _initialise_estimators(self):
        return {
            "R/S": RSEstimator(),
            "DFA": DFAEstimator(),
            "Whittle": WhittleEstimator(),
        }

    # ---------------------------------------------------------------- evaluation
    def _evaluate_dataset(
        self, record: DatasetRecord
    ) -> Tuple[Dict[str, Dict[str, object]], Optional[Dict[str, object]]]:
        results: Dict[str, Dict[str, object]] = {}
        domain_profile = self.domain_profiles.get(record.name)
        if domain_profile is not None:
            domain_label, fs = domain_profile
            processed_values, domain_meta = self.data_preprocessor.preprocess(
                record.values,
                domain=domain_label,
                sampling_rate_hz=fs,
            )
        else:
            processed_values = record.values
            domain_meta = None

        for name, estimator in self.estimators.items():
            try:
                outcome = estimator.estimate(processed_values)
                results[name] = {
                    "success": True,
                    "hurst_parameter": outcome.get("hurst_parameter"),
                    "r_squared": outcome.get("r_squared"),
                    "diagnostics": outcome.get("diagnostics"),
                }
            except Exception as exc:  # pragma: no cover - defensive
                results[name] = {"success": False, "error": str(exc)}
        return results, domain_meta

    # ---------------------------------------------------------------- persistence
    def _persist_outputs(self, summary: Dict[str, object], timestamp: str) -> None:
        run_dir = self.results_dir / f"run_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)

        summary_path = run_dir / "real_world_validation_summary.json"
        with summary_path.open("w") as fp:
            json.dump(summary, fp, indent=2, default=float)

        # Persist datasets for downstream inspection
        datasets_dir = run_dir / "datasets"
        datasets_dir.mkdir(exist_ok=True)
        for record in self.datasets.values():
            np.savetxt(
                datasets_dir / f"{record.name}.csv",
                record.values,
                delimiter=",",
            )

    # ---------------------------------------------------------------- public API
    def run(self, persist: bool = True) -> Dict[str, object]:
        timestamp = datetime.utcnow().isoformat()
        dataset_results: List[Dict[str, object]] = []

        for record in self.datasets.values():
            estimates, domain_meta = self._evaluate_dataset(record)
            dataset_results.append(
                {
                    "name": record.name,
                    "domain": record.domain,
                    "description": record.description,
                    "random_seed": record.seed,
                    "length": int(len(record.values)),
                    "estimates": estimates,
                    "preprocessing": domain_meta,
                }
            )

        rng_snapshot = self.random_manager.snapshot()
        provenance = self.provenance_tracker.capture_provenance(
            {
                "timestamp": timestamp,
                "benchmark_type": "real_world_validation",
                "total_datasets": len(dataset_results),
            },
            estimators_tested={"classical": list(self.estimators.keys())},
        )

        summary: Dict[str, object] = {
            "timestamp": timestamp,
            "global_seed": rng_snapshot.global_seed,
            "random_streams": rng_snapshot.child_seeds,
            "n_datasets": len(dataset_results),
            "datasets": dataset_results,
            "estimators": list(self.estimators.keys()),
            "provenance": provenance,
        }

        if persist:
            self._persist_outputs(summary, timestamp.replace(":", "").replace("-", ""))

        return summary


# --------------------------------------------------------------------------- CLI
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run deterministic real-world validation for LRDBenchmark."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results/real_world_validation"),
        help="Directory for validation artefacts (default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Global RNG seed. When omitted the configured default is used.",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Do not write artefacts to disk; useful for smoke tests.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> Dict[str, object]:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    validator = RealWorldDataValidator(results_dir=args.results_dir, seed=args.seed)
    summary = validator.run(persist=not args.no_persist)
    print(json.dumps(summary, indent=2, default=float))
    return summary


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

