"""package-lock.json faylını oxuyan parser (npm v6 və v7+ dəstəyi)."""
from __future__ import annotations

import json
from pathlib import Path


def parse_package_lock(path: str | Path) -> list[str]:
    """package-lock.json-dən BÜTÜN (transitive daxil) paket adlarını çıxarır.
    
    Dəstəklənən formatlar:
      - npm v7+ ("packages" açarı istifadə olunur)
      - npm v6 ("dependencies" açarı istifadə olunur)
    """
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)

    packages: list[str] = []
    seen: set[str] = set()

    def add(name: str):
        if name and name not in seen:
            seen.add(name)
            packages.append(name)

    # npm v7+ formatı
    if "packages" in data:
        for pkg_path, meta in data["packages"].items():
            # "" (root layihə) və ya "node_modules/" ilə başlamayanları atla
            if not pkg_path.startswith("node_modules/"):
                continue
            
            # Yalnız son node_modules-dən sonrakı hissəni götürürük.
            # Məsələn: "node_modules/express/node_modules/accepts" -> "accepts"
            parts = pkg_path.split("node_modules/")
            name = parts[-1].strip("/")
            
            if name:
                add(name)
                
    # npm v6 formatı (və ya "packages" olmayan köhnə fayllar)
    elif "dependencies" in data:
        def walk_deps(deps: dict):
            for name, meta in deps.items():
                add(name)
                if isinstance(meta, dict) and "dependencies" in meta:
                    walk_deps(meta["dependencies"])
                    
        walk_deps(data["dependencies"])

    return packages
