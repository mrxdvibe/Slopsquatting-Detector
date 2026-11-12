# 🛡️ Slopsquatting Detector

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PyPI](https://img.shields.io/badge/PyPI-Supported-success)
![npm](https://img.shields.io/badge/npm-Supported-red)
![License](https://img.shields.io/badge/License-MIT-green)

**Author:** [Mrxdvibe](https://github.com/mrxdvibe) | **Status:** Active Development

**A real-time security scanner that detects AI-hallucinated (slopsquatted) packages in Python and JavaScript ecosystems.**

## 🚨 The Problem: Slopsquatting

As AI coding assistants (ChatGPT, GitHub Copilot, Cursor) become ubiquitous, developers increasingly rely on "Vibe Coding." However, LLMs frequently hallucinate non-existent package names (e.g., `pip install cyber-secure-tool`). 

Attackers exploit this by pre-registering these hallucinated names on public registries (PyPI, npm) and injecting malicious payloads. When a developer installs the suggested package, the system is compromised. This emerging supply chain attack vector is known as **Slopsquatting**.

## 💡 The Solution

`Slopsquatting Detector` analyzes your dependency manifests and queries official registry APIs in real-time to identify:
1. Packages that **do not exist** (404 hallucination).
2. Packages that are **suspiciously new** (created recently by attackers).
3. **Typosquatted** package names using Levenshtein distance (e.g., `reqeusts` instead of `requests`).

## ✨ Key Features

- **Real-time Registry Verification:** Direct integration with official PyPI and npm JSON APIs.
- **Typosquatting Detection:** Zero-dependency Levenshtein distance algorithm to catch AI typos.
- **Transitive Dependency Scanning:** Full support for `package-lock.json` with concurrent (multi-threaded) lookups for speed.
- **CI/CD Ready:** Returns exit code `1` with the `--fail-on-danger` flag to automatically block vulnerable pipelines.
- **Structured Output:** Native `--format json` support for easy integration with SIEMs and custom tooling.
- **Scoped Package Support:** Fully handles npm scoped packages (e.g., `@types/node`).

## 🚀 Installation

Clone the repository and install it as an editable package:
```bash
git clone https://github.com/mrxdvibe/Slopsquatting-Detector.git
cd Slopsquatting-Detector
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```
## 🛠️ Usage

### Python (PyPI)
```bash
slopdetect requirements.txt
```
### JavaScript / Node.js (npm)
```bash
slopdetect package.json
```
### Lockfiles (Concurrent Scanning)
```bash
slopdetect package-lock.json --concurrent
```
### CI/CD Integration (GitHub Actions)
```bash
slopdetect requirements.txt --fail-on-danger
```
### JSON Output
```bash
slopdetect package.json --format json > report.json
```
## 📊 Risk Levels

The scanner categorizes packages into three distinct risk levels:

| Level | Icon | Description |
| :--- | :---: | :--- |
| **CLEAN** | 🟢 | Package exists, has a valid release history, and appears normal. |
| **SUSPICIOUS** | 🟡 | Package is very new (< 30 days) or its name is highly similar to a popular package. |
| **DANGER** | 🔴 | Package does not exist (hallucination) or has zero releases (empty registration). |

## 🏗️ Architecture

The project is built with a modular architecture for easy extension:
- `core/parsers.py`: Manifest parsing (`requirements.txt`, `package.json`).
- `core/lockfile.py`: `package-lock.json` parsing (npm v6 & v7+).
- `core/registry.py`: API communication and concurrent executor.
- `core/typosquat.py`: Levenshtein distance engine and popular package database.
- `core/risk.py`: Threat intelligence and risk assessment logic.
- `ui/render.py`: Rich terminal formatting and JSON output.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/mrxdvibe/Slopsquatting-Detector/issues).

## 📝 License

This project is [MIT](https://choosealicense.com/licenses/mit/) licensed.
