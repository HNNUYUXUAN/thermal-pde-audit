#!/usr/bin/env python3
"""Inspect the installed UnitaryLab PDE surface without executing algorithms."""

from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

SEARCH_TERMS = (
    "heat",
    "thermal",
    "diffusion",
    "schrodingerization",
    "advection",
    "equation",
    "pde",
)
CLASS_CANDIDATES = (
    (
        "unitarylab_algorithms.schrodingerization.equation_heat.algorithm",
        "HeatEquationAlgorithm",
    ),
    (
        "unitarylab_algorithms.schrodingerization.equation_heat2d.algorithm",
        "Heat2dEquationAlgorithm",
    ),
    (
        "unitarylab_algorithms.schrodingerization.equation_advection.algorithm",
        "AdvectionEquationAlgorithm",
    ),
)


def safe_signature(value: Any) -> str:
    try:
        return str(inspect.signature(value))
    except (TypeError, ValueError) as exc:
        return f"<signature unavailable: {type(exc).__name__}: {exc}>"


def print_module_summary(module: ModuleType) -> None:
    print(f"module={module.__name__}")
    print(f"module_file={getattr(module, '__file__', None)}")
    names = sorted(name for name in dir(module) if not name.startswith("__"))
    print(f"dir={json.dumps(names, ensure_ascii=False)}")


def print_candidate(module_name: str, class_name: str) -> None:
    print(f"\n=== candidate {module_name}:{class_name} ===")
    try:
        module = importlib.import_module(module_name)
        print_module_summary(module)
        cls = getattr(module, class_name)
        print(f"class_signature={safe_signature(cls)}")
        for method_name in ("run", "solve", "_solve_classical", "_solve_trotter", "_solve_block"):
            method = getattr(cls, method_name, None)
            if method is not None:
                print(f"{method_name}_signature={safe_signature(method)}")
        print("class_source_begin")
        print(inspect.getsource(cls))
        print("class_source_end")
    except Exception as exc:
        print(f"candidate_error={type(exc).__name__}: {exc}")


def print_setup_files(package_root: Path) -> None:
    print("\n=== setup files ===")
    for setup in sorted(package_root.rglob("setup.json")):
        lowered = str(setup).lower()
        if any(term in lowered for term in ("heat", "advection")):
            print(f"setup_path={setup}")
            try:
                data = json.loads(setup.read_text(encoding="utf-8"))
                print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
            except Exception as exc:
                print(f"setup_error={type(exc).__name__}: {exc}")


def print_matching_files(package_root: Path) -> None:
    print("\n=== package filename matches ===")
    for path in sorted(package_root.rglob("*")):
        if path.is_file() and any(term in str(path).lower() for term in SEARCH_TERMS):
            print(path)

    print("\n=== package text matches ===")
    suffixes = {".py", ".json", ".md", ".txt"}
    match_count = 0
    for path in sorted(package_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            lowered = line.lower()
            if any(term in lowered for term in SEARCH_TERMS):
                print(f"{path}:{line_number}:{line[:500]}")
                match_count += 1
                if match_count >= 500:
                    print("text_match_limit_reached=500")
                    return


def main() -> int:
    print(f"python={sys.executable}")
    root_module = importlib.import_module("unitarylab_algorithms")
    print_module_summary(root_module)
    module_file = root_module.__file__
    if module_file is None:
        raise RuntimeError("unitarylab_algorithms has no filesystem location")
    package_root = Path(module_file).resolve().parent
    print(f"package_root={package_root}")

    print("\n=== pkgutil modules ===")
    for info in sorted(pkgutil.walk_packages(root_module.__path__, root_module.__name__ + "."), key=lambda x: x.name):
        lowered = info.name.lower()
        if any(term in lowered for term in SEARCH_TERMS):
            print(info.name)

    for module_name, class_name in CLASS_CANDIDATES:
        print_candidate(module_name, class_name)

    try:
        schro = importlib.import_module("unitarylab.library.equation.schrodingerization")
        print("\n=== unitarylab schrodingerization ===")
        print_module_summary(schro)
        for name in ("schro_classical", "schro_trotter", "circuit_classical"):
            value = getattr(schro, name, None)
            print(f"{name}_signature={safe_signature(value)}")
            if value is not None:
                print(f"{name}_source_begin")
                print(inspect.getsource(value))
                print(f"{name}_source_end")
    except Exception as exc:
        print(f"schrodingerization_error={type(exc).__name__}: {exc}")

    print_setup_files(package_root)
    print_matching_files(package_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
