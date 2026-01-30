# Contributing to OpenTrans

## Getting Started

To contribute to this project, you will need to set up your development environment.

### 1. Prerequisites

* **Python 3.10+**
* **Ollama** (Running locally)
* **uv** (for fast dependency management)

### 2. Local Setup

```bash
# Clone the repository
git clone https://github.com/rainstorm108/OpenTrans.git
cd OpenTrans

# Sync dependencies and create a virtual environment
uv sync

# Enter the development environment
hatch shell

```

---

## Development

### Branching Policy

* Create a new branch for every feature or bug fix: `git checkout -b feat/your-feature-name` or `git checkout -b fix/issue-id`.
* Do not commit directly to the `master` or `main` branch.

### Testing

We use **pytest** and **hatch** for testing. Before submitting a Pull Request, please ensure all tests pass:

```bash
hatch test

```

If you are adding a new feature, please include a corresponding test in the `tests/` directory.

### Coding Standards

* **Formatting:** We follow PEP 8.
* **Typing:** Use Python type hints wherever possible.
* **Docstrings:** Use Google-style docstrings for all new functions.
* **Indentation:** Please use **2 spaces** to stay consistent with the existing codebase.

---

## Submitting a Pull Request

1. **Push your changes:** `git push origin feat/your-feature-name`.
2. **Open a PR:** Clearly describe the changes and link to any relevant issues.
3. **Review:** Maintainers will review your code. Be prepared to make small adjustments if requested!

## Reporting Issues

If you find a bug, please open an issue and include:

* Your OS and Python version.
* The Ollama model you were using.
* A small snippet of the Markdown/LaTeX that caused the error.
