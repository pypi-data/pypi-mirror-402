# envhealth

[![PyPI version](https://badge.fury.io/py/envhealth.svg)](https://pypi.org/project/envhealth/)
[![Downloads](https://pepy.tech/badge/envhealth)](https://pypi.org/project/envhealth/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)


EnvHealth is a powerful Python utility to check **system environment health**.

## Features
- Operating System details
- CPU usage and core stats
- RAM usage
- Disk usage
- CUDA GPU availability + performance benchmark
- Internet connection diagnostics
- Proxy configuration detection
- Package version drift detection (major / minor / patch)
- Deprecated & insecure package flags
- CI-friendly exit codes

Supports multiple report formats:

- Pretty terminal output (Default)
- JSON
- HTML
- PDF


---

## Installation
You can install envhealth via pip:
```python
pip install envhealth
```
After installation, the CLI command will be available as:
```bash
envhealth
```
# Usage
## CLI Usage
- Run the environment checker in the console:
    ```bash
        envhealth
    ```
- Generate HTML, JSON, or Markdown reports:
    ```bash
        envhealth --html
        envhealth --json
        envhealth --pdf
    ```

- Save reports to a custom path:
    ```bash
    envhealth --json --path /custom/output/dir
    envhealth --html --path C:\reports
    envhealth --pdf --path ./reports
    ```

- CI / automation usage:
    ```bash
    envhealth --fail-on minor
    envhealth --fail-on major
    ```
    - Exit codes:
        * 0 → No failure
        * 1 → Minor version drift
        * 2 → Major version drift

## CLI Flags Reference
| Flag              | Description                                |
| ----------------- | ------------------------------------------ |
| `--json`          | Save report as JSON                        |
| `--html`          | Save report as HTML                        |
| `--pdf`           | Save report as PDF                         |
| `--path`          | Custom directory to save reports           |
| `--fail-on minor` | Exit with code `1` if minor drift detected |
| `--fail-on major` | Exit with code `2` if major drift detected |
| `--help`          | Show all CLI options                       |

## Default Save Location

If ```bash --json```, ```bash --html```, or ```bash --pdf``` is used without ```bash --path```, the report is saved to:
* Windows → Desktop
* macOS → Desktop
* Linux → Desktop (fallback: home directory)
Each run prints the exact saved file path.

## Programatic Usage
- Use ``envhealth`` in your Python scripts:
    ```python
    from envhealth import Checker, Reporter

    checker = Checker()
    data = checker.full_report()

    reporter = Reporter(data)

    print(reporter.pretty_text())

    # Save reports
    reporter.save_json()
    reporter.save_html()
    reporter.save_pdf()

    ```
You may also pass a custom path:
```python
    from pathlib import Path

    reporter.save_json(Path("./reports"))

```
# Sample Output
## Console Output
```yaml
    === SYSTEM ===
    os: Windows
    architecture: AMD64
    python_version: 3.11.2

    === CPU ===
    cores: 8
    usage_percent: 12.3

    === MEMORY ===
    total_gb: 16.0
    used_percent: 41.8

    === DISK ===
    total_gb: 512.0
    used_percent: 60.2

    === INTERNET ===
    connected: true

    === PROXY ===
    http_proxy: false
    https_proxy: false

    === CUDA ===
    cuda_available: true
    gpu_name: NVIDIA RTX 3060
    benchmark_time_sec: 0.0124

    === VERSION_DRIFT ===
    - package: requests
    installed: 2.31.0
    latest: 2.32.3
    drift_level: minor

    - package: numpy
    installed: 1.24.2
    latest: 2.0.0
    drift_level: major

    === SECURITY ===
    deprecated:
    - optparse (Deprecated, use argparse)

    insecure:
    - pyyaml 5.3 (Known RCE vulnerability)

```
## JSON Output
Saved as ```bash envhealth_report.json```
```json
    {
    "system": {
        "os": "Windows",
        "architecture": "AMD64",
        "python_version": "3.11.2"
    },
    "cpu": {
        "cores": 8,
        "usage_percent": 12.3
    },
    "memory": {
        "total_gb": 16.0,
        "used_percent": 41.8
    },
    "disk": {
        "total_gb": 512.0,
        "used_percent": 60.2
    },
    "internet": {
        "connected": true,
        "status_code": 200
    },
    "proxy": {
        "http_proxy": false,
        "https_proxy": false
    },
    "cuda": {
        "cuda_available": true,
        "gpu_name": "NVIDIA RTX 3060",
        "benchmark_time_sec": 0.0124
    },
    "version_drift": [
        {
        "package": "requests",
        "installed": "2.31.0",
        "latest": "2.32.3",
        "drift_level": "minor"
        },
        {
        "package": "numpy",
        "installed": "1.24.2",
        "latest": "2.0.0",
        "drift_level": "major"
        }
    ],
    "security": {
        "deprecated": [
        {
            "package": "optparse",
            "reason": "Deprecated, use argparse"
        }
        ],
        "insecure": [
        {
            "package": "pyyaml",
            "installed": "5.3",
            "reason": "Known RCE vulnerability"
        }
        ]
    }
    }

```
## HTML Output
Saved as ```bash envhealth_report.html```
Contains the same data as console output, rendered in HTML.
```html
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>EnvHealth Report</title>
    <style>
        body {
        font-family: monospace;
        background: #ffffff;
        padding: 20px;
        }
        h2 {
        border-bottom: 1px solid #ccc;
        padding-bottom: 4px;
        }
        pre {
        background: #f7f7f7;
        padding: 12px;
        }
    </style>
    </head>
    <body>

    <h1>Environment Health Report</h1>

    <pre>
    === SYSTEM ===
    os: Windows
    architecture: AMD64
    python_version: 3.11.2

    === CPU ===
    cores: 8
    usage_percent: 12.3

    === MEMORY ===
    total_gb: 16.0
    used_percent: 41.8

    === DISK ===
    total_gb: 512.0
    used_percent: 60.2

    === INTERNET ===
    connected: true

    === PROXY ===
    http_proxy: false
    https_proxy: false

    === CUDA ===
    cuda_available: true
    gpu_name: NVIDIA RTX 3060
    benchmark_time_sec: 0.0124

    === VERSION_DRIFT ===
    - package: requests
    installed: 2.31.0
    latest: 2.32.3
    drift_level: minor

    - package: numpy
    installed: 1.24.2
    latest: 2.0.0
    drift_level: major

    === SECURITY ===
    deprecated:
    - optparse (Deprecated, use argparse)

    insecure:
    - pyyaml 5.3 (Known RCE vulnerability)
    </pre>

    </body>
    </html>

```

## PDF Output
Saved as ```bash envhealth_report.pdf```
Generated using reportlab, suitable for audits and sharing.

## CI Failure – JSON Example

When ```bash envhealth``` is used in CI mode with ```bash --fail-on```, it still produces a valid JSON report, but the process exits with a non-zero code.
Command:
```bash
    envhealth --json --fail-on major
```
| Condition   | Exit Code |
| ----------- | --------- |
| No drift    | `0`       |
| Minor drift | `1`       |
| Major drift | `2`       |

This allows GitHub Actions, GitLab CI, Jenkins, etc. to fail the pipeline.

## --help Command

EnvHealth provides a built-in help command using Python’s standard CLI interface.

To view all available commands and options:
```bash 
    envhealth --help
```
The help output includes:
* A short description of the tool
* All supported CLI flags
* Accepted values for each flag
* Usage examples

Example
```bash
    usage: envhealth [-h] [--json] [--html] [--pdf] [--path PATH]
                 [--fail-on {minor,major}]

    Environment Health Checker

    options:
    -h, --help            show this help message and exit
    --json                Save report as JSON
    --html                Save report as HTML
    --pdf                 Save report as PDF
    --path PATH           Directory to save generated reports
    --fail-on {minor,major}
                            Fail CI if version drift reaches this level

```
> [!NOTE]
> * --help is available on all platforms (Windows, Linux, macOS)
> * It is automatically provided and always up-to-date with the CLI
> * Recommended for first-time users and CI configuration

# Support
Supported Platforms: 
* Windows
* Linux
* macOS

## License
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Support
If you find this useful, please star the repository.
