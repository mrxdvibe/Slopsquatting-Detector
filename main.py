"""Slopsquatting Detector — CLI giriş nöqtəsi."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.parsers import parse_package_json, parse_requirements
from core.lockfile import parse_package_lock
from core.registry import check_many, check_many_npm, check_many_concurrent
from core.risk import Risk, assess
from ui.render import render, render_json


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="slopsquatting-detector",
        description="AI-nin uydurduğu zəhərli paketləri tapır (PyPI + npm).",
    )
    p.add_argument(
        "manifest",
        nargs="?",
        default="requirements.txt",
        help="requirements.txt, package.json və ya package-lock.json yolu",
    )
    p.add_argument(
        "--fail-on-danger",
        action="store_true",
        help="TƏHLÜKƏ tapılarsa exit code 1 qaytar (CI üçün).",
    )
    p.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Çıxış formatı: table (default) və ya json (CI üçün).",
    )
    p.add_argument(
        "--concurrent",
        action="store_true",
        help="Böyük fayllar üçün paralel yoxlama (ThreadPoolExecutor).",
    )
    return p


def detect_ecosystem(path: Path) -> str:
    name = path.name.lower()
    
    # Lock faylı
    if name == "package-lock.json" or name.endswith("-lock.json"):
        return "npm-lock"
        
    if name == "package.json" or name.endswith(".json"):
        return "npm"
    if name.startswith("requirements") and name.endswith(".txt"):
        return "pypi"
    if name.endswith(".txt"):
        return "pypi"
        
    raise ValueError(
        f"manifest növü tanınmadı: {path.name} "
        f"(gözlənilir: requirements*.txt, package.json və ya package-lock.json)"
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = Path(args.manifest)

    if not manifest.exists():
        print(f"Xəta: fayl tapılmadı — {manifest}", file=sys.stderr)
        return 2

    try:
        ecosystem = detect_ecosystem(manifest)
    except ValueError as exc:
        print(f"Xəta: {exc}", file=sys.stderr)
        return 2

    # Parser seçimi
    if ecosystem == "pypi":
        packages = parse_requirements(manifest)
        registry_label = "PyPI"
        check_ecosystem = "pypi"
    elif ecosystem == "npm":
        packages = parse_package_json(manifest)
        registry_label = "npm"
        check_ecosystem = "npm"
    else: # npm-lock
        packages = parse_package_lock(manifest)
        registry_label = "npm (lockfile)"
        check_ecosystem = "npm"

    if not packages:
        msg = f"Xəbərdarlıq: {manifest.name} içində heç bir paket tapılmadı."
        if args.format == "json":
            print('{"summary": {"total": 0}, "packages": []}')
        else:
            print(msg, file=sys.stderr)
        return 0

    # Status mesajı
    status_msg = f"[i] Registry: {registry_label} | {len(packages)} paket yoxlanılır..."
    if args.concurrent and len(packages) > 20:
        status_msg += " (paralel rejim)"
    
    if args.format == "table":
        print(status_msg)
    else:
        print(status_msg, file=sys.stderr)

    # Yoxlama məntiqi
    if args.concurrent and len(packages) > 20:
        checks = check_many_concurrent(packages, ecosystem=check_ecosystem, max_workers=10)
    else:
        if check_ecosystem == "pypi":
            checks = check_many(packages)
        else:
            checks = check_many_npm(packages)

    verdicts = [assess(c) for c in checks]

    if args.format == "json":
        render_json(verdicts)
    else:
        render(verdicts)

    if args.fail_on_danger and any(v.risk is Risk.DANGER for v in verdicts):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
