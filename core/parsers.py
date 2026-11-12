"""requirements.txt oxuyan parser."""
from __future__ import annotations

import re
from pathlib import Path


_PKG_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)"
    r"(?:\[[^\]]*\])?"
    r"(?:[<>=!~].*)?$"
)


def parse_requirements(path: str | Path) -> list[str]:
    """requirements.txt-dən təmiz paket adlarını qaytarır."""
    packages: list[str] = []
    text = Path(path).read_text(encoding="utf-8")

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith(("-", "git+", "http://", "https://")):
            continue

        match = _PKG_RE.match(line)
        if not match:
            continue

        name = match.group("name")
        normalized = name.lower().replace("_", "-").replace(".", "-")
        packages.append(normalized)

    seen: set[str] = set()
    unique: list[str] = []
    for pkg in packages:
        if pkg not in seen:
            seen.add(pkg)
            unique.append(pkg)
    return unique


def parse_package_json(path: str | Path) -> list[str]:
    """package.json-dən bütün asılılıqları çıxarır.

    Hansı sahələr oxunur:
      - dependencies
      - devDependencies
      - peerDependencies
      - optionalDependencies

    Scoped paketlər (@scope/name) dəstəklənir.
    """
    import json

    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)

    fields = (
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
    )

    packages: list[str] = []
    seen: set[str] = set()

    for field in fields:
        section = data.get(field) or {}
        if not isinstance(section, dict):
            continue
        for name in section.keys():
            # npm adları case-sensitive-dir, lower etmirik.
            if name in seen:
                continue
            seen.add(name)
            packages.append(name)

    return packages
