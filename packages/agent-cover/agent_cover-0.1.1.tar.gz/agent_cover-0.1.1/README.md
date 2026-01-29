# 🛡️ Agent Cover

[![PyPI version](https://badge.fury.io/py/agent-cover.svg)](https://badge.fury.io/py/agent-cover)
[![Tests](https://github.com/vittoriomussin/agent-cover/actions/workflows/test.yml/badge.svg)](https://github.com/vittoriomussin/agent-cover/actions/workflows/test.yml)
[![codecov](https://codecov.io/github/vittoriomussin/agent-cover/graph/badge.svg?token=H071SUY80A)](https://codecov.io/github/vittoriomussin/agent-cover)
[![Docs](https://github.com/vittoriomussin/agent-cover/actions/workflows/deploy_docs.yml/badge.svg)](https://github.com/vittoriomussin/agent-cover/actions/workflows/deploy_docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Agent Cover** is an observability and testing framework designed for LLMOps. Unlike traditional tools that measure executed lines of code, Agent Cover measures the **Logical Coverage** of your Agent.

It verifies that your test suite actually exercises the agent's capabilities: its **Prompts**, its **Tools**, and its **Business Decision** branches.

[**📚 Read the Documentation**](https://vittoriomussin.github.io/agent-cover/)

---

## 📉 The Gap in LLM Testing

Traditional tools (like `coverage.py`) measure Python execution. However, in LLM-based applications, "line coverage" creates a false sense of security.

> **The Scenario:** Your agent has a tool `refund_user` and a prompt instruction to "Ask for confirmation".
>
> **The Problem:** Your test runs the code, but the LLM *decides* to skip the tool or ignore the prompt. Standard coverage says **100%**. Agent Cover says **0% Tool Coverage**.

## 🚀 How It Works

Agent Cover operates on a hybrid "Static + Runtime" model:

1.  **🔍 Inventory Scan (Static):** Before tests run, it scans your codebase to build a map of "Logical Assets":
    * **Prompts:** LangChain objects, Jinja2 templates, and raw global strings.
    * **Tools:** Functions decorated with `@tool` or inheriting from `BaseTool`.
    * **Decisions:** Automatically derives coverage rules from your **Pydantic** models (Enums, Literals, Booleans).

2.  **⚡ Instrumentation (Runtime):** It hooks into the execution lifecycle (LangChain, LlamaIndex, OpenAI, PromptFlow) to verify if those assets were actually used by the LLM.

---

## 📦 Installation

```bash
pip install agent-cover

```

For development and testing support:

```bash
pip install "agent-cover[dev]"

```

---

## ⚡ Quick Start

### 1. Configuration (Optional but Recommended)

Create an `agent-cover.yaml` to define your Business Logic requirements.

```yaml
# agent-cover.yaml
decisions:
  - id: intent_classification
    description: "Ensure the agent triggers all support paths"
    target_field: intent
    expected_values: ["REFUND", "TECH_SUPPORT", "SALES"]

```

### 2. Run with Pytest

Simply add the `--agent-cov` flag to your existing test run.

```bash
pytest --agent-cov --agent-cov-html=coverage_report

```

### 3. View the Report

Open `coverage_report/index.html`. You will see:

* **Prompt Coverage:** Which templates were formatted and sent to the LLM.
* **Tool Coverage:** Which tools the LLM actually decided to call.
* **Decision Coverage:** Which logical branches (e.g., `REFUND` vs `SALES`) were observed in the output.

---

## 🔌 Supported Frameworks

Agent Cover dynamically patches these libraries to intercept logical events.

| Framework | Status | Features Tracked |
| --- | --- | --- |
| **LangChain** | ✅ | Chains, Agents, Tools, Callbacks, Pydantic Parsers |
| **LlamaIndex** | ✅ | AgentRunner, FunctionTools, Prompts |
| **OpenAI SDK** | ✅ | ChatCompletions, Function Calling (Raw Strings) |
| **PromptFlow** | ✅ | Flow Nodes, Jinja Templates, Python Tools |
| **Pydantic** | ✅ | Auto-generation of decision rules from Models |

---

## 🛠 Advanced Usage: Microsoft PromptFlow

PromptFlow executes nodes in separate worker processes, which breaks standard coverage tools. Agent Cover includes a dedicated CLI wrapper to handle multi-process aggregation.

Instead of running `pf run`, wrap your command:

```bash
# Injects instrumentation into all child worker processes
agent-cover run --source-dir ./src -- pf run create --flow ./my_flow --data data.jsonl

```

This will automatically aggregate coverage data from all parallel workers into a single report.

---

## 🤝 Contributing

Contributions are welcome! Please ensure all pull requests pass the CI quality gates.

1. Clone the repository.
2. Install development dependencies: `pip install -e ".[dev]"`
3. Install pre-commit hooks: `pre-commit install`
4. Run the test suite: `pytest`

## 📄 License

This project is licensed under the MIT License.
