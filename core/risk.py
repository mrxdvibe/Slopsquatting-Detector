"""Yoxlama nəticəsini risk səviyyəsinə çevirir."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .registry import PackageCheck
from .typosquat import find_close_match


class Risk(Enum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    DANGER = "danger"


@dataclass
class Verdict:
    check: PackageCheck
    risk: Risk
    reason: str
    suggested_name: str | None = None  # typosquatting zamanı düzgün ad


NEW_PACKAGE_DAYS = 30


def assess(check: PackageCheck) -> Verdict:
    if check.error:
        return Verdict(check, Risk.SUSPICIOUS, f"yoxlana bilmədi: {check.error}")

    if not check.exists:
        # Mövcud deyilsə, bəlkə real paketin yazılış səhvidir?
        close = find_close_match(check.name)
        if close:
            return Verdict(
                check,
                Risk.DANGER,
                f"PyPI/registry-də YOXDUR, amma '{close}' paketinə çox yaxındır "
                f"(typosquatting / AI hallucinasiyası)",
                suggested_name=close,
            )
        return Verdict(
            check,
            Risk.DANGER,
            "registry-də YOXDUR — AI uydurması / slopsquatting riski",
        )

    if check.release_count == 0:
        return Verdict(
            check,
            Risk.DANGER,
            "qeydiyyat var, amma HEÇ BİR buraxılış yoxdur",
        )

    age = check.age_days
    if age is not None and age < NEW_PACKAGE_DAYS:
        return Verdict(
            check,
            Risk.SUSPICIOUS,
            f"çox yeni paket: son buraxılış {age} gün əvvəl",
        )

    # Mövcud paket, amma populyar paketə çox yaxın ad?
    close = find_close_match(check.name)
    if close:
        return Verdict(
            check,
            Risk.SUSPICIOUS,
            f"adı populyar '{close}' paketinə çox yaxındır",
            suggested_name=close,
        )

    return Verdict(check, Risk.CLEAN, "normal görünür")
