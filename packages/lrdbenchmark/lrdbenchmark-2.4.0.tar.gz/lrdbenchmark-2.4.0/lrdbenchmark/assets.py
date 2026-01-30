"""
Artifact management for pretrained models and configuration files.

This module centralises knowledge about large binary assets (joblib/pth files)
so we can keep the source repository lightweight while still providing an
easy, verified download path for users that need the pretrained estimators.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Optional, Sequence
from urllib.request import urlopen

LOGGER = logging.getLogger(__name__)

DEFAULT_ASSET_BASE_URL = os.environ.get(
    "LRDBENCHMARK_ASSET_BASE_URL",
    "https://github.com/dave2k77/lrdbenchmark/releases/download/v2.3.1-assets",
)

DEFAULT_CACHE_ROOT = Path(
    os.environ.get("LRDBENCHMARK_MODELS_DIR", Path.home() / ".cache" / "lrdbenchmark" / "models")
)

LOCAL_FALLBACK_DIRS: Sequence[Path] = (
    DEFAULT_CACHE_ROOT,
    Path(__file__).resolve().parent / "assets" / "models",  # Package assets
    Path.cwd() / "artifacts" / "models",
    Path.cwd() / "models",
    Path.cwd() / "lrdbenchmark" / "assets" / "models",  # Dev mode
)

CONFIG_ROOT = Path(__file__).resolve().parent / "model_configs"


@dataclass(frozen=True)
class Artifact:
    key: str
    filename: str
    sha256: str
    url: Optional[str] = None
    description: str = ""

    @property
    def resolved_url(self) -> str:
        if self.url:
            return self.url
        return f"{DEFAULT_ASSET_BASE_URL}/{self.filename}"


_RF_ARTIFACTS: Sequence[Artifact] = (
    Artifact(
        key="random_forest_estimator_fixed",
        filename="random_forest_estimator_fixed.joblib",
        sha256="1EA8BF89180117A84750CCDB5606FF2ABA897F071EC466BB4DE8E8CCC3995807",
        description="Scikit-learn RandomForestRegressor tuned for production benchmarks.",
    ),
    Artifact(
        key="random_forest_estimator",
        filename="random_forest_estimator.joblib",
        sha256="5ADEFF71AC15652DD084B63CAF9FEDB9B15DC9F5A62512E943E747C0968A70BF",
        description="Legacy RandomForest estimator checkpoint.",
    ),
)

_GB_ARTIFACTS: Sequence[Artifact] = (
    Artifact(
        key="gradient_boosting_estimator_fixed",
        filename="gradient_boosting_estimator_fixed.joblib",
        sha256="4D9C9F6CC97AB20BB406A92AD7F401DCF3D29C7DAF9EE22829F10470C140C258",
        description="Production-tuned GradientBoostingRegressor.",
    ),
    Artifact(
        key="gradient_boosting_estimator",
        filename="gradient_boosting_estimator.joblib",
        sha256="E02674DFC6233E24A7815BC218696F495571B229DCDD99221DDA61BEF774AFF7",
        description="Legacy GradientBoosting checkpoint.",
    ),
)

_SVR_ARTIFACTS: Sequence[Artifact] = (
    Artifact(
        key="svr_estimator_fixed",
        filename="svr_estimator_fixed.joblib",
        sha256="A0BD691360E6F7214CF9C9150C495764717FCC6435C75F11916CDD076D0822DE",
        description="Production-tuned Support Vector Regression model.",
    ),
    Artifact(
        key="svr_estimator",
        filename="svr_estimator.joblib",
        sha256="094710A53A602318A775BBE2AD147C8CAF327EFF46D187F0D67AE147D65B7E8B",
        description="Legacy SVR checkpoint.",
    ),
)

_FFN_ARTIFACTS: Sequence[Artifact] = (
    Artifact(
        key="feedforwardnetwork_neural_network",
        filename="feedforwardnetwork_neural_network.pth",
        sha256="6E706A7D329E2225F15A7462E3E67CFEADD81D7B47783F95AEF94BD5B7D1EE1B",
        description="Reference feedforward neural network weights.",
    ),
)

MODEL_MANIFEST: Dict[str, Sequence[Artifact]] = {
    "random_forest_estimator": (
        *_RF_ARTIFACTS,
    ),
    "gradient_boosting_estimator": (
        *_GB_ARTIFACTS,
    ),
    "svr_estimator": (
        *_SVR_ARTIFACTS,
    ),
    "feedforwardnetwork": (
        *_FFN_ARTIFACTS,
    ),
}

MODEL_MANIFEST.update(
    {
        "random_forest_estimator_fixed": (_RF_ARTIFACTS[0],),
        "gradient_boosting_estimator_fixed": (_GB_ARTIFACTS[0],),
        "svr_estimator_fixed": (_SVR_ARTIFACTS[0],),
        "feedforwardnetwork_neural_network": _FFN_ARTIFACTS,
    }
)


def get_cache_dir() -> Path:
    """Ensure the default cache directory exists and return it."""
    DEFAULT_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    return DEFAULT_CACHE_ROOT


def _candidate_paths(filename: str) -> List[Path]:
    paths: List[Path] = []
    for base in LOCAL_FALLBACK_DIRS:
        paths.append(base / filename)
    return paths


def _verify_sha256(file_path: Path, expected_hash: str) -> bool:
    if not file_path.exists():
        return False
    hasher = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    digest = hasher.hexdigest().upper()
    return digest == expected_hash.upper()


def _download_artifact(artifact: Artifact, destination: Path) -> bool:
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        LOGGER.info("Downloading %s from %s", artifact.filename, artifact.resolved_url)
        with urlopen(artifact.resolved_url) as response, destination.open("wb") as handle:
            handle.write(response.read())
        return True
    except Exception as exc:  # pragma: no cover - network failure reporting
        LOGGER.error("Failed to download %s: %s", artifact.filename, exc)
        return False


def ensure_model_artifact(model_key: str) -> Optional[Path]:
    """
    Ensure a pretrained model artifact is available locally.

    Returns the path to the first artefact in the manifest that can be located
    or successfully downloaded, otherwise ``None``.
    """
    entries = MODEL_MANIFEST.get(model_key)
    if not entries:
        LOGGER.warning("Unknown model key '%s'", model_key)
        return None

    for artifact in entries:
        # First, try to find existing local files (skip SHA verification for local dev)
        for candidate in _candidate_paths(artifact.filename):
            if candidate.exists():
                LOGGER.info("Found local model at %s (skipping hash verification)", candidate)
                return candidate
        
        # Also check without "_fixed" suffix for locally trained models
        alt_filename = artifact.filename.replace("_fixed", "")
        if alt_filename != artifact.filename:
            for candidate in _candidate_paths(alt_filename):
                if candidate.exists():
                    LOGGER.info("Found local model at %s (alternate name)", candidate)
                    return candidate

        # Fall back to verified download
        cache_target = get_cache_dir() / artifact.filename
        if cache_target.exists() and not _verify_sha256(cache_target, artifact.sha256):
            LOGGER.warning("Cached artifact %s has wrong checksum; deleting", cache_target)
            cache_target.unlink(missing_ok=True)

        if _download_artifact(artifact, cache_target) and _verify_sha256(cache_target, artifact.sha256):
            return cache_target

    LOGGER.error("Unable to provide pretrained artifact for key '%s'", model_key)

    return None


def ensure_all_artifacts(keys: Optional[Iterable[str]] = None) -> MutableMapping[str, Path]:
    """Download (if needed) and return paths for all requested model keys."""
    resolved: MutableMapping[str, Path] = {}
    for key in keys or MODEL_MANIFEST.keys():
        path = ensure_model_artifact(key)
        if path:
            resolved[key] = path
    return resolved


def list_available_artifacts() -> Dict[str, Sequence[Artifact]]:
    """Expose the manifest for CLI tooling/documentation."""
    return MODEL_MANIFEST


def get_model_config_path(filename: str) -> Optional[Path]:
    """
    Locate a packaged neural-network configuration JSON.

    Parameters
    ----------
    filename:
        The JSON filename, e.g. ``"lstm_neural_network_config.json"``.
    """
    candidate = CONFIG_ROOT / filename
    if candidate.exists():
        return candidate

    for base in LOCAL_FALLBACK_DIRS:
        alt = base / filename
        if alt.exists():
            return alt

    LOGGER.warning("Configuration file %s not found in packaged assets", filename)
    return None


def get_artifacts_cache_hint() -> str:
    """Return a human-readable description of where assets are stored."""
    return str(get_cache_dir())

