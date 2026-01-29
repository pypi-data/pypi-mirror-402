# PrivScan 🔐

**Local-First Deterministic Security & Privacy Scanner (CLI)**

PrivScan is a **local-first, deterministic, rule-based security and privacy auditing CLI tool** that scans source code and configuration files to detect **secrets, credentials, and PII (Personally Identifiable Information)** using transparent YAML-driven rules.


**Built for developers, security engineers, and CI/CD pipelines.**


## ✨ Features

* 🔒 Secrets Detection
    - API keys (Stripe, GitHub, AWS, generic)
    - Passwords & tokens

* 🧾 PII Detection (India + Global)
    - Aadhaar, PAN, Driving License
    - Email addresses
    - Phone numbers (India & international)
    - Credit cards, passports, US SSN

* 📍 Exact Location Reporting
    - File path
    - Line number
    - Matched value

* 📊 Multiple Output Formats
    - Rich CLI table (default)
    - Summary
    - JSON (machine-readable)

* 🚫 Noise Control
    - Ignores virtualenvs, site-packages, build outputs

* ⚙️ Severity Filtering

* 🚦 CI/CD-Ready Exit Codes

* 📦 pip-installable CLI


### 📦 Installation (PyPI)

***From pypi***
```bash
pip install privscan
```

***Local / Development install:**
```bash
git clone https://github.com/KNIHAL/PrivScan.git
pip install -e .
```

***Verify installation:***
```bash
privscan --help
```


### 🚀 Usage

**Basic Scan**
```bash
privscan .
```

**Scan Specific Directory**
```bash
privscan src/
```

**Minimum Severity Filter**
```bash
privscan . --severity high
```

**Summary Output**
```bash
privscan . --format summary
```

**JSON Output (Automation / CI)**
```bash
privscan . --format json --output report.json
```


### 🤖 CI / Automation Mode

**Fail pipeline if findings are detected:**

```bash
privscan . --severity high --fail-on-findings
```

***Exit codes:***
- 0 → No findings
- 1 → Findings detected

***Compatible with:***
- GitHub Actions
- GitLab CI
- Jenkins
- Pre-commit hooks


### 📊 Example Output (CLI Table)

```ardunio
PrivScan Findings
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Severity ┃ Rule ID           ┃ File                               ┃ Line ┃ Match                               ┃ Description                    ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ HIGH     │ SECRET_STRIPE_KEY │ examples/sample_repo/app.py        │    1 │ sk_test_1234567890abcdef            │ Stripe secret API key detected │
│ HIGH     │ SECRET_API_KEY    │ examples/sample_repo/app.py        │    1 │ API_KEY="sk_test_1234567890abcdef"  │ Hardcoded API key detected     │
│ HIGH     │ SECRET_PASSWORD   │ examples/sample_repo/config.env    │    1 │ DB_PASSWORD="supersecret123"        │ Hardcoded password detected    │
└──────────┴───────────────────┴────────────────────────────────────┴──────┴─────────────────────────────────────┴────────────────────────────────┘
```

### 🧪 Example Repository

**PrivScan includes an example repository for demonstration:**
```bash
privscan examples/sample_repo
```

This validates:
- real-world secret detection
- accurate line numbers
- low false positives


### 🧠 How It Works
```yaml
Directory Scanner
        ↓
Safe File Reader
        ↓
YAML Rule Engine
        ↓
Secret / PII Detectors
        ↓
Location Enrichment
        ↓
Reporters (Table / Summary / JSON)
        ↓
Exit Codes
```

- Deterministic
- Explainable
- Fully offline

### 📁 Project Structure
```yaml
privscan/
├── privscan/
│   ├── cli/
│   ├── scanner/
│   ├── rules/
│   ├── detectors/
│   ├── engine/
│   └── reporter/
├── examples/
│   └── sample_repo/
├── tests/
├── pyproject.toml
└── README.md
```

### 🔐 Rule Design Philosophy

- Prefix-based secrets (low false positives)
- Assignment-only detection
- Length & boundary checks
- Country-aware + global PII
- No entropy guessing
- No ML black boxes

### 📌 Project Status

Status: Stable / Complete (v1)

PrivScan is a finished, production-ready CLI tool.

Future additions (optional):
    - more rule packs
    - organization-specific policies

## 📜 License

MIT License

## 👤 Author

**Kumar Nihal**
Built as a demonstration of applied security engineering, deterministic rule engines, and professional CLI design.