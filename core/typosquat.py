"""Typosquatting / yaxın-ad aşkarlanması (Levenshtein məsafəsi).

Məntiq: AI tez-tez real paketlərə 1-2 hərf yaxın adlar uydurur
(məsələn: 'reqeusts' -> 'requests'). Bu modul paket adını
populyar paketlər bazası ilə müqayisə edir və yaxın uyğunluq
tapdıqda risk siqnalı qaytarır.
"""
from __future__ import annotations


# Populyar paketlər bazası (PyPI + npm qarışıq, əl ilə seçilmiş).
# Siyahını sonradan genişləndirmək asandır.
POPULAR_PACKAGES: frozenset[str] = frozenset({
    # --- PyPI ---
    "requests", "urllib3", "numpy", "pandas", "scipy", "matplotlib",
    "django", "flask", "fastapi", "pydantic", "sqlalchemy", "celery",
    "pytest", "black", "ruff", "mypy", "poetry", "setuptools", "wheel",
    "pip", "boto3", "botocore", "click", "jinja2", "pyyaml", "toml",
    "aiohttp", "httpx", "websockets", "cryptography", "pycryptodome",
    "paramiko", "scapy", "pyopenssl", "beautifulsoup4", "lxml",
    "pillow", "opencv-python", "scikit-learn", "tensorflow", "torch",
    "transformers", "openai", "anthropic", "langchain", "rich",
    "typer", "loguru", "structlog", "redis", "pymongo", "psycopg2",
    "asyncpg", "alembic", "gunicorn", "uvicorn", "starlette",
    # --- npm ---
    "express", "lodash", "react", "react-dom", "vue", "angular",
    "axios", "webpack", "babel-core", "typescript", "eslint", "prettier",
    "jest", "mocha", "chai", "next", "nuxt", "svelte", "vite",
    "tailwindcss", "socket.io", "mongoose", "sequelize", "knex",
    "dotenv", "cors", "helmet", "jsonwebtoken", "bcrypt", "passport",
    "commander", "yargs", "chalk", "debug", "uuid", "moment", "dayjs",
    "rxjs", "redux", "mobx", "zustand", "formik", "yup", "zod",
    "cheerio", "puppeteer", "playwright", "cypress",
})


def levenshtein(a: str, b: str, max_distance: int = 3) -> int:
    """Levenshtein məsafəsi (optimallaşdırılmış, 2 sətir yaddaş).

    max_distance-dən böyük məsafələrdə erkən çıxış edir — bu,
    böyük siyahılarda sürəti xeyli artırır.
    """
    if a == b:
        return 0
    if abs(len(a) - len(b)) > max_distance:
        return max_distance + 1

    if len(a) < len(b):
        a, b = b, a

    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        row_min = i
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            value = min(
                previous[j] + 1,       # silmə
                current[j - 1] + 1,    # əlavə etmə
                previous[j - 1] + cost # əvəz etmə
            )
            current.append(value)
            if value < row_min:
                row_min = value
        if row_min > max_distance:
            return max_distance + 1
        previous = current

    return previous[-1]


def find_close_match(name: str, max_distance: int = 2) -> str | None:
    """Paket adına populyar bazadan ən yaxın uyğunluğu tapır.

    Qaytarır: yaxın paket adı (məsafə <= max_distance) və ya None.
    Özü ilə eyni adı uyğunluq saymır.
    """
    normalized = name.lower().replace("_", "-").replace(".", "-")

    best_match: str | None = None
    best_distance = max_distance + 1

    for candidate in POPULAR_PACKAGES:
        if candidate == normalized:
            return None  # real populyar paketin özüdür, problem yoxdur

        distance = levenshtein(normalized, candidate, max_distance=max_distance)
        if distance < best_distance:
            best_distance = distance
            best_match = candidate

    if best_match is not None and best_distance <= max_distance:
        return best_match
    return None
