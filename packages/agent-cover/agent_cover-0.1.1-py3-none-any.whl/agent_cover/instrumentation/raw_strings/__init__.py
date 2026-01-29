"""# Raw String Heuristics.

This module scans your codebase for simple string variables acting as prompts (e.g., f-strings).

## 🔗 Architectural Relationships

Since raw strings are not objects, they cannot be patched directly. This module acts as a **Pattern Generator**.

* **Feeds:** [AgentRegistry][agent_cover.registry.AgentRegistry] (Registers the "Definition" with a generated Regex).
* **Enables:** [CoverageCallbackHandler][agent_cover.instrumentation.callbacks.CoverageCallbackHandler] (The handler uses the regexes generated here to match runtime text).
* **Configured by:** CLI flags (`--prompt-prefixes`, `--prompt-suffixes`).

## ⚠️ Limitations

**Global Scope Only:**
Currently, this scanner uses runtime introspection (`vars(module)`). Therefore, it **only detects global module-level constants**.
Variables defined inside functions (local scope) are invisible to the scanner and will not be tracked.

## ⚙️ How it works

1.  **Static Scan:** It iterates through loaded modules looking for variables like `PROMPT_SALES`.
2.  **Regex Generation:** It converts the string content into a robust regex (handling whitespace and f-string placeholders like `{user}`).
3.  **Runtime Match:** When the LLM is called, the Callback Handler checks if the input text matches these regexes.


## Usage

```python
from agent_cover.instrumentation.raw_strings import (
    set_custom_prefixes,
    scan_raw_string_prompts
)

# 1. Configure custom naming conventions
set_custom_prefixes(["BOT_SAY_", "USER_ASK_"])

# 2. Run the scan
scan_raw_string_prompts()

```

## Customizing Raw String Scanning

If you don't use `PromptTemplate` objects but store prompts in global string variables,
you can tell AgentCover how to find them.

By default, we look for variables starting with `PROMPT_` or ending with `_TEMPLATE`.

### Via Python SDK

You can add your own prefixes/suffixes programmatically:

```python
from agent_cover.instrumentation.raw_strings import set_custom_prefixes

set_custom_prefixes(["MY_BOT_MSG_", "AI_INSTRUCTION_"])
# Now variables like MY_BOT_MSG_WELCOME = "..." will be tracked.

```

### Via Pytest CLI

Alternatively, if you are using the pytest plugin, you can configure these without changing code using CLI flags:

* `--prompt-prefixes="MY_BOT_MSG_,AI_INSTRUCTION_"`
* `--prompt-suffixes="_TEXT,_MSG"`

"""

from .scanner import (
    scan_raw_string_prompts,
    set_custom_prefixes,
    set_custom_suffixes,
)

__all__ = [
    "scan_raw_string_prompts",
    "set_custom_prefixes",
    "set_custom_suffixes",
]
