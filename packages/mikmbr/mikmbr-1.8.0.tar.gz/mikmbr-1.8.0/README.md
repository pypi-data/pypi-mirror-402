# Mikmbr - Python Security Scanner

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Fast, deterministic security scanner for Python.** Detects 25+ types of vulnerabilities including SQL injection, secrets, SSRF. Framework-specific rules for Django, Flask, FastAPI.

```bash
pip install mikmbr
mikmbr scan .
```

## Why Mikmbr?

- **⚡ Lightning Fast**: Scans 1000+ files per second using Python AST analysis
- **🎯 Framework-Aware**: Specialized rules for Django, Flask, and FastAPI applications
- **🔕 Suppression System**: Mark false positives with inline comments
- **🔗 GitHub Integration**: SARIF output for native Code Scanning support
- **🔒 Privacy First**: Runs entirely offline. Your code never leaves your machine
- **📚 Educational**: Every finding includes CWE/OWASP references and fix suggestions
- **🎛️ Fully Configurable**: YAML-based configuration for custom rules and severity levels
- **🧠 Smart Secret Detection**: Three-layer detection with entropy analysis and pattern matching

## Features

### Core Security Rules (21 rules)

**21 Detection Rules** covering **9/10 OWASP Top 10 2021** categories:

| Rule | Severity | Description | CWE |
|------|----------|-------------|-----|
| Template Injection | CRITICAL | SSTI in Jinja2, Mako, Django | CWE-94 |
| SQL Injection | HIGH | String concatenation, f-strings in queries | CWE-89 |
| Command Injection | HIGH | os.system(), subprocess with shell=True | CWE-78 |
| Hardcoded Secrets | HIGH | Smart detection with entropy + patterns | CWE-798 |
| SSRF | HIGH | Server-Side Request Forgery | CWE-918 |
| Dangerous Exec | HIGH | eval(), exec() usage | CWE-95 |
| Path Traversal | HIGH | Unsafe file path construction | CWE-22 |
| XXE | HIGH | XML External Entity vulnerabilities | CWE-611 |
| Insecure Deserialization | HIGH | pickle, unsafe yaml.load() | CWE-502 |
| Open Redirect | MEDIUM | Unvalidated redirects | CWE-601 |
| Timing Attack | MEDIUM | Non-constant-time comparisons | CWE-208 |
| Log Injection | MEDIUM | Unsanitized user input in logs | CWE-117 |
| Insecure Random | MEDIUM | Using random for security | CWE-338 |
| Weak Crypto | MEDIUM | MD5, SHA1 usage | CWE-327 |
| Regex DoS | MEDIUM | Catastrophic backtracking patterns | CWE-1333 |
| Bare Except | LOW | Catches all exceptions | CWE-396 |
| Debug Code | LOW | Debug mode in production | CWE-489 |

### Framework-Specific Rules (17 additional checks)

**Django (6 rules)**
- `Model.objects.raw()` without parameterization → SQL injection
- `mark_safe()` usage → XSS risk
- `QuerySet.extra()` → SQL injection
- `DEBUG = True` → Information disclosure
- Empty/wildcard `ALLOWED_HOSTS` → Host header attacks
- Hardcoded `SECRET_KEY` → Session compromise

**Flask (6 rules)**
- `send_file()` with user input → Path traversal
- `render_template_string()` → Server-Side Template Injection
- Hardcoded `app.secret_key` → Session compromise
- `app.debug = True` → Information disclosure
- `set_cookie()` without secure flags → Cookie theft
- Wildcard CORS → CSRF attacks

**FastAPI (5 rules)**
- `dict`/`Any` parameters → Input validation bypass
- `FileResponse` with user path → Path traversal
- `HTMLResponse` with user content → XSS
- Wildcard CORS → CSRF attacks
- Missing authentication on endpoints → Unauthorized access

See [FRAMEWORK_RULES.md](FRAMEWORK_RULES.md) for complete documentation.

### New in v1.6

**Inline Suppression**
```python
api_key = "test_key"  # mikmbr: ignore[HARDCODED_SECRET]
```

**SARIF Output for GitHub Code Scanning**
```bash
mikmbr scan . --format sarif > results.sarif
```

See [SUPPRESSION.md](SUPPRESSION.md) and [SARIF_FORMAT.md](SARIF_FORMAT.md) for details.

## Quick Start

### Installation

```bash
pip install mikmbr
```

For development:
```bash
git clone https://github.com/tonybowen-me/Mikmbr.git
cd mikmbr
pip install -e ".[dev]"
```

### Basic Usage

Scan your project:
```bash
mikmbr scan .
```

Scan with detailed output:
```bash
mikmbr scan . --verbose
```

JSON output for CI/CD:
```bash
mikmbr scan . --format json
```

### Configuration

Create a `.mikmbr.yaml` file in your project root to customize scanning behavior:

```yaml
version: "1.4"

# Disable specific rules
rules:
  REGEX_DOS: false

# Configure secret detection
secret_detection:
  entropy:
    min_entropy: 3.0  # More sensitive

# Output settings
output:
  verbose: true
```

mikmbr will automatically discover and use your configuration. See [CONFIGURATION.md](CONFIGURATION.md) for complete details.

### Output Formats

Human-readable output (default):

```bash
mikmbr scan myproject/
```

Verbose output with CWE IDs, OWASP mappings, and code snippets:

```bash
mikmbr scan myproject/ --verbose
```

JSON output:

```bash
mikmbr scan myproject/ --format json
```

Custom configuration file:

```bash
mikmbr scan myproject/ --config my-config.yaml
```

### Example Output

```
Found 3 security issue(s):

[HIGH] src/app.py:12
  Rule: DANGEROUS_EXEC
  CWE: CWE-95
  OWASP: A03:2021 - Injection
  Issue: Use of eval() allows arbitrary code execution
  Fix: Avoid eval(). Use safer alternatives like ast.literal_eval()

[HIGH] src/db.py:45
  Rule: SQL_INJECTION
  CWE: CWE-89
  OWASP: A03:2021 - Injection
  Issue: SQL query built with string concatenation/formatting
  Fix: Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))

[MED] src/utils.py:78
  Rule: WEAK_CRYPTO
  CWE: CWE-327
  OWASP: A02:2021 - Cryptographic Failures
  Issue: Use of weak cryptographic algorithm: MD5
  Fix: Replace MD5 with SHA-256: hashlib.sha256()
```

## Use Cases

### For Developers
Catch vulnerabilities before they reach production. Integrate into your IDE or pre-commit hooks:
```bash
# Pre-commit hook
mikmbr scan . --format json || exit 1
```

### For CI/CD
Automated security scanning in GitHub Actions:
```yaml
- name: Security Scan
  run: |
    pip install mikmbr
    mikmbr scan src/ --format json
```

### For Security Teams
Enforce security standards across your codebase with custom configurations:
```yaml
# .mikmbr.yaml
rules:
  SQL_INJECTION: true
  HARDCODED_SECRET: true
output:
  verbose: true
  fail_on_severity: high
```

### For Learners
Learn secure coding practices. Each finding includes educational content:
- **CWE references**: Industry-standard weakness classifications
- **OWASP mappings**: Map to OWASP Top 10 categories
- **Fix suggestions**: Concrete examples of secure alternatives
- **Code snippets**: See exactly what triggered the detection

## Detection Examples

<details>
<summary><b>SQL Injection</b></summary>

```python
# Vulnerable
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Secure
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```
</details>

<details>
<summary><b>Hardcoded Secrets</b></summary>

```python
# Vulnerable
api_key = "sk_live_1234567890abcdef"

# Secure
api_key = os.getenv("API_KEY")
```
</details>

<details>
<summary><b>Template Injection (SSTI)</b></summary>

```python
# Vulnerable
from flask import render_template_string
render_template_string(user_template)

# Secure
from flask import render_template
render_template('safe_template.html', data=user_data)
```
</details>

<details>
<summary><b>SSRF (Server-Side Request Forgery)</b></summary>

```python
# Vulnerable
import requests
requests.get(user_provided_url)

# Secure
ALLOWED_HOSTS = ['api.example.com']
if urlparse(user_url).hostname in ALLOWED_HOSTS:
    requests.get(user_url)
```
</details>

See [V1.5_NEW_RULES.md](V1.5_NEW_RULES.md) for complete documentation of all detection rules.

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=mikmbr --cov-report=html
```

### Project Structure

```
mikmbr/
├── src/mikmbr/
│   ├── cli.py              # CLI entry point
│   ├── scanner.py          # Main scanner orchestration
│   ├── models.py           # Data models (Finding, Severity)
│   ├── formatters.py       # Output formatters
│   └── rules/              # Detection rules
│       ├── base.py         # Rule interface
│       ├── dangerous_exec.py
│       ├── command_injection.py
│       ├── sql_injection.py
│       ├── weak_crypto.py
│       └── hardcoded_secrets.py
└── tests/
    ├── test_rules.py       # Rule unit tests
    └── test_scanner.py     # Scanner integration tests
```

## How It Works

Mikmbr uses **Abstract Syntax Tree (AST)** analysis to parse Python code into a structured tree, then applies deterministic rules to detect security vulnerabilities:

1. **Parse**: Python's `ast` module converts source code to AST
2. **Analyze**: Each rule walks the AST tree looking for vulnerable patterns
3. **Report**: Findings include exact line numbers, CWE IDs, and remediation steps

**Benefits of AST-based detection:**
- Zero false positives (not based on regex or AI guessing)
- Handles all code formatting variations
- Exact line numbers for every finding
- No execution required - safe static analysis

See [HOW_IT_WORKS.md](HOW_IT_WORKS.md) for detailed technical explanation.

## Documentation

- [Configuration Guide](CONFIGURATION.md) - Complete YAML reference and examples
- [Smart Secrets Detection](SMART_SECRETS.md) - How entropy analysis and pattern matching work
- [Detection Rules v1.5](V1.5_NEW_RULES.md) - Documentation for all 17 rules
- [Changelog](CHANGELOG.md) - Version history and release notes
- [Deployment Guide](DEPLOY_RENDER.md) - Deploy the landing page to Render

## Contributing

Contributions are welcome! Areas for improvement:

- **New Rules**: Add detection for more vulnerability types
- **Language Support**: Extend to JavaScript, TypeScript, Go, etc.
- **IDE Integrations**: VS Code, PyCharm plugins
- **Performance**: Optimize scanning speed for large codebases

Please open an issue to discuss before submitting large PRs.

## Development

Run tests:
```bash
pip install -e ".[dev]"
pytest --cov=mikmbr
```

Project structure:
```
src/mikmbr/
├── cli.py              # CLI entry point
├── scanner.py          # Main orchestration
├── config.py           # Configuration system
├── models.py           # Data models
├── formatters.py       # Output formatters
└── rules/              # Detection rules (17 rules)
```

## Limitations

- **Python only**: No support for other languages yet
- **Static analysis only**: No runtime or dynamic analysis
- **No dataflow tracking**: Limited to single-statement analysis
- **No SBOM**: Doesn't scan dependencies for known CVEs

## Exit Codes

- `0`: No issues found
- `1`: Security issues found
- `2`: Error during scanning

## License

MIT License - see [LICENSE](LICENSE) for details

## Credits

Built by Tony. Contributions welcome on [GitHub](https://github.com/tonybowen-me/Mikmbr).

---

**⭐ If Mikmbr helped secure your code, please star the repo!**