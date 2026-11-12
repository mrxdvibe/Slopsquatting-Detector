"""PyPI JSON API ilə real vaxt yoxlaması."""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed # <-- BUNU ƏLAVƏ ET
import requests


PYPI_JSON_URL = "https://pypi.org/pypi/{name}/json"
DEFAULT_TIMEOUT = 10
REQUEST_DELAY = 0.35
NPM_REGISTRY_URL = "https://registry.npmjs.org/{name}"


@dataclass
class PackageCheck:
    name: str
    exists: bool
    latest_version: str | None = None
    latest_upload: datetime | None = None
    release_count: int = 0
    error: str | None = None

    @property
    def age_days(self) -> int | None:
        if self.latest_upload is None:
            return None
        delta = datetime.now(timezone.utc) - self.latest_upload
        return max(delta.days, 0)


def check_pypi_package(name: str, session: requests.Session | None = None) -> PackageCheck:
    own_session = session is None
    if own_session:
        session = requests.Session()
        session.headers["User-Agent"] = "slopsquatting-detector/0.1"

    try:
        resp = session.get(
            PYPI_JSON_URL.format(name=name),
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        return PackageCheck(name=name, exists=False, error=f"network: {exc}")

    if resp.status_code == 404:
        return PackageCheck(name=name, exists=False)

    if resp.status_code != 200:
        return PackageCheck(
            name=name,
            exists=False,
            error=f"HTTP {resp.status_code}",
        )

    data = resp.json()
    info = data.get("info", {})
    releases = data.get("releases", {})

    latest_upload: datetime | None = None
    release_count = 0
    for files in releases.values():
        if files:
            release_count += 1
        for file_info in files:
            raw_time = file_info.get("upload_time_iso_8601")
            if not raw_time:
                continue
            try:
                dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            except ValueError:
                continue
            if latest_upload is None or dt > latest_upload:
                latest_upload = dt

    return PackageCheck(
        name=name,
        exists=True,
        latest_version=info.get("version"),
        latest_upload=latest_upload,
        release_count=release_count,
    )


def check_many(names: list[str]) -> list[PackageCheck]:
    session = requests.Session()
    session.headers["User-Agent"] = "slopsquatting-detector/0.1"

    results: list[PackageCheck] = []
    for i, name in enumerate(names):
        results.append(check_pypi_package(name, session=session))
        if i < len(names) - 1:
            time.sleep(REQUEST_DELAY)
    return results


def check_npm_package(name: str, session: requests.Session | None = None) -> PackageCheck:
    """Bir paketi npm registry-də yoxlayır.

    Qeyd: npm registry scoped paketlərdə (@scope/name) URL-də
    encode edilməlidir, çünki '/' xüsusi simvoldur.
    requests avtomatik encode edir, amma biz açıq şəkildə edirik.
    """
    from urllib.parse import quote

    own_session = session is None
    if own_session:
        session = requests.Session()
        session.headers["User-Agent"] = "slopsquatting-detector/0.1"

    encoded = quote(name, safe="")
    url = NPM_REGISTRY_URL.format(name=encoded)

    try:
        resp = session.get(
            url,
            timeout=DEFAULT_TIMEOUT,
            headers={"Accept": "application/json"},
        )
    except requests.RequestException as exc:
        return PackageCheck(name=name, exists=False, error=f"network: {exc}")

    if resp.status_code == 404:
        return PackageCheck(name=name, exists=False)

    if resp.status_code != 200:
        return PackageCheck(
            name=name,
            exists=False,
            error=f"HTTP {resp.status_code}",
        )

    data = resp.json()
    dist_tags = data.get("dist-tags") or {}
    latest_version = dist_tags.get("latest")
    versions = data.get("versions") or {}
    time_info = data.get("time") or {}

    # Ən son buraxılışın tarixi: time[latest_version]
    latest_upload: datetime | None = None
    if latest_version and latest_version in time_info:
        raw_time = time_info[latest_version]
        try:
            dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            latest_upload = dt
        except (ValueError, TypeError):
            pass

    # Versiya sayı (unpublish edilmişləri çıxaraq).
    release_count = len(versions)

    return PackageCheck(
        name=name,
        exists=True,
        latest_version=latest_version,
        latest_upload=latest_upload,
        release_count=release_count,
    )


def check_many_npm(names: list[str]) -> list[PackageCheck]:
    """npm paketlərini ardıcıl yoxlayır, registry-ni incitməmək üçün fasilə verir."""
    session = requests.Session()
    session.headers["User-Agent"] = "slopsquatting-detector/0.1"

    results: list[PackageCheck] = []
    for i, name in enumerate(names):
        results.append(check_npm_package(name, session=session))
        if i < len(names) - 1:
            time.sleep(REQUEST_DELAY)
    return results


def _safe_check(func, name: str, session: requests.Session) -> PackageCheck:
    """Thread daxilində xətanı tutmaq üçün wrapper."""
    try:
        return func(name, session=session)
    except Exception as exc:
        return PackageCheck(name=name, exists=False, error=f"thread-error: {exc}")


def check_many_concurrent(
    names: list[str], 
    ecosystem: str, 
    max_workers: int = 10
) -> list[PackageCheck]:
    """Paketləri paralel olaraq yoxlayır (ThreadPoolExecutor ilə).
    
    Qeyd: max_workers=10 seçilib ki, npm/PyPI rate limit-inə düşməyək.
    """
    func = check_pypi_package if ecosystem == "pypi" else check_npm_package
    
    session = requests.Session()
    session.headers["User-Agent"] = "slopsquatting-detector/0.2"

    results_map: dict[str, PackageCheck] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_name = {
            executor.submit(_safe_check, func, name, session): name
            for name in names
        }
        
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            results_map[name] = future.result()

    # Orijinal sıranı qoru (dict insertion order)
    return [results_map[name] for name in names]
