"""Rich ilə rəngli terminal çıxışı + JSON render."""
from __future__ import annotations

import json
from datetime import datetime

from rich.console import Console
from rich.table import Table

from core.risk import Risk, Verdict


_RISK_STYLE = {
    Risk.DANGER: "bold red",
    Risk.SUSPICIOUS: "bold yellow",
    Risk.CLEAN: "bold green",
}

_RISK_LABEL = {
    Risk.DANGER: "TƏHLÜKƏ",
    Risk.SUSPICIOUS: "ŞÜBHƏLİ",
    Risk.CLEAN: "TƏMİZ",
}


def render(verdicts: list[Verdict]) -> None:
    console = Console()
    table = Table(title="Slopsquatting Detector — Nəticələr", show_lines=True)

    table.add_column("Paket", style="cyan", no_wrap=True)
    table.add_column("Risk", justify="center")
    table.add_column("Versiya", justify="center")
    table.add_column("Yaş (gün)", justify="right")
    table.add_column("Təklif olunan ad", style="magenta")
    table.add_column("Səbəb")

    for v in verdicts:
        style = _RISK_STYLE[v.risk]
        label = _RISK_LABEL[v.risk]
        age = v.check.age_days
        table.add_row(
            v.check.name,
            f"[{style}]{label}[/{style}]",
            v.check.latest_version or "—",
            str(age) if age is not None else "—",
            v.suggested_name or "—",
            v.reason,
        )

    console.print(table)

    dangers = sum(1 for v in verdicts if v.risk is Risk.DANGER)
    suspicious = sum(1 for v in verdicts if v.risk is Risk.SUSPICIOUS)
    if dangers:
        console.print(f"\n[bold red]⚠ {dangers} paket TƏHLÜKƏLİDİR.[/bold red]")
    if suspicious:
        console.print(f"[bold yellow]⚠ {suspicious} paket ŞÜBHƏLİDİR.[/bold yellow]")


def render_json(verdicts: list[Verdict]) -> None:
    """CI / digər alətlərlə inteqrasiya üçün strukturlu JSON çıxışı."""
    payload = {
        "tool": "slopsquatting-detector",
        "version": "0.2",
        "generated_at": datetime.now().astimezone().isoformat(),
        "summary": {
            "total": len(verdicts),
            "danger": sum(1 for v in verdicts if v.risk is Risk.DANGER),
            "suspicious": sum(1 for v in verdicts if v.risk is Risk.SUSPICIOUS),
            "clean": sum(1 for v in verdicts if v.risk is Risk.CLEAN),
        },
        "packages": [
            {
                "name": v.check.name,
                "risk": v.risk.value,
                "reason": v.reason,
                "suggested_name": v.suggested_name,
                "exists": v.check.exists,
                "latest_version": v.check.latest_version,
                "age_days": v.check.age_days,
                "release_count": v.check.release_count,
                "error": v.check.error,
            }
            for v in verdicts
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
