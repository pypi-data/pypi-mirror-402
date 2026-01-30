#!/usr/bin/env python3
"""
Global random-number-management utilities for LRDBenchmark.

This module centralises RNG initialisation so that all stochastic components
share a consistent source of randomness.  Consumers can request named streams
to obtain deterministic sub-generators suitable for reproducible experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional

import numpy as np

DEFAULT_GLOBAL_SEED = 1729


@dataclass(frozen=True)
class RNGSnapshot:
    """Light-weight description of the RNG state for provenance reporting."""

    global_seed: int
    child_seeds: Dict[str, int]


class RandomManager:
    """Singleton-style manager that hands out deterministic RNG streams."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._global_seed = DEFAULT_GLOBAL_SEED
        self._global_rng = np.random.default_rng(self._global_seed)
        self._child_generators: Dict[str, np.random.Generator] = {}
        self._child_seeds: Dict[str, int] = {}

    def initialise(self, seed: Optional[int]) -> None:
        """
        Reset the global RNG with the provided seed (or the default).
        """
        with self._lock:
            resolved_seed = self._global_seed if seed is None else int(seed)
            self._global_seed = resolved_seed
            self._global_rng = np.random.default_rng(self._global_seed)
            self._child_generators.clear()
            self._child_seeds.clear()

    def global_seed(self) -> int:
        return self._global_seed

    def spawn_seed(self, name: str, *, seed: Optional[int] = None) -> int:
        with self._lock:
            if seed is not None:
                resolved = int(seed)
            elif name in self._child_seeds:
                resolved = self._child_seeds[name]
            else:
                resolved = int(self._global_rng.integers(0, 2**63 - 1))
            self._child_seeds[name] = resolved
            return resolved

    def spawn_generator(
        self, name: str, *, seed: Optional[int] = None
    ) -> np.random.Generator:
        with self._lock:
            if seed is not None:
                resolved_seed = int(seed)
            elif name in self._child_generators:
                return self._child_generators[name]
            else:
                resolved_seed = self.spawn_seed(name)

            generator = np.random.default_rng(resolved_seed)
            self._child_generators[name] = generator
            self._child_seeds[name] = resolved_seed
            return generator

    def snapshot(self) -> RNGSnapshot:
        with self._lock:
            return RNGSnapshot(
                global_seed=self._global_seed,
                child_seeds=dict(self._child_seeds),
            )


_MANAGER = RandomManager()


def get_random_manager() -> RandomManager:
    return _MANAGER


def initialise_global_rng(seed: Optional[int]) -> RandomManager:
    manager = get_random_manager()
    manager.initialise(seed)
    return manager