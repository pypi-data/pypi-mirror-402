[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

# Python: Garmin Connect

> **Note:** This is a fork of [python-garminconnect](https://github.com/cyberjunky/python-garminconnect) that uses [uv](https://docs.astral.sh/uv/) instead of PDM for dependency management. This change was made due to uv's growing adoption in the Python ecosystem, its significantly faster performance, and its unified approach to Python project management.

The Garmin Connect API library comes with two examples:

- **`example.py`** - Simple getting-started example showing authentication, token storage, and basic API calls
- **`demo.py`** - Comprehensive demo providing access to **105+ API methods** organized into **12 categories** for easy navigation

Note: The demo menu is generated dynamically; exact options may change between releases.

```bash
$ ./demo.py
🏃‍♂️ Full-blown Garmin Connect API Demo - Main Menu
==================================================
Select a category:

  [1] 👤 User & Profile
  [2] 📊 Daily Health & Activity
  [3] 🔬 Advanced Health Metrics
  [4] 📈 Historical Data & Trends
  [5] 🏃 Activities & Workouts
  [6] ⚖️ Body Composition & Weight
  [7] 🏆 Goals & Achievements
  [8] ⌚ Device & Technical
  [9] 🎽 Gear & Equipment
  [0] 💧 Hydration & Wellness
  [a] 🔧 System & Export
  [b] 📅 Training plans

  [q] Exit program

Make your selection:
```

## API Coverage Statistics

- **Total API Methods**: 105+ unique endpoints (snapshot)
- **Categories**: 12 organized sections
- **User & Profile**: 4 methods (basic user info, settings)
- **Daily Health & Activity**: 9 methods (today's health data)
- **Advanced Health Metrics**: 11 methods (fitness metrics, HRV, VO2, training readiness)
- **Historical Data & Trends**: 9 methods (date range queries, weekly aggregates)
- **Activities & Workouts**: 28 methods (comprehensive activity and workout management)
- **Body Composition & Weight**: 8 methods (weight tracking, body composition)
- **Goals & Achievements**: 15 methods (challenges, badges, goals)
- **Device & Technical**: 7 methods (device info, settings)
- **Gear & Equipment**: 8 methods (gear management, tracking)
- **Hydration & Wellness**: 9 methods (hydration, blood pressure, menstrual)
- **System & Export**: 4 methods (reporting, logout, GraphQL)
- **Training Plans**: 3 methods

### Interactive Features

- **Enhanced User Experience**: Categorized navigation with emoji indicators
- **Smart Data Management**: Interactive weigh-in deletion with search capabilities
- **Comprehensive Coverage**: All major Garmin Connect features are accessible
- **Error Handling**: Robust error handling with user-friendly prompts
- **Data Export**: JSON export functionality for all data types

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

A comprehensive Python3 API wrapper for Garmin Connect, providing access to health, fitness, and device data.

## 📖 About

This library enables developers to programmatically access Garmin Connect data including:

- **Health Metrics**: Heart rate, sleep, stress, body composition, SpO2, HRV
- **Activity Data**: Workouts, scheduled workouts, exercises, training status, performance metrics
- **Device Information**: Connected devices, settings, alarms, solar data
- **Goals & Achievements**: Personal records, badges, challenges, race predictions
- **Historical Data**: Trends, progress tracking, date range queries

Compatible with all Garmin Connect accounts. See <https://connect.garmin.com/>

## 📦 Installation

Install from PyPI:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install garminconnect
```

## Run demo software (recommended)

```bash
# Install uv if you haven't already
# See: https://docs.astral.sh/uv/getting-started/installation/

# Install dependencies and run examples
uv sync --group example

# Run the simple example
uv run python example.py

# Run the comprehensive demo
uv run python demo.py
```


## 🛠️ Development

Set up a development environment for contributing:

> **Note**: This project uses [uv](https://docs.astral.sh/uv/) for fast, modern Python dependency management. uv automatically manages virtual environments and provides a unified experience for Python project management.

**Environment Setup:**

```bash
# 1. Install uv (if not already installed)
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or via Homebrew: brew install uv

# 2. Install all development dependencies (creates .venv automatically)
uv sync --all-groups

# 3. Setup pre-commit hooks (optional)
uv run pre-commit install --install-hooks
```

**Available Development Commands:**
```bash
# Formatting
uv run ruff check . --fix --unsafe-fixes  # Auto-fix linting issues
uv run isort . --skip-gitignore           # Sort imports
uv run black -l 88 .                      # Format code

# Linting
uv run isort --check-only . --skip-gitignore  # Check import order
uv run ruff check .                           # Check linting
uv run black -l 88 . --check --diff           # Check formatting
uv run mypy garminconnect tests               # Type checking

# Testing
uv run coverage run -m pytest -v --durations=10  # Run tests with coverage
uv run coverage html                             # Generate HTML report
uv run coverage xml -o coverage/coverage.xml     # Generate XML report

# Building
uv build                                   # Build package for distribution
uv publish                                 # Publish to PyPI
```

**Code Quality Workflow:**
```bash
# Before making changes
uv run ruff check .           # Check current code quality

# After making changes
uv run ruff check . --fix     # Auto-fix issues
uv run black -l 88 .          # Format code
uv run mypy garminconnect     # Type check
uv run pytest -v              # Run tests
```

Run these commands before submitting PRs to ensure code quality standards.

## 🔐 Authentication

The library uses the same OAuth authentication as the official Garmin Connect app via [Garth](https://github.com/matin/garth).

**Key Features:**
- Login credentials valid for one year (no repeated logins)
- Secure OAuth token storage
- Same authentication flow as official app

**Advanced Configuration:**
```python
# Optional: Custom OAuth consumer (before login)
import os
import garth
garth.sso.OAUTH_CONSUMER = {
    'key': os.getenv('GARTH_OAUTH_KEY', '<YOUR_KEY>'),
    'secret': os.getenv('GARTH_OAUTH_SECRET', '<YOUR_SECRET>'),
}
# Note: Set these env vars securely; placeholders are non-sensitive.
```

**Token Storage:**
Tokens are automatically saved to `~/.garminconnect` directory for persistent authentication.
For security, ensure restrictive permissions:

```bash
chmod 700 ~/.garminconnect
chmod 600 ~/.garminconnect/* 2>/dev/null || true
```

## 🧪 Testing

Run the test suite to verify functionality:

**Prerequisites:**

Create tokens in ~/.garminconnect by running the example program.

```bash
# Install development dependencies
uv sync --all-groups
```

**Run Tests:**

```bash
uv run pytest -v                                     # Run all tests
uv run coverage run -m pytest -v --durations=10     # Run with coverage
uv run coverage html                                 # Generate HTML report
```

Optional: keep test tokens isolated

```bash
export GARMINTOKENS="$(mktemp -d)"
uv run python example.py  # create fresh tokens for tests
uv run pytest -v
```

**Note:** Tests automatically use `~/.garminconnect` as the default token file location. You can override this by setting the `GARMINTOKENS` environment variable. Run `example.py` first to generate authentication tokens for testing.

**For Developers:** Tests use VCR cassettes to record/replay HTTP interactions. If tests fail with authentication errors, ensure valid tokens exist in `~/.garminconnect`

## 📦 Publishing

For package maintainers:

**Setup PyPI credentials:**

```bash
# Option 1: Use environment variables (recommended)
export UV_PUBLISH_USERNAME="__token__"
export UV_PUBLISH_PASSWORD="<PyPI_API_TOKEN>"

# Option 2: Use ~/.pypirc file
cat > ~/.pypirc <<'EOF'
[pypi]
username = __token__
password = <PyPI_API_TOKEN>
EOF
chmod 600 ~/.pypirc
```

**Publish new version:**

```bash
uv build           # Build package
uv publish         # Publish to PyPI
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

- **Report Issues**: Bug reports and feature requests via GitHub issues
- **Submit PRs**: Code improvements, new features, documentation updates
- **Testing**: Help test new features and report compatibility issues
- **Documentation**: Improve examples, add use cases, fix typos

**Before Contributing:**
1. Set up development environment (`uv sync --all-groups`)
2. Execute code quality checks (`uv run ruff check . --fix && uv run black -l 88 .`)
3. Test your changes (`uv run pytest -v`)
4. Follow existing code style and patterns

**Development Workflow:**
```bash
# 1. Setup environment
uv sync --all-groups

# 2. Make your changes
# ... edit code ...

# 3. Quality checks
uv run ruff check . --fix   # Auto-fix linting issues
uv run black -l 88 .        # Format code
uv run mypy garminconnect   # Type check
uv run pytest -v            # Run tests

# 4. Submit PR
git commit -m "Your changes"
git push origin your-branch
```

### Jupyter Notebook

Explore the API interactively with our [reference notebook](https://github.com/cyberjunky/python-garminconnect/blob/master/reference.ipynb).

### Python Code Examples

```python
from garminconnect import Garmin
import os

# Initialize and login
client = Garmin(
    os.getenv("GARMIN_EMAIL", "<YOUR_EMAIL>"),
    os.getenv("GARMIN_PASSWORD", "<YOUR_PASSWORD>")
)
client.login()

# Get today's stats
from datetime import date
_today = date.today().strftime('%Y-%m-%d')
stats = client.get_stats(_today)

# Get heart rate data
hr_data = client.get_heart_rates(_today)
print(f"Resting HR: {hr_data.get('restingHeartRate', 'n/a')}")
```

### Additional Resources
- **Simple Example**: [example.py](https://raw.githubusercontent.com/cyberjunky/python-garminconnect/master/example.py) - Getting started guide
- **Comprehensive Demo**: [demo.py](https://raw.githubusercontent.com/cyberjunky/python-garminconnect/master/demo.py) - All 105+ API methods
- **API Documentation**: Comprehensive method documentation in source code
- **Test Cases**: Real-world usage examples in `tests/` directory

## 🙏 Acknowledgments

Special thanks to all contributors who have helped improve this project:

- **Community Contributors**: Bug reports, feature requests, and code improvements
- **Issue Reporters**: Helping identify and resolve compatibility issues
- **Feature Developers**: Adding new API endpoints and functionality
- **Documentation Authors**: Improving examples and user guides

This project thrives thanks to community involvement and feedback.

## 💖 Support This Project

If you find this library useful for your projects, please consider supporting its continued development and maintenance:

### 🌟 Ways to Support

- **⭐ Star this repository** - Help others discover the project
- **💰 Financial Support** - Contribute to development and hosting costs
- **🐛 Report Issues** - Help improve stability and compatibility
- **📖 Spread the Word** - Share with other developers

### 💳 Financial Support Options

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

**Why Support?**
- Keeps the project actively maintained
- Enables faster bug fixes and new features
- Supports infrastructure costs (testing, AI, CI/CD)
- Shows appreciation for hundreds of hours of development

Every contribution, no matter the size, makes a difference and is greatly appreciated! 🙏

[releases-shield]: https://img.shields.io/github/release/cyberjunky/python-garminconnect.svg?style=for-the-badge
[releases]: https://github.com/cyberjunky/python-garminconnect/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/cyberjunky/python-garminconnect.svg?style=for-the-badge
[commits]: https://github.com/cyberjunky/python-garminconnect/commits/main
[license-shield]: https://img.shields.io/github/license/cyberjunky/python-garminconnect.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-cyberjunky-blue.svg?style=for-the-badge
