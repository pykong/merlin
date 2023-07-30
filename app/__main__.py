import json
import pprint
import sys
from dataclasses import asdict

sys.dont_write_bytecode = True

from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any, Final, Iterable

from app.config import Config
from app.loop import loop
from app.utils.file_utils import ensure_dirs

EXPERIMENT_DIR: Final[Path] = Path("experiments")
RESULTS_DIR: Final[Path] = Path("results")
NUM_WORKERS: Final[int] = 2


def copy_orginal_files(files: Iterable[Path], dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        destination = dest_dir / file.name
        destination.write_bytes(file.read_bytes())


def unpack_variants(raw_dict: dict[str, Any]) -> list[dict[str, Any]]:
    if "variants" not in raw_dict:
        return [raw_dict]
    variants = raw_dict.pop("variants")
    variants = [c for v in variants for c in unpack_variants(v)]
    return [raw_dict | v for v in variants]


def load_experiments(files: Iterable[Path]) -> list[Config]:
    raw_dicts = [json.loads(f.read_text()) for f in files]
    return [Config(**c) for d in raw_dicts for c in unpack_variants(d)]


def validate_variants(variants: list[Config]) -> None:
    if not variants:
        raise ValueError("No experiment files found. Exiting.")
    if len(variants) != len(set(variants)):
        raise ValueError("Variants found not to be unique.")


def save_experiment(config: Config, file_path: Path) -> None:
    with open(file_path, "w") as f:
        json.dump(asdict(config), f, indent=4)


def pretty_print_config(config: Config) -> None:
    print(f"Conducting experiment with:")
    pprint.pprint(asdict(config), sort_dicts=False, indent=2)
    print("\n")


def train_variant(variant):
    # ensure result dirs
    exp_result_dir = RESULTS_DIR / variant.experiment_id
    result_dir = exp_result_dir / f"{variant.run_id}_{variant.variant_id}"
    ensure_dirs(exp_result_dir, result_dir)

    # persist config for reproducibility
    save_experiment(variant, result_dir / "variant.json")

    # start training
    loop(variant, result_dir)


def train():
    # glob experiment files
    experiment_files = [e for e in EXPERIMENT_DIR.glob("*.json")]
    variants = load_experiments(experiment_files)

    # some validation
    validate_variants(variants)

    with Pool(NUM_WORKERS) as p:
        # run each experiment in parallel
        p.map(train_variant, variants)


if __name__ == "__main__":
    train()
